"""
AI Agent views for REST API.
"""
import hashlib
import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework.permissions import AllowAny

from config.throttling import ClientIPScopedRateThrottle

from .models import ChatSession, ChatMessage, AgentModule
from .serializers import (
    ChatMessageSendSerializer,
    ChatMessageSerializer,
    ChatHistorySerializer,
    AgentModuleSerializer,
)
from .services.agent import AIAgent
from .services.router_ai import RouterAIClient, tts_content_type
from .services.routing import resolve_module_slug
from apps.analytics.services import _get_client_ip, _hash_ip

logger = logging.getLogger(__name__)

TTS_CACHE_TTL = 3600  # repeated greetings/questions should not re-bill the API


def _resolve_session(ip_hash: str) -> tuple[ChatSession, bool]:
    """Return ``(session, created)`` for a visitor, creating it exactly once.

    `get_or_create` is only race-free when the lookup key is unique at the
    database level. React 18 StrictMode mounts effects twice in dev, so two
    concurrent requests used to insert two rows for one IP and every later
    lookup then died with MultipleObjectsReturned. The unique constraint from
    migration 0003 makes the create-or-refetch below safe.
    """
    existing = ChatSession.objects.filter(ip_hash=ip_hash).first()
    if existing is not None:
        return existing, False

    try:
        return ChatSession.objects.create(ip_hash=ip_hash), True
    except IntegrityError:
        # Lost the race with a concurrent request; theirs is committed.
        return ChatSession.objects.get(ip_hash=ip_hash), False


class ChatSessionView(APIView):
    """Create or get a chat session."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Create a new chat session."""
        session, created = _resolve_session(_hash_ip(_get_client_ip(request)))
        session.touch()

        return Response({
            'session_id': str(session.session_id),
            'created': created,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def get(self, request):
        """Get or create a session for the current IP."""
        session, _ = _resolve_session(_hash_ip(_get_client_ip(request)))
        session.touch()
        return Response({'session_id': str(session.session_id)})


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

        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=user_message,
        )

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

        # Save assistant message
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=response_text,
            tokens_used=tokens_used,
        )
        session.touch()

        return Response({
            'message': ChatMessageSerializer(assistant_msg).data,
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

        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=user_message,
        )

        effective_slug = resolve_module_slug(user_message, module_slug)
        agent = AIAgent(session, lang=lang, module_slug=effective_slug)

        def event_stream():
            accumulated = ''
            persisted = False
            try:
                for event, data in agent.process_message_stream(user_message):
                    if event == 'delta':
                        accumulated += data.get('text', '')
                    elif event == 'done':
                        text = data.get('text') or accumulated
                        assistant_msg = ChatMessage.objects.create(
                            session=session,
                            role=ChatMessage.Role.ASSISTANT,
                            content=text,
                            tokens_used=data.get('tokens_used', 0),
                        )
                        session.touch()
                        data['message_id'] = str(assistant_msg.pk)
                        persisted = True
                    elif event == 'error' and accumulated:
                        # Keep whatever the visitor already saw on screen
                        ChatMessage.objects.create(
                            session=session,
                            role=ChatMessage.Role.ASSISTANT,
                            content=accumulated,
                            tokens_used=0,
                        )
                        session.touch()
                        persisted = True
                    yield f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'
            finally:
                # Client disconnect mid-stream: persist the partial answer so
                # DB history matches what the visitor saw.
                if not persisted and accumulated:
                    ChatMessage.objects.create(
                        session=session,
                        role=ChatMessage.Role.ASSISTANT,
                        content=accumulated,
                        tokens_used=0,
                    )
                    session.touch()

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
        cache_key = 'tts:chat:{}:{}:{}:{}'.format(
            settings.ROUTERAI_TTS_MODEL,
            settings.ROUTERAI_TTS_FORMAT,
            voice,
            hashlib.sha256(text.encode()).hexdigest()[:16],
        )
        audio = cache.get(cache_key)

        if audio is None:
            try:
                audio = RouterAIClient().tts(text, voice=voice)
            except Exception as e:
                logger.error(f"Chat TTS error: {e}")
                return Response(
                    {'error': 'Speech synthesis failed'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            cache.set(cache_key, audio, TTS_CACHE_TTL)

        return HttpResponse(audio, content_type=tts_content_type())


class ChatHistoryView(APIView):
    """Get chat history for a session."""
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get last N messages
        limit = min(int(request.query_params.get('limit', 50)), 100)
        messages = session.messages.all()[:limit]

        return Response(ChatHistorySerializer({
            'session_id': session.session_id,
            'messages': list(messages),
        }).data)


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

        audio_file = request.FILES.get('audio')
        if not audio_file:
            return Response(
                {'error': 'audio file required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = RouterAIClient()
            text = client.stt(audio_file)
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
