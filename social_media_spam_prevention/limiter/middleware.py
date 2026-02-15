"""
Rate Limiting Middleware for Social Media Spam Prevention

This middleware intercepts requests and applies rate limiting based on
the configured rules for different actions (posts, comments, DMs).
"""

import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .config import RATE_LIMIT_RULES, PATH_ACTION_MAPPING
from .algorithms import SlidingWindowCounter


# Global rate limiters for each action type
_rate_limiters = {}


def get_rate_limiter(action: str, limit: int, window: int) -> SlidingWindowCounter:
    """
    Get or create a rate limiter for a specific action and limit.
    
    Args:
        action: Action type (post_creation, comment_creation, direct_message)
        limit: Maximum requests allowed
        window: Window size in seconds
        
    Returns:
        SlidingWindowCounter instance
    """
    key = f"{action}:{limit}:{window}"
    if key not in _rate_limiters:
        _rate_limiters[key] = SlidingWindowCounter(window_size=window, max_requests=limit)
    return _rate_limiters[key]


class SpamPreventionMiddleware(MiddlewareMixin):
    """
    Middleware that enforces rate limits on social media actions.
    
    - Maps URL paths to action types (post, comment, DM)
    - Determines client identifier (User ID or IP)
    - Checks if account is new and adjusts limits
    - Returns HTTP 429 with proper headers when rate limited
    """
    
    def process_request(self, request):
        """
        Process incoming request and apply rate limiting.
        
        Args:
            request: Django HttpRequest object
            
        Returns:
            None if allowed, JsonResponse with 429 if rate limited
        """
        # Get the action type from the path
        action = PATH_ACTION_MAPPING.get(request.path)
        
        # Only apply rate limiting to configured paths
        if action is None:
            return None
        
        # Get rate limit rules for this action
        rules = RATE_LIMIT_RULES.get(action)
        if not rules:
            return None
        
        # Determine the client identifier
        # Use User ID if authenticated, otherwise use IP address
        if hasattr(request, 'user') and request.user.is_authenticated:
            client_id = f"user:{request.user.id}"
            
            # Check if this is a new account
            is_new = False
            if hasattr(request.user, 'is_new_account'):
                is_new = request.user.is_new_account()
        else:
            # Use IP address for anonymous users
            client_id = f"ip:{self._get_client_ip(request)}"
            is_new = False
        
        # Determine the limit based on account age
        limit = rules['new_account_limit'] if is_new else rules['limit']
        window = rules['window']
        
        # Get the appropriate rate limiter
        rate_limiter = get_rate_limiter(action, limit, window)
        
        # Check if request is allowed
        allowed = rate_limiter.allow_request(client_id)
        
        # Get rate limit info for headers
        remaining = rate_limiter.get_remaining(client_id)
        reset_time = rate_limiter.get_reset_time(client_id)
        
        # Store rate limit info in request for use in response headers
        request.rate_limit_info = {
            'limit': limit,
            'remaining': remaining,
            'reset': reset_time,
        }
        
        if not allowed:
            # Calculate retry_after in seconds
            retry_after = int(reset_time - time.time())
            retry_after = max(1, retry_after)  # At least 1 second
            
            # Return 429 Too Many Requests
            response = JsonResponse({
                'error': {
                    'code': 429,
                    'message': f'Rate limit exceeded. Please retry after {retry_after} seconds.',
                    'retry_after': retry_after,
                }
            }, status=429)
            
            # Add rate limit headers
            response['X-RateLimit-Limit'] = str(limit)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = str(int(reset_time))
            response['Retry-After'] = str(retry_after)
            
            return response
        
        # Request is allowed, continue processing
        return None
    
    def process_response(self, request, response):
        """
        Add rate limit headers to successful responses.
        
        Args:
            request: Django HttpRequest object
            response: Django HttpResponse object
            
        Returns:
            Response with added rate limit headers
        """
        # Add rate limit headers if they were set during request processing
        if hasattr(request, 'rate_limit_info'):
            info = request.rate_limit_info
            response['X-RateLimit-Limit'] = str(info['limit'])
            response['X-RateLimit-Remaining'] = str(info['remaining'])
            response['X-RateLimit-Reset'] = str(int(info['reset']))
        
        return response
    
    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        
        Args:
            request: Django HttpRequest object
            
        Returns:
            Client IP address as string
        """
        # Check for X-Forwarded-For header (common in reverse proxy setups)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the list
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
