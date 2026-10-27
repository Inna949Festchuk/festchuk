"""
Blog models for Festchuk portfolio.
"""
from django.db import models
from django.utils.text import slugify


class Post(models.Model):
    """Blog post model."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField('Заголовок', max_length=255)
    slug = models.SlugField('Slug', unique=True, allow_unicode=True)
    excerpt = models.CharField('Анонс', max_length=500, blank=True)
    content = models.TextField('Контент (Markdown)')

    cover_image = models.ImageField(
        'Обложка',
        upload_to='blog/covers/',
        blank=True,
        null=True,
    )

    tags = models.JSONField(
        'Теги',
        default=list,
        blank=True,
        help_text='Список тегов, например: ["django", "ai", "docker"]'
    )

    status = models.CharField(
        'Статус',
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_at = models.DateTimeField('Дата публикации', blank=True, null=True)

    views_count = models.PositiveIntegerField('Просмотры', default=0)
    likes_count = models.PositiveIntegerField('Лайки', default=0)

    # TTS cache
    tts_audio_url = models.URLField('Аудио (TTS)', blank=True)
    tts_generated_at = models.DateTimeField('Аудио сгенерировано', blank=True, null=True)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Auto-set published_at if status changed to published
        if self.status == self.Status.PUBLISHED and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def reading_time_minutes(self):
        """Estimate reading time in minutes."""
        words = len(self.content.split())
        return max(1, words // 200)  # ~200 words per minute
