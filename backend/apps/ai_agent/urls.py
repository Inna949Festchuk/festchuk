"""
AI Agent app URL configuration.
"""
from django.urls import path
from .views import (
    ChatSessionView,
    ChatMessageView,
    ChatMessageStreamView,
    ChatTTSView,
    ChatSTTView,
    AgentModuleListView,
    AgentModuleDetailView,
)

urlpatterns = [
    # DELETE /api/chat/session/ — «право на удаление» (152-ФЗ):
    # сессия и история диалога удаляются со стороны сервера по IP
    path('chat/session/', ChatSessionView.as_view(), name='chat-session'),
    path('chat/message/', ChatMessageView.as_view(), name='chat-message'),
    path('chat/message/stream/', ChatMessageStreamView.as_view(), name='chat-message-stream'),
    path('chat/tts/', ChatTTSView.as_view(), name='chat-tts'),
    path('chat/voice/stt/', ChatSTTView.as_view(), name='chat-stt'),
    path('modules/', AgentModuleListView.as_view(), name='agent-modules'),
    path('modules/<slug:slug>/', AgentModuleDetailView.as_view(), name='agent-module-detail'),
]
