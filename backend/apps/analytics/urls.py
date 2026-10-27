"""
Analytics app URL configuration.
"""
from django.urls import path
from .views import AnalyticsStatsView

urlpatterns = [
    path('stats/', AnalyticsStatsView.as_view(), name='analytics-stats'),
]
