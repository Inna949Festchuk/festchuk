"""
Blog admin configuration.
"""
from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'status', 'published_at', 'views_count', 'likes_count', 'reading_time_minutes']
    list_filter = ['status', 'published_at', 'created_at']
    search_fields = ['title', 'excerpt', 'content', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = []
    date_hierarchy = 'published_at'
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'excerpt', 'content'),
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
