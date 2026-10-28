"""
Projects models for Festchuk portfolio.
"""
from django.db import models
from django.utils.text import slugify


class Project(models.Model):
    """Portfolio project model."""

    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        UNLISTED = 'unlisted', 'Unlisted'
        DRAFT = 'draft', 'Draft'

    title_ru = models.CharField('Название (RU)', max_length=255)
    title_en = models.CharField('Название (EN)', max_length=255, blank=True)
    slug = models.SlugField('Slug', unique=True, allow_unicode=True)
    description_ru = models.TextField('Описание (RU)', blank=True)
    description_en = models.TextField('Описание (EN)', blank=True)
    summary_ru = models.CharField('Краткое описание (RU)', max_length=500, blank=True)
    summary_en = models.CharField('Краткое описание (EN)', max_length=500, blank=True)

    github_url = models.URLField('GitHub URL', blank=True)
    demo_url = models.URLField('Демо URL', blank=True)

    technologies = models.JSONField(
        'Технологии',
        default=list,
        blank=True,
        help_text='Список технологий, например: ["Django", "React", "PostgreSQL"]'
    )

    readme_ru = models.TextField('README (RU, Markdown)', blank=True)
    readme_en = models.TextField('README (EN, Markdown)', blank=True)
    image_preview = models.ImageField(
        'Превью',
        upload_to='projects/previews/',
        blank=True,
        null=True,
    )
    cover_image = models.ImageField(
        'Обложка',
        upload_to='projects/covers/',
        blank=True,
        null=True,
    )

    views_count = models.PositiveIntegerField('Просмотры', default=0)
    likes_count = models.PositiveIntegerField('Лайки', default=0)

    visibility = models.CharField(
        'Видимость',
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    order = models.PositiveIntegerField('Порядок', default=0)
    is_featured = models.BooleanField('Избранное', default=False)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title_ru

    def get_field(self, name: str, lang: str = 'ru') -> str:
        """Return a localized text field with fallback to Russian."""
        value = getattr(self, f'{name}_{lang}', '')
        return value or getattr(self, f'{name}_ru', '')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_ru)
        super().save(*args, **kwargs)
