"""
Blog admin configuration.
"""
from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title_ru', 'slug', 'status', 'published_at', 'views_count', 'likes_count', 'reading_time_minutes']
    list_filter = ['status', 'published_at', 'created_at']
    search_fields = ['title_ru', 'title_en', 'excerpt_ru', 'excerpt_en', 'content_ru', 'tags']
    prepopulated_fields = {'slug': ('title_ru',)}
    filter_horizontal = []
    date_hierarchy = 'published_at'
    fieldsets = (
        ('Основное (RU)', {
            'fields': ('title_ru', 'slug', 'excerpt_ru', 'content_ru'),
        }),
        ('Основное (EN)', {
            'fields': ('title_en', 'excerpt_en', 'content_en'),
            'classes': ('collapse',),
            'description': 'Если поле пустое — для английского языка используется русский.',
        }),
        ('Медиа', {
            'fields': ('cover_image',),
        }),
        ('Тегирование', {
            'fields': ('tags',),
        }),
        ('Публикация', {
            'fields': ('status', 'published_at'),
        }),
        ('Статистика', {
            'fields': ('views_count', 'likes_count'),
        }),
        ('TTS', {
            'fields': ('tts_audio_url', 'tts_generated_at'),
        }),
    )