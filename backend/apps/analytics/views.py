"""
Analytics views for REST API.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from apps.projects.models import Project
from apps.blog.models import Post


class AnalyticsStatsView(APIView):
    """Aggregated analytics statistics."""
    permission_classes = [AllowAny]

    def get(self, request):
        projects = Project.objects.aggregate(total_views=Sum('views_count'), total_likes=Sum('likes_count'))
        posts = Post.objects.aggregate(total_views=Sum('views_count'), total_likes=Sum('likes_count'))

        return Response({
            'projects': {
                'count': Project.objects.count(),
                'total_views': projects['total_views'] or 0,
                'total_likes': projects['total_likes'] or 0,
            },
            'posts': {
                'count': Post.objects.filter(status=Post.Status.PUBLISHED).count(),
                'total_views': posts['total_views'] or 0,
                'total_likes': posts['total_likes'] or 0,
            },
        })
