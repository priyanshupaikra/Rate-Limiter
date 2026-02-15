"""
Unit tests for the Sliding Window Counter algorithm
"""

import time
import unittest
from threading import Thread
from limiter.algorithms import SlidingWindowCounter


class SlidingWindowCounterTests(unittest.TestCase):
    """Test cases for the Sliding Window Counter algorithm"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.limiter = SlidingWindowCounter(window_size=60, max_requests=10)
    
    def tearDown(self):
        """Clean up after tests"""
        self.limiter.reset()
    
    def test_basic_allow_request(self):
        """Test that requests are allowed up to the limit"""
        client_id = "test_user_1"
        
        # Should allow first 10 requests
        for i in range(10):
            self.assertTrue(
                self.limiter.allow_request(client_id),
                f"Request {i+1} should be allowed"
            )
        
        # 11th request should be denied
        self.assertFalse(
            self.limiter.allow_request(client_id),
            "Request 11 should be denied"
        )
    
    def test_get_remaining(self):
        """Test that remaining count is accurate"""
        client_id = "test_user_2"
        
        # Initially should have full limit remaining
        self.assertEqual(self.limiter.get_remaining(client_id), 10)
        
        # After 3 requests, should have 7 remaining
        for _ in range(3):
            self.limiter.allow_request(client_id)
        
        remaining = self.limiter.get_remaining(client_id)
        self.assertGreaterEqual(remaining, 6)
        self.assertLessEqual(remaining, 7)
    
    def test_get_reset_time(self):
        """Test that reset time is calculated correctly"""
        client_id = "test_user_3"
        
        before = time.time()
        self.limiter.allow_request(client_id)
        after = time.time()
        
        reset_time = self.limiter.get_reset_time(client_id)
        
        # Reset time should be approximately 60 seconds in the future
        self.assertGreater(reset_time, before + 59)
        self.assertLess(reset_time, after + 61)
    
    def test_window_rotation(self):
        """Test that window state is maintained correctly over time"""
        # Use a short window for testing
        limiter = SlidingWindowCounter(window_size=1, max_requests=5)
        client_id = "test_user_4"
        
        # Use 3 requests
        for _ in range(3):
            self.assertTrue(limiter.allow_request(client_id))
        
        # Wait for half a window
        time.sleep(0.6)
        
        # The weighted count calculation should allow more requests
        # Previous window had 3, current has 0, overlap ~40%
        # Weighted = 3 * 0.4 + 0 = 1.2, so we have room for 3-4 more
        result = limiter.allow_request(client_id)
        self.assertTrue(result, "Should allow request after partial window elapsed")
    
    def test_multiple_clients(self):
        """Test that different clients have independent limits"""
        client1 = "user_1"
        client2 = "user_2"
        
        # Both clients should have independent limits
        for _ in range(10):
            self.assertTrue(self.limiter.allow_request(client1))
            self.assertTrue(self.limiter.allow_request(client2))
        
        # Both should be rate limited independently
        self.assertFalse(self.limiter.allow_request(client1))
        self.assertFalse(self.limiter.allow_request(client2))
    
    def test_weighted_count_calculation(self):
        """Test that weighted count is calculated correctly"""
        # Use a short window for testing
        limiter = SlidingWindowCounter(window_size=10, max_requests=10)
        client_id = "test_user_5"
        
        # Use 8 requests in first window
        for _ in range(8):
            self.assertTrue(limiter.allow_request(client_id))
        
        # Wait half a window (5 seconds)
        time.sleep(5.1)
        
        # The weighted count should be approximately 8 * 0.5 = 4
        # So we should be able to make about 6 more requests
        allowed_count = 0
        for _ in range(10):
            if limiter.allow_request(client_id):
                allowed_count += 1
            else:
                break
        
        # Should allow at least 1 request (current window has room)
        self.assertGreater(allowed_count, 0)
    
    def test_thread_safety(self):
        """Test that the limiter is thread-safe"""
        client_id = "test_user_6"
        results = []
        
        def make_requests():
            for _ in range(5):
                result = self.limiter.allow_request(client_id)
                results.append(result)
        
        # Create multiple threads
        threads = [Thread(target=make_requests) for _ in range(3)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have made 15 requests total, 10 allowed, 5 denied
        allowed = sum(1 for r in results if r)
        denied = sum(1 for r in results if not r)
        
        self.assertEqual(allowed, 10, "Should allow exactly 10 requests")
        self.assertEqual(denied, 5, "Should deny exactly 5 requests")
    
    def test_reset_specific_client(self):
        """Test resetting a specific client"""
        client1 = "user_1"
        client2 = "user_2"
        
        # Use some requests for both clients
        for _ in range(5):
            self.limiter.allow_request(client1)
            self.limiter.allow_request(client2)
        
        # Reset client1
        self.limiter.reset(client1)
        
        # Client1 should have full limit again
        self.assertEqual(self.limiter.get_remaining(client1), 10)
        
        # Client2 should still have ~5 remaining
        remaining = self.limiter.get_remaining(client2)
        self.assertGreaterEqual(remaining, 4)
        self.assertLessEqual(remaining, 5)
    
    def test_reset_all_clients(self):
        """Test resetting all clients"""
        # Make requests for multiple clients
        for i in range(3):
            client_id = f"user_{i}"
            for _ in range(5):
                self.limiter.allow_request(client_id)
        
        # Reset all
        self.limiter.reset()
        
        # All clients should have full limit
        for i in range(3):
            client_id = f"user_{i}"
            self.assertEqual(self.limiter.get_remaining(client_id), 10)


if __name__ == '__main__':
    unittest.main()
