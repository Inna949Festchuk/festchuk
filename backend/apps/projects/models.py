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

    title = models.CharField('Название', max_length=255)
    slug = models.SlugField('Slug', unique=True, allow_unicode=True)
    description = models.TextField('Описание', blank=True)
    summary = models.CharField('Краткое описание', max_length=500, blank=True)

    github_url = models.URLField('GitHub URL', blank=True)
    demo_url = models.URLField('Демо URL', blank=True)

    technologies = models.JSONField(
        'Технологии',
        default=list,
        blank=True,
        help_text='Список технологий, например: ["Django", "React", "PostgreSQL"]'
    )

    readme_content = models.TextField('README (Markdown)', blank=True)
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
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
