"""
AI Agent admin configuration.
"""
from django import forms
from django.contrib import admin, messages
from .models import AgentModule, DocumentEmbedding, LegalDocument
from .tasks import embed_legal_document


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


class LegalDocumentForm(forms.ModelForm):
    """Крупный моноширинный textarea: документ на сотни КБ — дефолтный
    виджет Django Admin его рендерит невыносимо узким."""

    class Meta:
        model = LegalDocument
        fields = '__all__'
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 30,
                'style': 'width: 100%; font-family: monospace; font-size: 12px; line-height: 1.4;',
            }),
        }


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    form = LegalDocumentForm
    list_display = ['code', 'title', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['code', 'title']
    actions = ['index_in_rag']

    @admin.action(description='Проиндексировать в RAG (фоновая Celery-задача)')
    def index_in_rag(self, request, queryset):
        """Явное пересоздание эмбеддингов: по сохранению текста индекс не
        обновляется автоматически (см. embed_legal_document в tasks.py)."""
        for doc in queryset:
            embed_legal_document.delay(doc.pk)
        self.message_user(
            request,
            f'Поставлена в очередь {queryset.count()} документ(ов): RAG-индекс '
            'пересоздаётся фоновой задачей (несколько минут). Неактивные '
            'документы — их чанки будут удалены из RAG.',
            messages.INFO,
        )
