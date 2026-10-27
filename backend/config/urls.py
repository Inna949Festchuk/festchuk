"""
URL configuration for Festchuk project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.projects.urls')),
    path('api/', include('apps.blog.urls')),
    path('api/', include('apps.analytics.urls')),
    path('api/', include('apps.ai_agent.urls')),
    path('api/health/', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
