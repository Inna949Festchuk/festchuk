"""
Blog serializers for REST API.

Localized fields (title/excerpt/content) are resolved via the ``lang`` key
in the serializer context (query param ``?lang=ru|en``), with fallback to
Russian when the requested language is empty.
"""
from rest_framework import serializers
from .models import Post

VALID_LANGS = ('ru', 'en')


def _lang_from_context(context: dict) -> str:
    lang = (context or {}).get('lang', 'ru')
    return lang if lang in VALID_LANGS else 'ru'


class PostSerializer(serializers.ModelSerializer):
    """Full post serializer for detail view."""
    reading_time_minutes = serializers.IntegerField(read_only=True)
    title = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content',
            'cover_image', 'tags', 'status', 'published_at',
            'views_count', 'likes_count', 'tts_audio_url',
            'reading_time_minutes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'likes_count', 'tts_audio_url', 'created_at', 'updated_at']

    def get_title(self, obj):
        return obj.get_field('title', _lang_from_context(self.context))

    def get_excerpt(self, obj):
        return obj.get_field('excerpt', _lang_from_context(self.context))

    def get_content(self, obj):
        return obj.get_field('content', _lang_from_context(self.context))


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""
    reading_time_minutes = serializers.IntegerField(read_only=True)
    title = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'cover_image',
            'tags', 'published_at', 'views_count', 'likes_count',
            'reading_time_minutes',
        ]
        read_only_fields = fields

    def get_title(self, obj):
        return obj.get_field('title', _lang_from_context(self.context))

    def get_excerpt(self, obj):
        return obj.get_field('excerpt', _lang_from_context(self.context))


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts via API.

    Accepts localized fields (``*_ru`` / ``*_en``); Russian is required.
    """

    class Meta:
        model = Post
        fields = [
            'title_ru', 'title_en',
            'excerpt_ru', 'excerpt_en',
            'content_ru', 'content_en',
            'cover_image', 'tags', 'status',
        ]
        extra_kwargs = {
            'cover_image': {'required': False},
        }


class PostUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating posts."""

    class Meta:
        model = Post
        fields = [
            'title_ru', 'title_en',
            'excerpt_ru', 'excerpt_en',
            'content_ru', 'content_en',
            'cover_image', 'tags', 'status',
        ]