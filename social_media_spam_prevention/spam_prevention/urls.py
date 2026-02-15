"""
URL configuration for spam_prevention project.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('limiter.urls')),
]
