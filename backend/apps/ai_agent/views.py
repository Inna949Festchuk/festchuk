"""
AI Agent views for REST API.
"""
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatMessageSendSerializer,
    ChatMessageSerializer,
    ChatHistorySerializer,
)
from .services.agent import AIAgent
from .services.router_ai import RouterAIClient
from apps.analytics.services import _get_client_ip, _hash_ip

logger = logging.getLogger(__name__)


class ChatSessionView(APIView):
    """Create or get a chat session."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Create a new chat session."""
        ip_hash = _hash_ip(_get_client_ip(request))
        session, created = ChatSession.objects.get_or_create(
            ip_hash=ip_hash,
            defaults={'last_active_at': timezone.now()},
        )
        if not created:
            session.touch()

        return Response({
            'session_id': str(session.session_id),
            'created': created,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def get(self, request):
        """Get or create a session for the current IP."""
        ip_hash = _hash_ip(_get_client_ip(request))
        session, created = ChatSession.objects.get_or_create(
            ip_hash=ip_hash,
        )
        session.touch()
        return Response({'session_id': str(session.session_id)})


class ChatMessageView(APIView):
    """Send a message to the AI agent."""
    permission_classes = [AllowAny]

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

    def post(self, request, session_id=None):
        # Get session_id from query params or path
        session_id = session_id or request.query_params.get('session_id')
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


# Fix import
from django.utils import timezone
