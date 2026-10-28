"""
AI Agent serializers for REST API.
"""
import uuid

from rest_framework import serializers

from .models import ChatSession, ChatMessage


class ChatSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new chat session."""
    pass  # No fields needed — session is auto-created


class ChatMessageSendSerializer(serializers.Serializer):
    """Serializer for sending a message to the AI agent."""
    session_id = serializers.UUIDField()
    message = serializers.CharField(max_length=4000)
    lang = serializers.ChoiceField(choices=('ru', 'en'), required=False, default='ru')


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'audio_url', 'created_at']
        read_only_fields = fields


class ChatHistorySerializer(serializers.Serializer):
    """Serializer for chat history response."""
    session_id = serializers.UUIDField()
    messages = ChatMessageSerializer(many=True)


class STTRequestSerializer(serializers.Serializer):
    """Serializer for Speech-to-Text request."""
    session_id = serializers.UUIDField()
    # audio file is passed as multipart form data
