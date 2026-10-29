"""
Projects views for REST API.
"""
from django.db.models import F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.analytics.services import AnalyticsService
from config.throttling import ClientIPScopedRateThrottle

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
    # The frontend links to /api/projects/<slug>/; the default pk lookup 404'd
    # every detail page.
    lookup_field = 'slug'
    # 35 projects with PAGE_SIZE=20 silently hid 15 of them, and the paginated
    # `next` URL leaked the internal Docker host (http://backend:8000/...).
    pagination_class = None
    throttle_scope = 'write'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ('update', 'partial_update'):
            return ProjectUpdateSerializer
        return ProjectSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lang = self.request.query_params.get('lang', 'ru')
        context['lang'] = lang if lang in ('ru', 'en') else 'ru'
        return context

    def get_throttles(self):
        if self.action in ('like', 'view'):
            return [ClientIPScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        queryset = super().get_queryset()
        # Support filtering
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        technology = self.request.query_params.get('technology')
        if technology:
            wanted = technology.lower()
            # technologies is a JSON list with no portable case-insensitive
            # containment lookup, so match in Python — but hand DRF a QuerySet
            # back, since a bare list breaks get_object() and pagination.
            matching = [
                p.pk for p in queryset
                if wanted in [t.lower() for t in p.technologies]
            ]
            queryset = queryset.filter(pk__in=matching)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def like(self, request, slug=None):
        """Record a like for a project."""
        project = self.get_object()
        success, already_liked = AnalyticsService.record_like(request, project)
        return Response({
            'success': success,
            'likes_count': project.likes_count if success else project.likes_count + 1,
            'already_liked': already_liked,
        }, status=status.HTTP_200_OK if success else status.HTTP_429_TOO_MANY_REQUESTS)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def view(self, request, slug=None):
        """Record a view for a project."""
        project = self.get_object()
        AnalyticsService.record_view(request, project)
        return Response({'success': True, 'views_count': project.views_count})

