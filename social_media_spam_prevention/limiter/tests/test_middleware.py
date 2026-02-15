"""
Tests for the SpamPreventionMiddleware
"""

from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from limiter.middleware import SpamPreventionMiddleware
from limiter.models import SocialUser
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from datetime import timedelta


class SpamPreventionMiddlewareTests(TestCase):
    """Test cases for the spam prevention middleware"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.middleware = SpamPreventionMiddleware(get_response=lambda r: JsonResponse({'success': True}))
        
        # Reset rate limiters between tests
        from limiter.middleware import _rate_limiters
        _rate_limiters.clear()
    
    def test_allows_non_rate_limited_paths(self):
        """Test that non-rate-limited paths are not affected"""
        request = self.factory.get('/api/health/')
        request.user = AnonymousUser()
        
        response = self.middleware.process_request(request)
        
        # Should return None (allow request to proceed)
        self.assertIsNone(response)
    
    def test_rate_limits_post_creation(self):
        """Test that post creation is rate limited"""
        request = self.factory.post('/api/posts/create/')
        request.user = AnonymousUser()
        
        # Make 10 requests (should all succeed)
        for i in range(10):
            response = self.middleware.process_request(request)
            self.assertIsNone(response, f"Request {i+1} should be allowed")
        
        # 11th request should be rate limited
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 429)
    
    def test_429_response_format(self):
        """Test that 429 responses have correct format and headers"""
        request = self.factory.post('/api/comments/create/')
        request.user = AnonymousUser()
        
        # Exhaust the limit
        for _ in range(30):
            self.middleware.process_request(request)
        
        # Next request should get 429
        response = self.middleware.process_request(request)
        
        # Check status code
        self.assertEqual(response.status_code, 429)
        
        # Check headers
        self.assertIn('X-RateLimit-Limit', response)
        self.assertIn('X-RateLimit-Remaining', response)
        self.assertIn('X-RateLimit-Reset', response)
        self.assertIn('Retry-After', response)
        
        # Check response body
        import json
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 429)
        self.assertIn('retry_after', data['error'])
    
    def test_rate_limit_headers_on_success(self):
        """Test that rate limit headers are added to successful responses"""
        request = self.factory.post('/api/dm/send/')
        request.user = AnonymousUser()
        
        # Make a request
        self.middleware.process_request(request)
        
        # Create a mock successful response
        success_response = JsonResponse({'success': True})
        
        # Process the response through middleware
        response = self.middleware.process_response(request, success_response)
        
        # Check that headers were added
        self.assertIn('X-RateLimit-Limit', response)
        self.assertIn('X-RateLimit-Remaining', response)
        self.assertIn('X-RateLimit-Reset', response)
    
    def test_different_actions_have_different_limits(self):
        """Test that different actions have independent rate limits"""
        # Post creation (10 per hour)
        post_request = self.factory.post('/api/posts/create/')
        post_request.user = AnonymousUser()
        
        # Comment creation (30 per 15 min)
        comment_request = self.factory.post('/api/comments/create/')
        comment_request.user = AnonymousUser()
        
        # Use up post limit
        for _ in range(10):
            self.middleware.process_request(post_request)
        
        # Post should be rate limited
        response = self.middleware.process_request(post_request)
        self.assertEqual(response.status_code, 429)
        
        # Comments should still work
        response = self.middleware.process_request(comment_request)
        self.assertIsNone(response)
    
    def test_ip_based_rate_limiting_for_anonymous(self):
        """Test that anonymous users are rate limited by IP"""
        request1 = self.factory.post('/api/posts/create/')
        request1.user = AnonymousUser()
        request1.META['REMOTE_ADDR'] = '192.168.1.1'
        
        request2 = self.factory.post('/api/posts/create/')
        request2.user = AnonymousUser()
        request2.META['REMOTE_ADDR'] = '192.168.1.2'
        
        # Use up limit for first IP
        for _ in range(10):
            self.middleware.process_request(request1)
        
        # First IP should be rate limited
        response = self.middleware.process_request(request1)
        self.assertEqual(response.status_code, 429)
        
        # Second IP should still work (different IP, different limit)
        response = self.middleware.process_request(request2)
        self.assertIsNone(response)
    
    def test_x_forwarded_for_header(self):
        """Test that X-Forwarded-For header is respected"""
        request = self.factory.post('/api/posts/create/')
        request.user = AnonymousUser()
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Should use the first IP from X-Forwarded-For
        self.middleware.process_request(request)
        
        # Make another request from different X-Forwarded-For
        request2 = self.factory.post('/api/posts/create/')
        request2.user = AnonymousUser()
        request2.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.2, 192.168.1.1'
        request2.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Should have independent limits
        response = self.middleware.process_request(request2)
        self.assertIsNone(response)


if __name__ == '__main__':
    import unittest
    unittest.main()
