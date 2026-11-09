"""
AI Agent models for Festchuk portfolio.
"""
import uuid

from django.db import models
from django.utils import timezone
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


class ChatSession(models.Model):
    """AI chat session for a user (identified by IP hash)."""

    session_id = models.UUIDField(
        'Session ID',
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    ip_hash = models.CharField('IP Hash', max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    last_active_at = models.DateTimeField('Активность', default=timezone.now)

    class Meta:
        verbose_name = 'Сессия чата'
        verbose_name_plural = 'Сессии чата'
        ordering = ['-last_active_at']

    def __str__(self):
        return f"Session {str(self.session_id)[:8]}..."

    def touch(self):
        """Update last activity timestamp."""
        self.last_active_at = timezone.now()
        self.save(update_fields=['last_active_at'])


class ChatMessage(models.Model):
    """Individual message in a chat session."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField('Роль', max_length=10, choices=Role.choices)
    content = models.TextField('Контент')
    audio_url = models.URLField('Аудио URL', blank=True, null=True)
    tokens_used = models.PositiveIntegerField('Токены', default=0)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class DocumentEmbedding(models.Model):
    """Vector embedding for RAG retrieval."""

    class SourceType(models.TextChoices):
        PROJECT = 'project', 'Проект'
        BLOG_POST = 'blog_post', 'Статья'

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
