"""
AI Agent admin configuration.
"""
from django.contrib import admin
from .models import ChatSession, ChatMessage, DocumentEmbedding


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'ip_hash', 'created_at', 'last_active_at']
    readonly_fields = ['session_id', 'ip_hash', 'created_at', 'last_active_at']


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['role', 'content', 'audio_url', 'tokens_used', 'created_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content', 'tokens_used', 'created_at']
    list_filter = ['role', 'created_at']
    readonly_fields = ['session', 'role', 'content', 'audio_url', 'tokens_used', 'created_at']


@admin.register(DocumentEmbedding)
class DocumentEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_id', 'chunk_index', 'created_at']
    list_filter = ['source_type', 'created_at']
    readonly_fields = ['source_type', 'source_id', 'chunk_index', 'chunk_text', 'metadata', 'created_at', 'updated_at']
