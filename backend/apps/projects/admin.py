"""
Projects admin configuration.
"""
from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title_ru', 'slug', 'is_featured', 'visibility', 'views_count', 'likes_count', 'created_at']
    list_filter = ['is_featured', 'visibility', 'created_at']
    search_fields = ['title_ru', 'title_en', 'description_ru', 'description_en', 'technologies']
    prepopulated_fields = {'slug': ('title_ru',)}
    filter_horizontal = []
    fieldsets = (
        ('Основное (RU)', {
            'fields': ('title_ru', 'slug', 'summary_ru', 'description_ru', 'visibility'),
        }),
        ('Основное (EN)', {
            'fields': ('title_en', 'summary_en', 'description_en'),
            'classes': ('collapse',),
            'description': 'Если поле пустое — для английского языка используется русский.',
        }),
        ('Ссылки', {
            'fields': ('github_url', 'demo_url'),
        }),
        ('Технологии', {
            'fields': ('technologies',),
        }),
        ('Контент (RU)', {
            'fields': ('readme_ru', 'image_preview', 'cover_image'),
        }),
        ('Контент (EN)', {
            'fields': ('readme_en',),
            'classes': ('collapse',),
            'description': 'Англоязычная версия README (Markdown).',
        }),
        ('Статистика', {
            'fields': ('views_count', 'likes_count'),
        }),
        ('Настройки', {
            'fields': ('order', 'is_featured'),
        }),
    )