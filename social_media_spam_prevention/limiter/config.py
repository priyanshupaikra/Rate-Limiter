"""
Rate Limit Configuration for Social Media Spam Prevention

This module defines the rate limiting rules for different actions
in a social media platform (posts, comments, direct messages).
"""

# Rate limit rules for different actions
RATE_LIMIT_RULES = {
    'post_creation': {
        'limit': 10,                    # Max 10 posts per hour
        'window': 3600,                 # 1 hour in seconds
        'new_account_limit': 5,         # 50% of normal limit for new accounts
        'algorithm': 'sliding_window_counter',
    },
    'comment_creation': {
        'limit': 30,                    # Max 30 comments per 15 minutes
        'window': 900,                  # 15 minutes in seconds
        'new_account_limit': 15,        # 50% of normal limit for new accounts
        'algorithm': 'sliding_window_counter',
    },
    'direct_message': {
        'limit': 50,                    # Max 50 DMs per hour
        'window': 3600,                 # 1 hour in seconds
        'new_account_limit': 25,        # 50% of normal limit for new accounts
        'algorithm': 'sliding_window_counter',
    },
}

# New account threshold (24 hours in hours)
NEW_ACCOUNT_THRESHOLD_HOURS = 24

# Path mapping for middleware (URL path -> action type)
PATH_ACTION_MAPPING = {
    '/api/posts/create/': 'post_creation',
    '/api/comments/create/': 'comment_creation',
    '/api/dm/send/': 'direct_message',
}
