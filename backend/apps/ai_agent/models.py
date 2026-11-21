"""
AI Agent models for Feshchuk portfolio.

Chat sessions and messages intentionally do NOT live here: since 2026-11-21
the dialogue history is stored in Redis only (TTL = retention period), so
visitor personal data never rests in PostgreSQL (152-FZ minimization).
See apps/ai_agent/services/session.py.
"""
from django.db import models
from pgvector.django import VectorField


class AgentModule(models.Model):
    """Core agent module (NEURAL SYNC, QUANTUM SHIELD, OMNI VISION, HYPER DRIVE)."""

    slug = models.SlugField('Slug', max_length=50, unique=True, db_index=True)
    code_name = models.CharField('Кодовое имя', max_length=50)
    name_ru = models.CharField('Название (RU)', max_length=100)
    name_en = models.CharField('Название (EN)', max_length=100, blank=True, default='')
    description_ru = models.TextField('Описание (RU)', blank=True, default='')
    description_en = models.TextField('Описание (EN)', blank=True, default='')
    video_url = models.URLField('URL видео', blank=True, default='')
    video_file = models.FileField(
        'Видео-файл', upload_to='agent_videos/', blank=True, default='',
        help_text='Загрузка видео с хоста. Если задано — имеет приоритет над URL видео.',
    )
    skills_text_ru = models.TextField('Компетенции (RU)', blank=True, default='')
    skills_text_en = models.TextField('Компетенции (EN)', blank=True, default='')
    tts_voice = models.CharField(
        'TTS голос', max_length=50, blank=True, default='',
        help_text='Имя голоса для синтеза речи модуля (пусто — голос по умолчанию из .env)',
    )
    routing_keywords = models.TextField(
        'Ключевые слова стека', blank=True, default='',
        help_text='Термины через запятую: упоминание в сообщении переключает чат на этот модуль (пусто — дефолты из кода)',
    )
    greeting_ru = models.TextField('Приветствие чата (RU)', blank=True, default='')
    greeting_en = models.TextField('Приветствие чата (EN)', blank=True, default='')
    system_prompt_ru = models.TextField(
        'System prompt / SKILL (RU)', blank=True, default='',
        help_text='Линия поведения ИИ-ассистента для этого модуля',
    )
    system_prompt_en = models.TextField(
        'System prompt / SKILL (EN)', blank=True, default='',
    )
    init_text_ru = models.TextField(
        'Текст инициализации терминала (RU)', blank=True, default='',
    )
    init_text_en = models.TextField(
        'Текст инициализации терминала (EN)', blank=True, default='',
    )
    shutdown_text_ru = models.TextField(
        'Текст завершения экрана (RU)', blank=True, default='',
    )
    shutdown_text_en = models.TextField(
        'Текст завершения экрана (EN)', blank=True, default='',
    )
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Модуль агента'
        verbose_name_plural = 'Модули агентов'
        ordering = ['slug']

    def __str__(self):
        return f'{self.code_name} ({self.slug})'

    def get_field(self, field: str, lang: str) -> str:
        """Return localized field value with RU fallback."""
        value = getattr(self, f'{field}_{lang}', '')
        if not value and lang != 'ru':
            value = getattr(self, f'{field}_ru', '')
        return value


class DocumentEmbedding(models.Model):
    """Vector embedding for RAG retrieval."""

    class SourceType(models.TextChoices):
        PROJECT = 'project', 'Проект'
        BLOG_POST = 'blog_post', 'Статья'
        LEGAL = 'legal', 'Нормативный документ'

    source_type = models.CharField(
        'Тип источника',
        max_length=20,
        choices=SourceType.choices,
    )
    source_id = models.PositiveIntegerField('ID источника')
    chunk_index = models.PositiveIntegerField('Индекс чанка', default=0)
    chunk_text = models.TextField('Текст чанка')
    metadata = models.JSONField('Метаданные', default=dict)
    embedding = VectorField('Вектор', dimensions=1024)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Векторное представление'
        verbose_name_plural = 'Векторные представления'
        unique_together = ['source_type', 'source_id', 'chunk_index']
        indexes = [
            models.Index(fields=['source_type', 'source_id']),
        ]

    def __str__(self):
        return f"{self.source_type}:{self.source_id}#{self.chunk_index}"


class LegalDocument(models.Model):
    """Нормативный документ для RAG (152-ФЗ и потенциально другие законы).

    Текст редактируется в Django Admin; RAG-индекс обновляется ЯВНО
    экшеном «Проиндексировать в RAG» (Celery-задача) — автоматически по
    сохранению индекс не пересоздаётся: каждый ре-эмбеддинг стоит денег
    и на время индексации RAG по документу пустует.
    """
    code = models.SlugField(
        'Код', max_length=50, unique=True, db_index=True,
        help_text='Стабильный идентификатор документа (например, fz-152).',
    )
    title = models.CharField('Название', max_length=255)
    text = models.TextField(
        'Текст',
        help_text=(
            'Полный текст документа для RAG. Индекс обновляется экшеном '
            '«Проиндексировать в RAG» на списке документов; при смене '
            'редакции также обновите дату в SKILL QUANTUM SHIELD.'
        ),
    )
    is_active = models.BooleanField(
        'Активен для RAG', default=True,
        help_text='Если выключен — при индексировании чанки документа удаляются из RAG.',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Нормативный документ'
        verbose_name_plural = 'Нормативные документы'
        ordering = ['code']

    def __str__(self):
        return f'{self.code}: {self.title}'
