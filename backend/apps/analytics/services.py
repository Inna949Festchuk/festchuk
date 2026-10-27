"""
Analytics services — anonymous likes and views tracking via Redis.
"""
import hashlib
import ipaddress
import logging

from django.db.models import F
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str:
    """Extract client IP from request, respecting proxy headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _hash_ip(ip: str) -> str:
    """Hash IP address to protect privacy."""
    salt = settings.SECRET_KEY
    return hashlib.sha256(f"{ip}:{salt}".encode()).hexdigest()[:32]


class AnalyticsService:
    """Service for tracking anonymous likes and views."""

    @staticmethod
    def record_like(request, obj) -> tuple[bool, bool]:
        """
        Record a like for an object (Project or Post).

        Returns:
            (success: bool, already_liked: bool)
        """
        ip_hash = _hash_ip(_get_client_ip(request))
        obj_type = type(obj).__name__.lower()
        key = f"like:{obj_type}:{obj.pk}:{ip_hash}"
        ttl = settings.LIKES_TTL

        try:
            # Check if already liked
            already_liked = cache.get(key) is not None
            if already_liked:
                return False, True

            # Set key with TTL
            cache.set(key, 1, ttl)

            # Increment counter atomically
            obj.__class__.objects.filter(pk=obj.pk).update(
                likes_count=F('likes_count') + 1
            )

            return True, False

        except Exception as e:
            logger.error(f"Error recording like for {obj_type}:{obj.pk}: {e}")
            return False, False

    @staticmethod
    def record_view(request, obj) -> bool:
        """
        Record a view for an object (Project or Post).

        Returns:
            (success: bool)
        """
        ip_hash = _hash_ip(_get_client_ip(request))
        obj_type = type(obj).__name__.lower()
        key = f"view:{obj_type}:{obj.pk}:{ip_hash}"
        ttl = settings.VIEWS_TTL

        try:
            # Check if already viewed in TTL window
            if cache.get(key) is not None:
                return True

            # Set key with TTL
            cache.set(key, 1, ttl)

            # Increment counter atomically
            obj.__class__.objects.filter(pk=obj.pk).update(
                views_count=F('views_count') + 1
            )

            return True

        except Exception as e:
            logger.error(f"Error recording view for {obj_type}:{obj.pk}: {e}")
            return False

    @staticmethod
    def has_liked(request, obj) -> bool:
        """Check if current IP has already liked this object."""
        ip_hash = _hash_ip(_get_client_ip(request))
        obj_type = type(obj).__name__.lower()
        key = f"like:{obj_type}:{obj.pk}:{ip_hash}"
        return cache.get(key) is not None
