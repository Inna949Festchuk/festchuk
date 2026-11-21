"""
AI Agent admin configuration.
"""
from django.contrib import admin
from .models import AgentModule, DocumentEmbedding


@admin.register(AgentModule)
class AgentModuleAdmin(admin.ModelAdmin):
    list_display = ['slug', 'code_name', 'name_ru', 'is_active']
    list_filter = ['is_active']
    search_fields = ['slug', 'code_name', 'name_ru']
    fieldsets = (
        (None, {
            'fields': ('slug', 'code_name', 'name_ru', 'name_en', 'description_ru', 'description_en', 'is_active'),
        }),
        ('Видео и контент', {
            'fields': ('video_url', 'video_file', 'skills_text_ru', 'skills_text_en'),
        }),
        ('Тексты терминала', {
            'fields': ('init_text_ru', 'init_text_en', 'shutdown_text_ru', 'shutdown_text_en'),
        }),
        ('Чат / SKILL', {
            'fields': ('tts_voice', 'routing_keywords', 'greeting_ru', 'greeting_en', 'system_prompt_ru', 'system_prompt_en'),
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DocumentEmbedding)
class DocumentEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_id', 'chunk_index', 'created_at']
    list_filter = ['source_type', 'created_at']
    readonly_fields = ['source_type', 'source_id', 'chunk_index', 'chunk_text', 'metadata', 'created_at', 'updated_at']
