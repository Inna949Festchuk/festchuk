"""
Blog views for REST API.
"""
import hashlib
import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.analytics.services import AnalyticsService
from apps.ai_agent.services.router_ai import RouterAIClient, tts_content_type
from config.throttling import ClientIPScopedRateThrottle

from .models import Post
from .serializers import (
    PostSerializer,
    PostListSerializer,
    PostCreateSerializer,
    PostUpdateSerializer,
)

logger = logging.getLogger(__name__)

VALID_LANGS = ('ru', 'en')
TTS_CACHE_TTL = 7 * 24 * 3600  # a week; audio is content-derived and stable

# Markdown -> readable plain text for the synthesizer.
_MD_BLOCK_RE = re.compile(r'```.*?```', re.S)
_MD_IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]*\)')
_MD_LINK_RE = re.compile(r'\[([^\]]*)\]\([^)]*\)')
_MD_NOISE_RE = re.compile(r'^\s{0,3}(#{1,6}\s*|>\s?|[-*+]\s+|\d+\.\s+|\|)', re.M)
_MD_WS_RE = re.compile(r'\n{3,}')


def _markdown_to_text(markdown: str) -> str:
    """Flatten Markdown to plain text so the TTS voice does not read syntax."""
    text = _MD_BLOCK_RE.sub(' ', markdown or '')
    text = _MD_IMAGE_RE.sub(' ', text)
    text = _MD_LINK_RE.sub(r'\1', text)
    text = _MD_NOISE_RE.sub('', text)
    text = text.replace('*', '').replace('`', '').replace('_', ' ')
    return _MD_WS_RE.sub('\n\n', text).strip()


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for blog posts."""
    permission_classes = [AllowAny]
    queryset = Post.objects.filter(status=Post.Status.PUBLISHED)
    # The frontend links to /api/posts/<slug>/; the default pk lookup 404'd
    # every article page.
    lookup_field = 'slug'
    pagination_class = None

    @property
    def throttle_scope(self):
        # ScopedRateThrottle re-reads `throttle_scope` off the view on every
        # request, so a property is the only way to vary it per action.
        return 'tts' if self.action == 'tts' else 'write'

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        elif self.action == 'create':
            return PostCreateSerializer
        elif self.action in ('update', 'partial_update'):
            return PostUpdateSerializer
        return PostSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get('lang', 'ru')
        context['lang'] = lang if lang in VALID_LANGS else 'ru'
        return context

    def get_throttles(self):
        if self.action in ('like', 'view', 'tts'):
            return [ClientIPScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        queryset = super().get_queryset()
        tag = self.request.query_params.get('tag')
        if tag:
            wanted = tag.lower()
            # tags is a JSON list with no portable case-insensitive containment
            # lookup, so match in Python — but hand DRF a QuerySet back, since
            # a bare list breaks get_object() and pagination.
            matching = [
                p.pk for p in queryset
                if wanted in [t.lower() for t in p.tags]
            ]
            queryset = queryset.filter(pk__in=matching)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def like(self, request, slug=None):
        """Record a like for a post."""
        post = self.get_object()
        success, already_liked = AnalyticsService.record_like(request, post)
        return Response({
            'success': success,
            'likes_count': post.likes_count if success else post.likes_count + 1,
            'already_liked': already_liked,
        }, status=status.HTTP_200_OK if success else status.HTTP_429_TOO_MANY_REQUESTS)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def view(self, request, slug=None):
        """Record a view for a post."""
        post = self.get_object()
        AnalyticsService.record_view(request, post)
        return Response({'success': True, 'views_count': post.views_count})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def tts(self, request, slug=None):
        """Synthesize the article as audio, cached per (post, language)."""
        post = self.get_object()
        lang = request.query_params.get('lang', 'ru')
        lang = lang if lang in VALID_LANGS else 'ru'

        text = _markdown_to_text(post.get_field('content', lang))[:settings.TTS_MAX_CHARS]
        if not text:
            return Response(
                {'error': 'Nothing to synthesize'},
                status=status.HTTP_404_NOT_FOUND,
            )

        cache_key = 'tts:post:{}:{}:{}:{}'.format(
            settings.ROUTERAI_TTS_FORMAT,
            post.pk,
            lang,
            hashlib.sha256(text.encode()).hexdigest()[:16],
        )
        audio = cache.get(cache_key)

        if audio is None:
            try:
                audio = RouterAIClient().tts(text)
            except Exception as e:
                logger.error(f"Post TTS error ({post.slug}): {e}")
                return Response(
                    {'error': 'Speech synthesis failed'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            cache.set(cache_key, audio, TTS_CACHE_TTL)

        return HttpResponse(audio, content_type=tts_content_type())
