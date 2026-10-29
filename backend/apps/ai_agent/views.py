"""
AI Agent views for REST API.
"""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from config.throttling import ClientIPScopedRateThrottle

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatMessageSendSerializer,
    ChatMessageSerializer,
    ChatHistorySerializer,
)
from .services.agent import AIAgent
from .services.router_ai import RouterAIClient, tts_content_type
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

        # Process through AI agent
        agent = AIAgent(session, lang=lang)
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
        })


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

        voice = request.query_params.get('voice') or settings.ROUTERAI_TTS_VOICE
        cache_key = 'tts:chat:{}:{}:{}'.format(
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
