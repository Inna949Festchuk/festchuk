"""
AI Agent application for Festchuk project.
"""
from django.apps import AppConfig


class AIAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_agent'
    verbose_name = 'AI Agent'
