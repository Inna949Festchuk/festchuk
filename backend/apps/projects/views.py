"""
Projects views for REST API.
"""
from django.db.models import F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.analytics.services import AnalyticsService

from .models import Project
from .serializers import (
    ProjectSerializer,
    ProjectListSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for projects."""
    permission_classes = [AllowAny]
    queryset = Project.objects.filter(visibility=Project.Visibility.PUBLIC)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ('update', 'partial_update'):
            return ProjectUpdateSerializer
        return ProjectSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Support filtering
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        if self.request.query_params.get('technology'):
            queryset = [
                p for p in queryset
                if self.request.query_params['technology'].lower() in
                [t.lower() for t in p.technologies]
            ]
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def like(self, request, pk=None):
        """Record a like for a project."""
        project = self.get_object()
        success, already_liked = AnalyticsService.record_like(request, project)
        return Response({
            'success': success,
            'likes_count': project.likes_count if success else project.likes_count + 1,
            'already_liked': already_liked,
        }, status=status.HTTP_200_OK if success else status.HTTP_429_TOO_MANY_REQUESTS)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def view(self, request, pk=None):
        """Record a view for a project."""
        project = self.get_object()
        AnalyticsService.record_view(request, project)
        return Response({'success': True, 'views_count': project.views_count})
