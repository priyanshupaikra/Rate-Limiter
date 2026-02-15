"""
Integration tests for the API views with rate limiting
"""

from django.test import TestCase, Client
from limiter.models import SocialUser
from django.utils import timezone
import json


class ViewTests(TestCase):
    """Test cases for the API views"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        
        # Reset both middleware and decorator rate limiters between tests
        from limiter.decorators import _decorator_limiters
        from limiter.middleware import _rate_limiters
        _decorator_limiters.clear()
        _rate_limiters.clear()
    
    def test_create_post_endpoint(self):
        """Test the create post endpoint"""
        response = self.client.post(
            '/api/posts/create/',
            data=json.dumps({'title': 'Test Post', 'content': 'Test content'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('post', data)
    
    def test_create_comment_endpoint(self):
        """Test the create comment endpoint"""
        response = self.client.post(
            '/api/comments/create/',
            data=json.dumps({'post_id': 123, 'content': 'Great post!'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('comment', data)
    
    def test_send_dm_endpoint(self):
        """Test the send DM endpoint"""
        response = self.client.post(
            '/api/dm/send/',
            data=json.dumps({'recipient_id': 456, 'message': 'Hello!'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('dm', data)
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint (not rate limited)"""
        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
    
    def test_post_creation_rate_limit(self):
        """Test that post creation enforces rate limit"""
        # Make 10 posts (should all succeed)
        for i in range(10):
            response = self.client.post(
                '/api/posts/create/',
                data=json.dumps({'title': f'Post {i}', 'content': 'Content'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201, f"Request {i+1} should succeed")
        
        # 11th post should be rate limited
        response = self.client.post(
            '/api/posts/create/',
            data=json.dumps({'title': 'Post 11', 'content': 'Content'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 429)
    
    def test_comment_creation_rate_limit(self):
        """Test that comment creation enforces rate limit (30 per 15 min)"""
        # Make 30 comments (should all succeed)
        for i in range(30):
            response = self.client.post(
                '/api/comments/create/',
                data=json.dumps({'post_id': 1, 'content': f'Comment {i}'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201, f"Request {i+1} should succeed")
        
        # 31st comment should be rate limited
        response = self.client.post(
            '/api/comments/create/',
            data=json.dumps({'post_id': 1, 'content': 'Comment 31'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 429)
    
    def test_dm_rate_limit(self):
        """Test that DM sending enforces rate limit (50 per hour)"""
        # Make 50 DMs (should all succeed)
        for i in range(50):
            response = self.client.post(
                '/api/dm/send/',
                data=json.dumps({'recipient_id': 123, 'message': f'Message {i}'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201, f"Request {i+1} should succeed")
        
        # 51st DM should be rate limited
        response = self.client.post(
            '/api/dm/send/',
            data=json.dumps({'recipient_id': 123, 'message': 'Message 51'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 429)
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in responses"""
        response = self.client.post(
            '/api/posts/create/',
            data=json.dumps({'title': 'Test', 'content': 'Content'}),
            content_type='application/json'
        )
        
        # Check for rate limit headers
        self.assertIn('X-RateLimit-Limit', response)
        self.assertIn('X-RateLimit-Remaining', response)
        self.assertIn('X-RateLimit-Reset', response)
        
        # Verify header values
        limit = int(response['X-RateLimit-Limit'])
        remaining = int(response['X-RateLimit-Remaining'])
        
        self.assertEqual(limit, 10)
        self.assertLessEqual(remaining, 9)
    
    def test_429_response_includes_retry_after(self):
        """Test that 429 responses include Retry-After header"""
        # Exhaust the limit
        for _ in range(10):
            self.client.post(
                '/api/posts/create/',
                data=json.dumps({'title': 'Test', 'content': 'Content'}),
                content_type='application/json'
            )
        
        # Next request should get 429
        response = self.client.post(
            '/api/posts/create/',
            data=json.dumps({'title': 'Test', 'content': 'Content'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        
        # Retry-After should be a positive integer
        retry_after = int(response['Retry-After'])
        self.assertGreater(retry_after, 0)
    
    def test_invalid_json_handling(self):
        """Test that invalid JSON is handled gracefully"""
        response = self.client.post(
            '/api/posts/create/',
            data='invalid json{',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_health_check_not_rate_limited(self):
        """Test that health check endpoint is never rate limited"""
        # Make many requests to health check
        for _ in range(100):
            response = self.client.get('/api/health/')
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    import unittest
    unittest.main()
