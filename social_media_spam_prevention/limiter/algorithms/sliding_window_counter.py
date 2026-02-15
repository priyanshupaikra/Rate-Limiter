"""
Sliding Window Counter Algorithm Implementation

This module implements the Sliding Window Counter algorithm for rate limiting.
It provides a good balance between accuracy (~99.7%) and memory efficiency
by using two adjacent fixed windows and weighting the previous window's count.

Thread-safe implementation using threading.Lock.
"""

import time
import threading
from typing import Dict, Tuple


class SlidingWindowCounter:
    """
    Sliding Window Counter algorithm for rate limiting.
    
    This algorithm uses two adjacent fixed windows and weights the previous
    window's count based on how much of it overlaps with the current sliding window.
    
    Args:
        window_size: Size of the time window in seconds
        max_requests: Maximum number of requests allowed in the window
    """
    
    def __init__(self, window_size: int, max_requests: int):
        """
        Initialize the Sliding Window Counter.
        
        Args:
            window_size: Size of the time window in seconds
            max_requests: Maximum number of requests allowed in the window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        
        # Store data for each client: {client_id: (prev_count, curr_count, curr_window_start)}
        self._clients: Dict[str, Tuple[int, int, float]] = {}
        self._lock = threading.Lock()
    
    def allow_request(self, client_id: str) -> bool:
        """
        Check if a request should be allowed and increment the counter if so.
        
        Args:
            client_id: Unique identifier for the client (user ID or IP address)
            
        Returns:
            True if the request is allowed, False if rate limited
        """
        with self._lock:
            now = time.time()
            
            # Get or initialize client data
            if client_id not in self._clients:
                self._clients[client_id] = (0, 0, now)
            
            prev_count, curr_count, curr_window_start = self._clients[client_id]
            
            # Calculate elapsed time since current window started
            elapsed = now - curr_window_start
            
            # Check if we need to rotate the window
            if elapsed >= self.window_size:
                # Move to a new window
                prev_count = curr_count
                curr_count = 0
                curr_window_start = now
                elapsed = 0
            
            # Calculate the overlap percentage (how much of previous window is in current sliding window)
            overlap = 1 - (elapsed / self.window_size)
            
            # Calculate weighted count
            weighted_count = (prev_count * overlap) + curr_count
            
            # Check if request should be allowed
            if weighted_count < self.max_requests:
                # Allow the request and increment counter
                curr_count += 1
                self._clients[client_id] = (prev_count, curr_count, curr_window_start)
                return True
            else:
                # Rate limited
                return False
    
    def get_remaining(self, client_id: str) -> int:
        """
        Get the number of remaining requests for a client in the current window.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Number of remaining requests (0 if rate limited)
        """
        with self._lock:
            now = time.time()
            
            if client_id not in self._clients:
                return self.max_requests
            
            prev_count, curr_count, curr_window_start = self._clients[client_id]
            
            # Calculate elapsed time
            elapsed = now - curr_window_start
            
            # If window has expired, return max
            if elapsed >= self.window_size:
                return self.max_requests
            
            # Calculate overlap and weighted count
            overlap = 1 - (elapsed / self.window_size)
            weighted_count = (prev_count * overlap) + curr_count
            
            # Calculate remaining
            remaining = max(0, int(self.max_requests - weighted_count))
            return remaining
    
    def get_reset_time(self, client_id: str) -> float:
        """
        Get the Unix timestamp when the rate limit window will reset for a client.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Unix timestamp (seconds since epoch) when the window resets
        """
        with self._lock:
            now = time.time()
            
            if client_id not in self._clients:
                return now + self.window_size
            
            _, _, curr_window_start = self._clients[client_id]
            
            # The window resets at the end of the current window
            reset_time = curr_window_start + self.window_size
            
            return reset_time
    
    def reset(self, client_id: str = None):
        """
        Reset the counter for a specific client or all clients.
        
        Args:
            client_id: Client to reset, or None to reset all clients
        """
        with self._lock:
            if client_id is None:
                self._clients.clear()
            elif client_id in self._clients:
                del self._clients[client_id]
