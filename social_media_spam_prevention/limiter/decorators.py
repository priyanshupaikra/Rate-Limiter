"""
Rate Limiting Decorators

Provides decorators to apply rate limiting to individual Django views.
"""

import time
from functools import wraps
from django.http import JsonResponse
from .config import RATE_LIMIT_RULES
from .algorithms import SlidingWindowCounter


# Global rate limiters for decorator usage
_decorator_limiters = {}


def get_decorator_limiter(action: str, limit: int, window: int) -> SlidingWindowCounter:
    """
    Get or create a rate limiter for decorator usage.
    
    Args:
        action: Action type
        limit: Maximum requests allowed
        window: Window size in seconds
        
    Returns:
        SlidingWindowCounter instance
    """
    key = f"{action}:{limit}:{window}"
    if key not in _decorator_limiters:
        _decorator_limiters[key] = SlidingWindowCounter(window_size=window, max_requests=limit)
    return _decorator_limiters[key]


def rate_limit(action=None, limit=None, window=None):
    """
    Decorator to apply rate limiting to a view function.
    
    Can be used in two ways:
    1. With action name (uses configured limits):
       @rate_limit(action='post_creation')
       
    2. With custom limits:
       @rate_limit(limit=50, window=3600)
    
    Args:
        action: Action name from RATE_LIMIT_RULES (post_creation, comment_creation, direct_message)
        limit: Custom limit (overrides action's limit)
        window: Custom window in seconds (overrides action's window)
        
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Determine the rate limit parameters
            if action and action in RATE_LIMIT_RULES:
                rules = RATE_LIMIT_RULES[action]
                effective_limit = limit if limit is not None else rules['limit']
                effective_window = window if window is not None else rules['window']
                
                # Check if account is new and adjust limit
                if hasattr(request, 'user') and request.user.is_authenticated:
                    if hasattr(request.user, 'is_new_account') and request.user.is_new_account():
                        effective_limit = rules.get('new_account_limit', effective_limit)
            elif limit is not None and window is not None:
                # Custom limits provided
                effective_limit = limit
                effective_window = window
            else:
                # No valid configuration
                return view_func(request, *args, **kwargs)
            
            # Determine client identifier
            if hasattr(request, 'user') and request.user.is_authenticated:
                client_id = f"user:{request.user.id}"
            else:
                # Use IP for anonymous users
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0].strip()
                else:
                    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                client_id = f"ip:{ip}"
            
            # Get the rate limiter
            limiter_key = action or f"custom:{effective_limit}:{effective_window}"
            rate_limiter = get_decorator_limiter(limiter_key, effective_limit, effective_window)
            
            # Check if request is allowed
            allowed = rate_limiter.allow_request(client_id)
            
            # Get rate limit info
            remaining = rate_limiter.get_remaining(client_id)
            reset_time = rate_limiter.get_reset_time(client_id)
            
            if not allowed:
                # Calculate retry_after
                retry_after = int(reset_time - time.time())
                retry_after = max(1, retry_after)
                
                # Return 429 response
                response = JsonResponse({
                    'error': {
                        'code': 429,
                        'message': f'Rate limit exceeded. Please retry after {retry_after} seconds.',
                        'retry_after': retry_after,
                    }
                }, status=429)
                
                # Add headers
                response['X-RateLimit-Limit'] = str(effective_limit)
                response['X-RateLimit-Remaining'] = '0'
                response['X-RateLimit-Reset'] = str(int(reset_time))
                response['Retry-After'] = str(retry_after)
                
                return response
            
            # Call the view
            response = view_func(request, *args, **kwargs)
            
            # Add rate limit headers to successful response
            response['X-RateLimit-Limit'] = str(effective_limit)
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Reset'] = str(int(reset_time))
            
            return response
        
        return wrapper
    return decorator
