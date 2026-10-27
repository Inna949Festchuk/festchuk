"""
Projects serializers for REST API.
"""
from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """Full project serializer for detail view."""
    technologies = serializers.JSONField()

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


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""
    technologies = serializers.JSONField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'summary', 'technologies',
            'image_preview', 'cover_image', 'github_url',
            'views_count', 'likes_count', 'is_featured', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'likes_count', 'created_at']


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects via API."""

    class Meta:
        model = Project
        fields = [
            'title', 'description', 'summary',
            'github_url', 'demo_url', 'technologies',
            'readme_content', 'image_preview', 'cover_image',
            'visibility', 'order', 'is_featured',
        ]
        extra_kwargs = {
            'readme_content': {'required': False},
            'image_preview': {'required': False},
            'cover_image': {'required': False},
        }


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects."""

    class Meta:
        model = Project
        fields = [
            'title', 'description', 'summary',
            'github_url', 'demo_url', 'technologies',
            'readme_content', 'image_preview', 'cover_image',
            'visibility', 'order', 'is_featured',
        ]
