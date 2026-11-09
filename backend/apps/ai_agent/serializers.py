"""
AI Agent serializers for REST API.
"""
import uuid

from django.conf import settings
from rest_framework import serializers

from .models import AgentModule, ChatSession, ChatMessage


class AgentModuleSerializer(serializers.ModelSerializer):
    """Serializer for agent module data (public, localized)."""
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    skills_text = serializers.SerializerMethodField()
    greeting = serializers.SerializerMethodField()
    init_text = serializers.SerializerMethodField()
    shutdown_text = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = AgentModule
        fields = [
            'id', 'slug', 'code_name', 'name', 'description',
            'video_url', 'skills_text', 'greeting', 'init_text', 'shutdown_text',
            'is_active',
        ]
        read_only_fields = fields

    def _lang(self) -> str:
        return self.context.get('lang', 'ru')

    def get_video_url(self, obj: AgentModule) -> str:
        """Uploaded video file wins over the external URL.

        Built as an absolute URL from ``API_BASE_URL`` — the backend only sees
        internal proxy hosts (Host: backend:8000), which browsers cannot resolve.
        """
        if obj.video_file:
            path = f"{settings.MEDIA_URL}{obj.video_file.name}"
            base = getattr(settings, 'API_BASE_URL', '')
            if base:
                return base.rstrip('/') + path
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(path)
            return path
        return obj.video_url

    def get_name(self, obj: AgentModule) -> str:
        return obj.get_field('name', self._lang())

    def get_description(self, obj: AgentModule) -> str:
        return obj.get_field('description', self._lang())

    def get_skills_text(self, obj: AgentModule) -> str:
        return obj.get_field('skills_text', self._lang())

    def get_greeting(self, obj: AgentModule) -> str:
        return obj.get_field('greeting', self._lang())

    def get_init_text(self, obj: AgentModule) -> str:
        return obj.get_field('init_text', self._lang())

    def get_shutdown_text(self, obj: AgentModule) -> str:
        return obj.get_field('shutdown_text', self._lang())


class ChatSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new chat session."""
    pass  # No fields needed — session is auto-created


class ChatMessageSendSerializer(serializers.Serializer):
    """Serializer for sending a message to the AI agent."""
    session_id = serializers.UUIDField()
    message = serializers.CharField(max_length=4000)
    lang = serializers.ChoiceField(choices=('ru', 'en'), required=False, default='ru')
    module_slug = serializers.CharField(max_length=50, required=False, allow_blank=True)


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
