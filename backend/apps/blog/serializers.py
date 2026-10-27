"""
Blog serializers for REST API.
"""
from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    """Full post serializer for detail view."""
    reading_time_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content',
            'cover_image', 'tags', 'status', 'published_at',
            'views_count', 'likes_count', 'tts_audio_url',
            'reading_time_minutes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'views_count', 'likes_count', 'tts_audio_url', 'created_at', 'updated_at']


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""
    reading_time_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'cover_image',
            'tags', 'published_at', 'views_count', 'likes_count',
            'reading_time_minutes',
        ]
        read_only_fields = fields


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts via API."""

    class Meta:
        model = Post
        fields = [
            'title', 'excerpt', 'content',
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
            'title', 'excerpt', 'content',
            'cover_image', 'tags', 'status',
        ]
