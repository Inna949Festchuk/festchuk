"""
AI Agent app URL configuration.
"""
from django.urls import path
from .views import (
    ChatSessionView,
    ChatMessageView,
    ChatTTSView,
    ChatHistoryView,
    ChatSTTView,
)

urlpatterns = [
    path('chat/session/', ChatSessionView.as_view(), name='chat-session'),
    path('chat/message/', ChatMessageView.as_view(), name='chat-message'),
    path('chat/tts/', ChatTTSView.as_view(), name='chat-tts'),
    path('chat/history/<uuid:session_id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('chat/voice/stt/', ChatSTTView.as_view(), name='chat-stt'),
]
