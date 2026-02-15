"""
URL Configuration for the Limiter App
"""

from django.urls import path
from . import views

app_name = 'limiter'

urlpatterns = [
    path('posts/create/', views.create_post, name='create_post'),
    path('comments/create/', views.create_comment, name='create_comment'),
    path('dm/send/', views.send_dm, name='send_dm'),
    path('health/', views.health_check, name='health_check'),
]
