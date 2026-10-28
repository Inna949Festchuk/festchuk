"""
Projects serializers for REST API.

Localized fields (title/summary/description/readme) are resolved via the
``lang`` key in the serializer context (query param ``?lang=ru|en``),
with fallback to Russian when the requested language is empty.
"""
from rest_framework import serializers
from .models import Project

VALID_LANGS = ('ru', 'en')


def _lang_from_context(context: dict) -> str:
    lang = (context or {}).get('lang', 'ru')
    return lang if lang in VALID_LANGS else 'ru'


class ProjectSerializer(serializers.ModelSerializer):
    """Full project serializer for detail view."""
    technologies = serializers.JSONField()
    title = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    readme_content = serializers.SerializerMethodField()

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