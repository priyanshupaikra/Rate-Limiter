"""
Models for the Social Media Spam Prevention system
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
from .config import NEW_ACCOUNT_THRESHOLD_HOURS


class SocialUser(models.Model):
    """
    User model for the social media platform.
    
    Tracks user information and account age for rate limiting purposes.
    """
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Social User"
        verbose_name_plural = "Social Users"
    
    def __str__(self):
        return self.username
    
    def is_new_account(self) -> bool:
        """
        Check if this account is considered "new" (created within the threshold).
        
        New accounts (< 24 hours old) get reduced rate limits (50% of normal).
        
        Returns:
            True if the account is less than NEW_ACCOUNT_THRESHOLD_HOURS old
        """
        account_age = timezone.now() - self.created_at
        threshold = timedelta(hours=NEW_ACCOUNT_THRESHOLD_HOURS)
        return account_age < threshold
