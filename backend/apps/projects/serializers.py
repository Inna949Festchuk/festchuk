"""
Projects serializers for REST API.

Localized fields (title/summary/description/readme) are resolved via the
``lang`` key in the serializer context (query param ``?lang=ru|en``),
with fallback to Russian when the requested language is empty.
"""
from django.conf import settings
from rest_framework import serializers
from .models import Project

VALID_LANGS = ('ru', 'en')


def _lang_from_context(context: dict) -> str:
    lang = (context or {}).get('lang', 'ru')
    return lang if lang in VALID_LANGS else 'ru'


class MediaUrlField(serializers.Field):
    """
    Serializes an ImageField as a browser-resolvable absolute URL.

    Without this, DRF builds the URL from the Host header of the *internal*
    proxy request (Host: backend:8000), which the user's browser cannot
    resolve (ERR_NAME_NOT_RESOLVED). When API_BASE_URL is configured we build
    the URL ourselves from that setting instead.
    """

    def __init__(self, field_name=None, **kwargs):
        super().__init__(**kwargs)
        self.field_name = field_name

    def get_attribute(self, obj):
        # Return the FieldFile itself; to_representation handles empty files.
        return getattr(obj, self.field_name)

    def to_representation(self, value):
        rel = getattr(value, 'name', value)
        if not rel:
            return None
        path = f"{settings.MEDIA_URL}{rel}"
        base = getattr(settings, 'API_BASE_URL', '')
        if base:
            return base.rstrip('/') + path
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(path)
        return path


class ProjectSerializer(serializers.ModelSerializer):
    """Full project serializer for detail view."""
    technologies = serializers.JSONField()
    title = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    readme_content = serializers.SerializerMethodField()
    image_preview = MediaUrlField('image_preview')
    cover_image = MediaUrlField('cover_image')

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'description', 'summary',
            'github_url', 'demo_url', 'technologies',
            'readme_content', 'image_preview', 'cover_image',
            'views_count', 'likes_count', 'visibility',
            'is_featured', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'likes_count', 'created_at', 'updated_at']

    def get_title(self, obj):
        return obj.get_field('title', _lang_from_context(self.context))

    def get_summary(self, obj):
        return obj.get_field('summary', _lang_from_context(self.context))

    def get_description(self, obj):
        return obj.get_field('description', _lang_from_context(self.context))

    def get_readme_content(self, obj):
        return obj.get_field('readme', _lang_from_context(self.context))


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""
    technologies = serializers.JSONField()
    title = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    image_preview = MediaUrlField('image_preview')
    cover_image = MediaUrlField('cover_image')

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'summary', 'technologies',
            'image_preview', 'cover_image', 'github_url',
            'views_count', 'likes_count', 'is_featured', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'likes_count', 'created_at']

    def get_title(self, obj):
        return obj.get_field('title', _lang_from_context(self.context))

    def get_summary(self, obj):
        return obj.get_field('summary', _lang_from_context(self.context))


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects via API.

    Accepts localized fields (``*_ru`` / ``*_en``); Russian is required.
    """

    class Meta:
        model = Project
        fields = [
            'title_ru', 'title_en',
            'description_ru', 'description_en',
            'summary_ru', 'summary_en',
            'github_url', 'demo_url', 'technologies',
            'readme_ru', 'readme_en', 'image_preview', 'cover_image',
            'visibility', 'order', 'is_featured',
        ]
        extra_kwargs = {
            'readme_en': {'required': False},
            'image_preview': {'required': False},
            'cover_image': {'required': False},
        }


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects."""

    class Meta:
        model = Project
        fields = [
            'title_ru', 'title_en',
            'description_ru', 'description_en',
            'summary_ru', 'summary_en',
            'github_url', 'demo_url', 'technologies',
            'readme_ru', 'readme_en', 'image_preview', 'cover_image',
            'visibility', 'order', 'is_featured',
        ]