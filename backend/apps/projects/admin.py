"""
Projects admin configuration.
"""
from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title_ru', 'slug', 'is_featured', 'visibility', 'sync_from_source', 'views_count', 'likes_count']
    list_filter = ['is_featured', 'visibility', 'created_at', 'sync_from_source']
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
            'fields': ('order', 'is_featured', 'sync_from_source'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            original = self.model.objects.filter(
                pk=obj.pk
            ).values_list('sync_from_source', flat=True).first()
            submitted = form.cleaned_data.get('sync_from_source')
            # Явное включение в этой же форме (False -> True) — уважаем.
            # Любое другое сохранение — ручная правка, синк отключаем,
            # чтобы seed_portfolio не затёр правку пользователя.
            obj.sync_from_source = (original is False and submitted is True)
        super().save_model(request, obj, form, change)