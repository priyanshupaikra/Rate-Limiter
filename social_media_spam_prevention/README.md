# Social Media Post/Comment Spam Prevention

A production-ready rate limiting implementation for social media platforms using Django and the Sliding Window Counter algorithm.

## 📋 Overview

This module implements a sophisticated spam prevention system for social media platforms, protecting against:
- **Post spam**: Users flooding feeds with excessive posts
- **Comment spam**: Bots posting hundreds of comments per minute
- **Direct message abuse**: Excessive DM sending

The implementation uses the **Sliding Window Counter** algorithm, which provides ~99.7% accuracy while maintaining low memory usage.

## 🎯 Features

- **Multiple Rate Limits**: Different limits for posts (10/hour), comments (30/15min), and DMs (50/hour)
- **New Account Protection**: Accounts < 24 hours old get 50% of normal limits
- **Dual Identification**: Uses User ID for authenticated users, IP address for anonymous users
- **Thread-Safe**: Built with `threading.Lock` for concurrent request handling
- **HTTP Standards Compliant**: Returns proper 429 responses with standard headers
- **In-Memory Storage**: No Redis dependency - uses efficient in-memory data structures

## 🏗️ Architecture

```
   Mobile App / Web Client
            │
            ▼
    ┌───────────────┐
    │  API Gateway   │
    │  (Nginx/Kong)  │
    └───────┬───────┘
            │
    ┌───────▼───────┐
    │ Rate Limiter   │
    │ Middleware      │
    │                 │
    │ ┌─────────────┐│
    │ │ Rule Engine  ││ ← Loads rules from config
    │ └──────┬──────┘│
    │        │       │
    │ ┌──────▼──────┐│
    │ │Sliding Window││ ← Algorithm: ~99.7% accuracy
    │ │   Counter    ││
    │ └──────┬──────┘│
    └────────┼───────┘
             │
      ┌───────▼───────┐
      │ Django Views  │
      │ (Posts/DMs)   │
      └──────┬───────┘
             │
      ┌───────▼───────┐
      │   Database    │
      │  (SQLite)     │
      └─────────────┘
```

## 📊 Rate Limit Rules

| Action | Normal Limit | New Account Limit | Window |
|--------|-------------|-------------------|---------|
| **Post Creation** | 10 requests | 5 requests | 1 hour |
| **Comment Creation** | 30 requests | 15 requests | 15 minutes |
| **Direct Messages** | 50 requests | 25 requests | 1 hour |

**New Account Definition**: Accounts created less than 24 hours ago

## 🚀 Getting Started

### Prerequisites

```bash
Python 3.8+
Django 3.2+
```

### Installation

1. **Navigate to the module directory**
```bash
cd social_media_spam_prevention
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Start the development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## 📖 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Endpoints

#### 1. Create Post
Create a new social media post.

**Endpoint**: `POST /api/posts/create/`

**Rate Limit**: 10 requests/hour (5 for new accounts)

**Request Body**:
```json
{
  "title": "My Post Title",
  "content": "This is the post content"
}
```

**Success Response** (201 Created):
```json
{
  "success": true,
  "message": "Post created successfully",
  "post": {
    "title": "My Post Title",
    "content": "This is the post content",
    "created_at": "now"
  }
}
```

**Headers**:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1708016400
```

**Example with curl**:
```bash
curl -X POST http://localhost:8000/api/posts/create/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello World", "content": "My first post!"}'
```

#### 2. Create Comment
Create a comment on a post.

**Endpoint**: `POST /api/comments/create/`

**Rate Limit**: 30 requests/15 minutes (15 for new accounts)

**Request Body**:
```json
{
  "post_id": 123,
  "content": "Great post!"
}
```

**Success Response** (201 Created):
```json
{
  "success": true,
  "message": "Comment created successfully",
  "comment": {
    "post_id": 123,
    "content": "Great post!",
    "created_at": "now"
  }
}
```

**Example with curl**:
```bash
curl -X POST http://localhost:8000/api/comments/create/ \
  -H "Content-Type: application/json" \
  -d '{"post_id": 123, "content": "Nice!"}'
```

#### 3. Send Direct Message
Send a direct message to another user.

**Endpoint**: `POST /api/dm/send/`

**Rate Limit**: 50 requests/hour (25 for new accounts)

**Request Body**:
```json
{
  "recipient_id": 456,
  "message": "Hello there!"
}
```

**Success Response** (201 Created):
```json
{
  "success": true,
  "message": "Direct message sent successfully",
  "dm": {
    "recipient_id": 456,
    "message": "Hello there!",
    "sent_at": "now"
  }
}
```

**Example with curl**:
```bash
curl -X POST http://localhost:8000/api/dm/send/ \
  -H "Content-Type: application/json" \
  -d '{"recipient_id": 456, "message": "Hi!"}'
```

#### 4. Health Check
Check API health status (not rate limited).

**Endpoint**: `GET /api/health/`

**Success Response** (200 OK):
```json
{
  "status": "ok",
  "service": "Social Media Spam Prevention API"
}
```

**Example with curl**:
```bash
curl http://localhost:8000/api/health/
```

### Rate Limit Exceeded Response

When rate limit is exceeded, all endpoints return:

**Status**: 429 Too Many Requests

**Response Body**:
```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded. Please retry after 3456 seconds.",
    "retry_after": 3456
  }
}
```

**Headers**:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1708016400
Retry-After: 3456
```

## 🧪 Running Tests

### Run all tests
```bash
python manage.py test
```

### Run specific test modules
```bash
# Test the Sliding Window Counter algorithm
python manage.py test limiter.tests.test_sliding_window

# Test middleware integration
python manage.py test limiter.tests.test_middleware

# Test API endpoints
python manage.py test limiter.tests.test_views

# Test new account restrictions
python manage.py test limiter.tests.test_new_account
```

### Test Coverage
```bash
# Install coverage if needed
pip install coverage

# Run tests with coverage
coverage run --source='limiter' manage.py test

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
```

## 📁 Project Structure

```
social_media_spam_prevention/
├── __init__.py
├── README.md                          # This file
├── manage.py                          # Django management script
├── requirements.txt                   # Python dependencies
│
├── spam_prevention/                   # Django project settings
│   ├── __init__.py
│   ├── settings.py                    # Django configuration
│   ├── urls.py                        # Root URL routing
│   └── wsgi.py                        # WSGI application
│
└── limiter/                           # Main application
    ├── __init__.py
    ├── apps.py                        # App configuration
    ├── models.py                      # SocialUser model
    ├── config.py                      # Rate limit rules
    ├── middleware.py                  # SpamPreventionMiddleware
    ├── decorators.py                  # @rate_limit decorator
    ├── views.py                       # API endpoints
    ├── urls.py                        # App URL routing
    │
    ├── algorithms/                    # Rate limiting algorithms
    │   ├── __init__.py
    │   └── sliding_window_counter.py  # Core algorithm
    │
    └── tests/                         # Test suite
        ├── __init__.py
        ├── test_sliding_window.py     # Algorithm unit tests
        ├── test_middleware.py         # Middleware tests
        ├── test_views.py              # API endpoint tests
        └── test_new_account.py        # New account logic tests
```

## 🔧 Configuration

### Customizing Rate Limits

Edit `limiter/config.py` to customize rate limits:

```python
RATE_LIMIT_RULES = {
    'post_creation': {
        'limit': 10,                    # Max requests
        'window': 3600,                 # Window in seconds
        'new_account_limit': 5,         # Limit for new accounts
        'algorithm': 'sliding_window_counter',
    },
    # ... add more rules
}
```

### New Account Threshold

Change the threshold for "new accounts" in `limiter/config.py`:

```python
NEW_ACCOUNT_THRESHOLD_HOURS = 24  # Hours
```

## 🔬 Algorithm: Sliding Window Counter

### How It Works

The Sliding Window Counter algorithm combines the efficiency of fixed windows with the accuracy of sliding windows:

1. **Tracks two adjacent windows**: Previous and current
2. **Calculates weighted count**:
   ```
   weighted_count = (prev_count × overlap%) + current_count
   ```
3. **Allows/denies based on weighted count**

### Example

```
Window: 60 seconds, Limit: 100 requests
Previous window (0-60s): 84 requests
Current window (60-120s): 36 requests
Current time: 75s (15 seconds into current window)

Overlap = 1 - (15/60) = 0.75 (75% of previous window overlaps)

Weighted count = (84 × 0.75) + 36 = 63 + 36 = 99

99 < 100 → ✅ Request Allowed!
```

### Benefits

- **~99.7% accuracy** (Cloudflare-verified)
- **Low memory**: Only 2 counters + 1 timestamp per client
- **No boundary burst problem**: Smooth enforcement across window boundaries
- **Thread-safe**: Uses locks for concurrent access

## 🛡️ Security Features

- **IP-based limiting** for anonymous users (uses X-Forwarded-For when available)
- **User-based limiting** for authenticated users
- **New account restrictions** to prevent spam bot registration
- **Thread-safe implementation** for production environments
- **No data leakage**: Each client's data is isolated

## 🎓 Use Cases

This implementation is suitable for:

- **Social Media Platforms** (Twitter, Instagram, Reddit-like apps)
- **Forum Systems** (comment spam prevention)
- **Messaging Apps** (DM rate limiting)
- **User-Generated Content Sites** (prevent content flooding)

## 📚 References

- [Sliding Window Counter Algorithm - Cloudflare Blog](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)
- [Rate Limiting Strategies - Google Cloud](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [HTTP 429 Too Many Requests - RFC 6585](https://tools.ietf.org/html/rfc6585#section-4)

## 📝 License

This project is part of the Rate-Limiter repository and follows the same license.

## 👨‍💻 Contributing

Contributions are welcome! Please ensure:
- All tests pass
- Code follows Django best practices
- New features include tests and documentation

## 🙏 Acknowledgments

- Implementation based on production systems at Cloudflare, Twitter, and Stripe
- Algorithm design from Section 5.2 of the main documentation
- Built with Django and Python best practices

---

**Note**: This is a demonstration implementation using in-memory storage. For production use with multiple servers, consider using Redis or another distributed cache for the rate limiter state.
