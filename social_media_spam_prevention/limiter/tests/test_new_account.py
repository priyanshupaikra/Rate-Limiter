"""
Tests for new account restriction logic
"""

from django.test import TestCase, Client
from limiter.models import SocialUser
from django.utils import timezone
from datetime import timedelta
import json


class NewAccountTests(TestCase):
    """Test cases for new account rate limiting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        
        # Create a new user (less than 24 hours old)
        self.new_user = SocialUser.objects.create(
            username='newuser',
            email='new@example.com'
        )
        
        # Create an old user (more than 24 hours old)
        self.old_user = SocialUser.objects.create(
            username='olduser',
            email='old@example.com'
        )
        # Manually set created_at to 25 hours ago
        self.old_user.created_at = timezone.now() - timedelta(hours=25)
        self.old_user.save()
    
    def test_new_account_detection(self):
        """Test that is_new_account() correctly identifies new accounts"""
        self.assertTrue(
            self.new_user.is_new_account(),
            "User created now should be considered new"
        )
        
        self.assertFalse(
            self.old_user.is_new_account(),
            "User created 25 hours ago should not be considered new"
        )
    
    def test_new_account_boundary(self):
        """Test the 24-hour boundary for new accounts"""
        # Create a user at exactly 24 hours ago
        boundary_user = SocialUser.objects.create(
            username='boundaryuser',
            email='boundary@example.com'
        )
        boundary_user.created_at = timezone.now() - timedelta(hours=24, minutes=1)
        boundary_user.save()
        
        self.assertFalse(
            boundary_user.is_new_account(),
            "User created 24+ hours ago should not be new"
        )
        
        # Create a user just under 24 hours ago
        almost_new_user = SocialUser.objects.create(
            username='almostnew',
            email='almostnew@example.com'
        )
        almost_new_user.created_at = timezone.now() - timedelta(hours=23, minutes=59)
        almost_new_user.save()
        
        self.assertTrue(
            almost_new_user.is_new_account(),
            "User created 23h59m ago should still be new"
        )
    
    def test_new_account_reduced_post_limit(self):
        """Test that new accounts get 50% of normal post limit (5 instead of 10)"""
        # This test would require authentication integration
        # For now, we test the logic in the model
        
        # Verify the limits are set correctly in config
        from limiter.config import RATE_LIMIT_RULES
        
        post_rules = RATE_LIMIT_RULES['post_creation']
        self.assertEqual(post_rules['limit'], 10)
        self.assertEqual(post_rules['new_account_limit'], 5)
        
        # Verify it's 50%
        self.assertEqual(
            post_rules['new_account_limit'],
            post_rules['limit'] // 2
        )
    
    def test_new_account_reduced_comment_limit(self):
        """Test that new accounts get 50% of normal comment limit (15 instead of 30)"""
        from limiter.config import RATE_LIMIT_RULES
        
        comment_rules = RATE_LIMIT_RULES['comment_creation']
        self.assertEqual(comment_rules['limit'], 30)
        self.assertEqual(comment_rules['new_account_limit'], 15)
        
        # Verify it's 50%
        self.assertEqual(
            comment_rules['new_account_limit'],
            comment_rules['limit'] // 2
        )
    
    def test_new_account_reduced_dm_limit(self):
        """Test that new accounts get 50% of normal DM limit (25 instead of 50)"""
        from limiter.config import RATE_LIMIT_RULES
        
        dm_rules = RATE_LIMIT_RULES['direct_message']
        self.assertEqual(dm_rules['limit'], 50)
        self.assertEqual(dm_rules['new_account_limit'], 25)
        
        # Verify it's 50%
        self.assertEqual(
            dm_rules['new_account_limit'],
            dm_rules['limit'] // 2
        )
    
    def test_new_account_threshold_config(self):
        """Test that the new account threshold is set to 24 hours"""
        from limiter.config import NEW_ACCOUNT_THRESHOLD_HOURS
        
        self.assertEqual(NEW_ACCOUNT_THRESHOLD_HOURS, 24)
    
    def test_all_limits_have_new_account_restriction(self):
        """Test that all rate limit rules have new account limits defined"""
        from limiter.config import RATE_LIMIT_RULES
        
        for action, rules in RATE_LIMIT_RULES.items():
            self.assertIn(
                'new_account_limit',
                rules,
                f"Action '{action}' should have new_account_limit defined"
            )
            
            # Verify new account limit is less than normal limit
            self.assertLess(
                rules['new_account_limit'],
                rules['limit'],
                f"Action '{action}' new account limit should be less than normal limit"
            )
            
            # Verify it's exactly 50%
            self.assertEqual(
                rules['new_account_limit'],
                rules['limit'] // 2,
                f"Action '{action}' new account limit should be 50% of normal limit"
            )
    
    def test_user_model_fields(self):
        """Test that User model has required fields"""
        user = SocialUser.objects.create(
            username='testuser',
            email='test@example.com'
        )
        
        # Check that all required fields exist
        self.assertTrue(hasattr(user, 'username'))
        self.assertTrue(hasattr(user, 'email'))
        self.assertTrue(hasattr(user, 'created_at'))
        self.assertTrue(hasattr(user, 'is_new_account'))
        
        # Check that created_at is automatically set
        self.assertIsNotNone(user.created_at)
        
        # Check that is_new_account is callable
        self.assertTrue(callable(user.is_new_account))


if __name__ == '__main__':
    import unittest
    unittest.main()
