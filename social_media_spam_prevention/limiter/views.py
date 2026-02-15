"""
Sample API Views for Social Media Spam Prevention

These views demonstrate the rate limiting functionality for different
social media actions: creating posts, comments, and sending direct messages.
"""

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .decorators import rate_limit


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit(action='post_creation')
def create_post(request):
    """
    Create a new post.
    
    Rate limited to 10 posts per hour (5 for new accounts).
    
    POST /api/posts/create/
    {
        "title": "Post title",
        "content": "Post content"
    }
    """
    try:
        # Parse request body
        if request.body:
            data = json.loads(request.body)
        else:
            data = {}
        
        title = data.get('title', '')
        content = data.get('content', '')
        
        # In a real application, save to database here
        # For demo purposes, just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Post created successfully',
            'post': {
                'title': title,
                'content': content,
                'created_at': 'now',
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit(action='comment_creation')
def create_comment(request):
    """
    Create a new comment.
    
    Rate limited to 30 comments per 15 minutes (15 for new accounts).
    
    POST /api/comments/create/
    {
        "post_id": 123,
        "content": "Comment content"
    }
    """
    try:
        # Parse request body
        if request.body:
            data = json.loads(request.body)
        else:
            data = {}
        
        post_id = data.get('post_id')
        content = data.get('content', '')
        
        # In a real application, save to database here
        # For demo purposes, just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Comment created successfully',
            'comment': {
                'post_id': post_id,
                'content': content,
                'created_at': 'now',
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit(action='direct_message')
def send_dm(request):
    """
    Send a direct message.
    
    Rate limited to 50 DMs per hour (25 for new accounts).
    
    POST /api/dm/send/
    {
        "recipient_id": 456,
        "message": "Hello!"
    }
    """
    try:
        # Parse request body
        if request.body:
            data = json.loads(request.body)
        else:
            data = {}
        
        recipient_id = data.get('recipient_id')
        message = data.get('message', '')
        
        # In a real application, save to database here
        # For demo purposes, just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Direct message sent successfully',
            'dm': {
                'recipient_id': recipient_id,
                'message': message,
                'sent_at': 'now',
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


def health_check(request):
    """
    Simple health check endpoint (not rate limited).
    
    GET /api/health/
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'Social Media Spam Prevention API'
    })
