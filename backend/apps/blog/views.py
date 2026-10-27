"""
Blog views for REST API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.analytics.services import AnalyticsService

from .models import Post
from .serializers import (
    PostSerializer,
    PostListSerializer,
    PostCreateSerializer,
    PostUpdateSerializer,
)


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for blog posts."""
    permission_classes = [AllowAny]
    queryset = Post.objects.filter(status=Post.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        elif self.action == 'create':
            return PostCreateSerializer
        elif self.action in ('update', 'partial_update'):
            return PostUpdateSerializer
        return PostSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Support tag filtering
        if self.request.query_params.get('tag'):
            tag = self.request.query_params['tag'].lower()
            queryset = [
                p for p in queryset
                if tag in [t.lower() for t in p.tags]
            ]
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def like(self, request, pk=None):
        """Record a like for a post."""
        post = self.get_object()
        success, already_liked = AnalyticsService.record_like(request, post)
        return Response({
            'success': success,
            'likes_count': post.likes_count if success else post.likes_count + 1,
            'already_liked': already_liked,
        }, status=status.HTTP_200_OK if success else status.HTTP_429_TOO_MANY_REQUESTS)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def view(self, request, pk=None):
        """Record a view for a post."""
        post = self.get_object()
        AnalyticsService.record_view(request, post)
        return Response({'success': True, 'views_count': post.views_count})
