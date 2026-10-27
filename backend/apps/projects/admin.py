"""
Projects admin configuration.
"""
from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_featured', 'visibility', 'views_count', 'likes_count', 'created_at']
    list_filter = ['is_featured', 'visibility', 'created_at']
    search_fields = ['title', 'description', 'technologies']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = []
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'summary', 'description', 'visibility'),
        }),
        ('Ссылки', {
            'fields': ('github_url', 'demo_url'),
        }),
        ('Технологии', {
            'fields': ('technologies',),
        }),
        ('Контент', {
            'fields': ('readme_content', 'image_preview', 'cover_image'),
        }),
        ('Статистика', {
            'fields': ('views_count', 'likes_count'),
        }),
        ('Настройки', {
            'fields': ('order', 'is_featured'),
        }),
    )
