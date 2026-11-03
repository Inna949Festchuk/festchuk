"""
Blog admin configuration.
"""
from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title_ru', 'slug', 'status', 'published_at', 'sync_from_source', 'views_count', 'likes_count']
    list_filter = ['status', 'published_at', 'created_at', 'sync_from_source']
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
            'fields': ('status', 'published_at', 'sync_from_source'),
        }),
        ('Статистика', {
            'fields': ('views_count', 'likes_count'),
        }),
        ('TTS', {
            'fields': ('tts_audio_url', 'tts_generated_at'),
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