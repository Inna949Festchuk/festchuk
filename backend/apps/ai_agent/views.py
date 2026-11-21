"""
AI Agent views for REST API.
"""
import hashlib
import json
import logging
import uuid

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework.permissions import AllowAny

from config.throttling import ClientIPScopedRateThrottle

from .models import AgentModule
from .serializers import (
    ChatMessageSendSerializer,
    AgentModuleSerializer,
)
from .services.agent import AIAgent
from .services.pii import mask_pii
from .services.router_ai import RouterAIClient, tts_content_type
from .services.routing import resolve_module_slug
from .services.session import resolve_session, verify_session, delete_session
from apps.analytics.services import _get_client_ip, _hash_ip

logger = logging.getLogger(__name__)

TTS_CACHE_TTL = 3600  # repeated greetings/questions should not re-bill the API


def _pii_counters(types: list):
    """Анонимные счётчики срабатываний PII-маскера (без ПДн — только тип).

    Замена просмотра диалогов в Django Admin после перевода истории в Redis:
    читаются через redis-cli (GET stats:pii_masked:*).
    """
    for t in set(types):
        key = f'stats:pii_masked:{t.upper()}'
        try:
            cache.incr(key)
        except ValueError:
            # cache.incr требует существующего ключа — создаём первый раз
            cache.set(key, 1)


class ChatSessionView(APIView):
    """Create, get or delete a chat session (Redis-only storage)."""
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPScopedRateThrottle]

    def get_throttle_scope(self, obj=None):
        # DELETE («право на удаление») — в chat-бакет. POST/GET не троттлятся:
        # их вызывает каждое открытие чата (в dev StrictMode монтирует
        # эффект дважды), и лимит бы резал обычный сценарий.
        return 'chat' if self.request.method == 'DELETE' else None

    def post(self, request):
        """Create a new chat session."""
        session, created = resolve_session(_hash_ip(_get_client_ip(request)))
        session.touch()

        return Response({
            'session_id': session.session_id,
            'created': created,
            # UI подставляет срок в уведомлении о хранении — число берём
            # из конфига, чтобы заявление не дрифтнуло от фактического TTL.
            'retention_hours': settings.CHAT_RETENTION_HOURS,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def get(self, request):
        """Get or create a session for the current IP."""
        session, _ = resolve_session(_hash_ip(_get_client_ip(request)))
        session.touch()
        return Response({
            'session_id': session.session_id,
            'retention_hours': settings.CHAT_RETENTION_HOURS,
        })

    def delete(self, request):
        """«Право на удаление» (152-ФЗ): сессия и история диалога.

        Идентификация строго по IP запроса (тот же путь, что при создании):
        клиент не передаёт идентификаторы, чужие сессии удалить нельзя.
        Throttle 'chat' (30/час) защищает от злоупотребления.
        """
        deleted = delete_session(_hash_ip(_get_client_ip(request)))
        return Response({'deleted': deleted})


class ChatMessageView(APIView):
    """Send a message to the AI agent."""
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPScopedRateThrottle]
    throttle_scope = 'chat'

    def post(self, request):
        serializer = ChatMessageSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data['session_id']
        user_message = serializer.validated_data['message']
        lang = serializer.validated_data.get('lang', 'ru')
        module_slug = serializer.validated_data.get('module_slug', '')

        # Сессия привязана к IP: чужой/протухший session_id → 404
        session = verify_session(_hash_ip(_get_client_ip(request)), session_id)
        if session is None:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # PII-маскировка (152-ФЗ): до сохранения в Redis и до отправки в
        # LLM/эмбеддинги провайдера — персональные данные не покидают периметр
        user_message, pii_types = mask_pii(user_message)
        _pii_counters(pii_types)

        # The UI pins module_slug to the module the chat was opened from.
        # The deterministic routing layer may override it (a named module,
        # stack keywords, or "пока"/"assistant" back to the coordinator).
        effective_slug = resolve_module_slug(user_message, module_slug)
        agent = AIAgent(session, lang=lang, module_slug=effective_slug)
        try:
            response_text, tokens_used = agent.process_message(user_message)
        except Exception as e:
            logger.error(f"AI agent error: {e}")
            return Response(
                {'error': 'AI service temporarily unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        session.touch()

        return Response({
            # История живёт в Redis: id генерируется, а не берётся из БД
            'message': {
                'id': str(uuid.uuid4()),
                'role': 'assistant',
                'content': response_text,
                'audio_url': None,
                'created_at': timezone.now().isoformat(),
            },
            'tokens_used': tokens_used,
            # Final slug: the agent may have switched persona mid-reply via
            # the activate_module tool — the frontend syncs its TTS voice
            # from this value.
            'module_slug': agent.module_slug or '',
        })


class ChatMessageStreamView(APIView):
    """Send a message and stream the answer as Server-Sent Events.

    Same request contract as ChatMessageView; the reply arrives incrementally:
    meta (active module slug, may repeat after activate_module) → delta*
    (text fragments) → done (authoritative text, slug, tokens, message_id).
    error event on failure. The JSON endpoint stays for compatibility.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPScopedRateThrottle]
    throttle_scope = 'chat'

    def perform_content_negotiation(self, request, force=False):
        # The SSE response bypasses DRF rendering; Accept: text/event-stream
        # must not 406 against the JSON-only renderer list. Error responses
        # (400/404) still render as JSON.
        return JSONRenderer(), 'application/json'

    def post(self, request):
        serializer = ChatMessageSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data['session_id']
        user_message = serializer.validated_data['message']
        lang = serializer.validated_data.get('lang', 'ru')
        module_slug = serializer.validated_data.get('module_slug', '')

        # Сессия привязана к IP: чужой/протухший session_id → 404
        session = verify_session(_hash_ip(_get_client_ip(request)), session_id)
        if session is None:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # PII-маскировка (152-ФЗ): до сохранения в Redis и до отправки в
        # LLM/эмбеддинги провайдера — персональные данные не покидают периметр
        user_message, pii_types = mask_pii(user_message)
        _pii_counters(pii_types)

        effective_slug = resolve_module_slug(user_message, module_slug)
        agent = AIAgent(session, lang=lang, module_slug=effective_slug)

        def event_stream():
            # Персистентность истории — в finally самого генератора агента
            # (потоковый _save_history в Redis); при обрыве клиента
            # GeneratorExit пробрасывается и туда. Здесь остаётся только
            # продление TTL сессии и авторитетный message_id.
            for event, data in agent.process_message_stream(user_message):
                if event == 'done':
                    session.touch()
                    data['message_id'] = str(uuid.uuid4())
                yield f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'

        response = StreamingHttpResponse(
            event_stream(), content_type='text/event-stream; charset=utf-8'
        )
        # no-transform skips the Next.js compression middleware (it would
        # buffer the stream); X-Accel-Buffering disables nginx buffering.
        response['Cache-Control'] = 'no-cache, no-transform'
        response['X-Accel-Buffering'] = 'no'
        return response


class ChatTTSView(APIView):
    """Text-to-speech for assistant replies."""
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPScopedRateThrottle]
    throttle_scope = 'tts'

    def get(self, request):
        text = (request.query_params.get('text') or '').strip()[:500]
        if not text:
            return Response(
                {'error': 'text required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        voice = request.query_params.get('voice')
        if not voice:
            # Per-module voice: each agent module has its own TTS voice
            # (AgentModule.tts_voice), the global default covers the plain
            # NEURAL ASSIST chat.
            module_slug = (request.query_params.get('module_slug') or '').strip()
            if module_slug:
                module = AgentModule.objects.filter(
                    slug=module_slug, is_active=True
                ).first()
                voice = getattr(module, 'tts_voice', '') or None
        voice = voice or settings.ROUTERAI_TTS_VOICE
        # Голосовая локаль: UI шлёт lang=ru|en, язык речи фиксируется им —
        # смешанные RU/EN ответы иначе читаются с английским акцентом
        # (пробный замер 2026-11-20: RouterAI принимает параметр).
        lang = (request.query_params.get('lang') or '').strip() or None
        cache_key = 'tts:chat:{}:{}:{}:{}:{}'.format(
            settings.ROUTERAI_TTS_MODEL,
            settings.ROUTERAI_TTS_FORMAT,
            voice,
            lang or '',
            hashlib.sha256(text.encode()).hexdigest()[:16],
        )
        audio = cache.get(cache_key)

        if audio is None:
            try:
                audio = RouterAIClient().tts(text, voice=voice, language=lang)
            except Exception as e:
                logger.error(f"Chat TTS error: {e}")
                return Response(
                    {'error': 'Speech synthesis failed'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            cache.set(cache_key, audio, TTS_CACHE_TTL)

        return HttpResponse(audio, content_type=tts_content_type())


class ChatSTTView(APIView):
    """Speech-to-Text endpoint."""
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPScopedRateThrottle]
    throttle_scope = 'stt'

    def post(self, request):
        # Get session_id from query params or form data
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Сессия должна принадлежать этому IP (история в Redis, привязка по
        # IP-hash): чужой/протухший ID → 404, как у чата.
        session = verify_session(_hash_ip(_get_client_ip(request)), session_id)
        if session is None:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        audio_file = request.FILES.get('audio')
        if not audio_file:
            return Response(
                {'error': 'audio file required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Pin the recognition language to the UI locale (sent by the
            # frontend as ?lang=ru|en): whisper auto-detect mis-hears short
            # Russian phrases as English.
            lang = request.query_params.get('lang', 'ru')
            client = RouterAIClient()
            text = client.stt(audio_file, language=lang)
            return Response({'text': text})
        except Exception as e:
            logger.error(f"STT error: {e}")
            return Response(
                {'error': 'Speech recognition failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgentModuleListView(APIView):
    """List all active agent modules."""
    permission_classes = [AllowAny]

    def get(self, request):
        lang = request.query_params.get('lang', 'ru')
        modules = AgentModule.objects.filter(is_active=True)
        serializer = AgentModuleSerializer(modules, many=True, context={'lang': lang})
        return Response(serializer.data)


class AgentModuleDetailView(APIView):
    """Get a single active agent module by slug."""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        lang = request.query_params.get('lang', 'ru')
        try:
            module = AgentModule.objects.get(slug=slug, is_active=True)
        except AgentModule.DoesNotExist:
            return Response(
                {'error': 'Module not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AgentModuleSerializer(module, context={'lang': lang})
        return Response(serializer.data)
