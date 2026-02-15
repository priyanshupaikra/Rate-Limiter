"""
Django app configuration for the limiter app
"""

from django.apps import AppConfig


class LimiterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'limiter'
    verbose_name = 'Rate Limiter'
