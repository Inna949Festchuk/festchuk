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
        projects = Project.objects.filter(visibility=Project.Visibility.PUBLIC)
        posts = Post.objects.filter(status=Post.Status.PUBLISHED)
        project_totals = projects.aggregate(total_views=Sum('views_count'), total_likes=Sum('likes_count'))
        post_totals = posts.aggregate(total_views=Sum('views_count'), total_likes=Sum('likes_count'))

        return Response({
            'projects': {
                'count': projects.count(),
                'total_views': project_totals['total_views'] or 0,
                'total_likes': project_totals['total_likes'] or 0,
            },
            'posts': {
                'count': posts.count(),
                'total_views': post_totals['total_views'] or 0,
                'total_likes': post_totals['total_likes'] or 0,
            },
        })
