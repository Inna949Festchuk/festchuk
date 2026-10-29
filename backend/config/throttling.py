"""
Rate limiting keyed on the real client IP.

DRF's stock throttles use ``REMOTE_ADDR``. Every browser request reaches
Django through a reverse proxy — the Next.js rewrite in dev, nginx in prod —
so ``REMOTE_ADDR`` is the *proxy's* address and a single throttle bucket ends
up shared by the whole site. With the default ``100/hour`` that meant ~50 page
views per hour for all visitors combined, after which every endpoint (lists,
chat session, STT) started answering 429 and the UI silently went empty.

These throttles resolve the client through ``_get_client_ip``, which honours
``X-Forwarded-For`` only when the direct peer is a trusted proxy.
"""
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle

from apps.analytics.services import _get_client_ip


class ClientIPAnonRateThrottle(AnonRateThrottle):
    """``anon`` rate, counted per real client IP instead of per proxy."""

    def get_ident(self, request):
        return _get_client_ip(request)


class ClientIPScopedRateThrottle(ScopedRateThrottle):
    """Per-scope rate (``chat``, ``tts``, ``stt``, ``write``) per real client IP."""

    def get_ident(self, request):
        return _get_client_ip(request)
