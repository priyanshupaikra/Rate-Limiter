# 📚 Rate Limiter — Complete Documentation

> A comprehensive guide to understanding Rate Limiting: algorithms, components, metrics, HTTP headers, and real-world system designs.

---

## Table of Contents

- [1. Core Rate Limiting Algorithms](#1-core-rate-limiting-algorithms)
  - [1.1 Token Bucket](#11-token-bucket)
  - [1.2 Leaky Bucket](#12-leaky-bucket)
  - [1.3 Fixed Window Counter](#13-fixed-window-counter)
  - [1.4 Sliding Window Log](#14-sliding-window-log)
  - [1.5 Sliding Window Counter](#15-sliding-window-counter)
- [2. Essential System Components](#2-essential-system-components)
  - [2.1 Client Identifier](#21-client-identifier)
  - [2.2 Rules / Policies](#22-rules--policies)
  - [2.3 Storage (Redis)](#23-storage-redis)
- [3. Key Performance & Technical Metrics](#3-key-performance--technical-metrics)
  - [3.1 High Availability](#31-high-availability)
  - [3.2 Latency](#32-latency)
  - [3.3 Race Condition](#33-race-condition)
  - [3.4 HTTP 429 (Too Many Requests)](#34-http-429-too-many-requests)
- [4. HTTP Headers for Rate Limiting](#4-http-headers-for-rate-limiting)
- [5. Design a Rate Limiter for Real-Life Problems](#5-design-a-rate-limiter-for-real-life-problems)
  - [5.1 E-Commerce Flash Sale API](#51-e-commerce-flash-sale-api)
  - [5.2 Social Media Post/Comment Spam Prevention](#52-social-media-postcomment-spam-prevention)
  - [5.3 Banking / Payment Gateway Transaction Limiter](#53-banking--payment-gateway-transaction-limiter)

---

## 1. Core Rate Limiting Algorithms

Rate limiting algorithms control how many requests a client can make to a server within a given timeframe. Choosing the right algorithm depends on your traffic pattern, tolerance for bursts, and memory constraints.

---

### 1.1 Token Bucket

#### 💡 Concept

The **Token Bucket** algorithm uses a metaphorical "bucket" that holds a fixed number of **tokens**. Tokens are added to the bucket at a **constant rate** (e.g., 10 tokens per second). Each incoming request **consumes one token**. If the bucket is empty, the request is **rejected** (or queued).

#### How It Works (Step-by-Step)

1. A bucket is initialized with a **maximum capacity** (e.g., 100 tokens).
2. Tokens are added at a **fixed refill rate** (e.g., 10 tokens/second).
3. When a request arrives:
   - If **tokens > 0** → allow the request and decrement the token count.
   - If **tokens == 0** → reject the request (HTTP 429).
4. The bucket **never exceeds** its maximum capacity, even if no requests are made for a long time.

#### Characteristics

| Property | Detail |
|---|---|
| **Burst Handling** | ✅ Allows bursts up to bucket capacity |
| **Smoothing** | Moderate — bursts are allowed, then throttled |
| **Memory Usage** | Very Low — only stores token count and last refill timestamp |
| **Complexity** | Simple |

#### Visual Diagram

```
  Tokens added at fixed rate
         ↓  ↓  ↓
    ┌──────────────┐
    │  🪣 Bucket    │  ← Max Capacity (e.g., 100)
    │  Tokens: 73   │
    └──────┬───────┘
           │
     Request arrives
           │
    ┌──────▼───────┐
    │ Tokens > 0?  │
    │  YES → Allow │
    │  NO  → Deny  │
    └──────────────┘
```

#### Example Use Case

- **API Gateways** (e.g., AWS API Gateway uses Token Bucket)
- Allowing a user to make 100 API calls per minute, but tolerating short bursts of 20 calls in 1 second.

#### Pseudocode

```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity          # Max tokens
        self.tokens = capacity            # Start full
        self.refill_rate = refill_rate    # Tokens added per second
        self.last_refill = time.now()

    def allow_request(self):
        self._refill()
        if self.tokens > 0:
            self.tokens -= 1
            return True   # ✅ Request Allowed
        return False      # ❌ Rate Limited

    def _refill(self):
        now = time.now()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
```

---

### 1.2 Leaky Bucket

#### 💡 Concept

The **Leaky Bucket** algorithm works like a bucket with a **small hole at the bottom**. Requests are added to the bucket (queue), and they are processed (leaked out) at a **constant, fixed rate**. If the bucket (queue) is full, new incoming requests are **dropped**.

Unlike Token Bucket, this algorithm **does not allow bursts** — it enforces a perfectly smooth, constant output rate.

#### How It Works (Step-by-Step)

1. A FIFO queue is initialized with a **fixed size** (e.g., 50 requests).
2. Incoming requests are **added to the queue**.
3. Requests are **processed from the queue at a constant rate** (e.g., 5 requests/second).
4. If the queue is **full**, new requests are **dropped immediately**.

#### Characteristics

| Property | Detail |
|---|---|
| **Burst Handling** | ❌ No bursts — output is always constant |
| **Smoothing** | Excellent — perfectly smooth traffic |
| **Memory Usage** | Moderate — stores the queue of pending requests |
| **Complexity** | Simple |

#### Visual Diagram

```
  Incoming Requests
     ↓  ↓  ↓  ↓  ↓
  ┌──────────────────┐
  │  🪣 Queue/Bucket  │  ← Fixed Size (e.g., 50)
  │  [req][req][req]  │
  └────────┬─────────┘
           │
    Leaks at constant rate
     (e.g., 5 req/sec)
           │
     ┌─────▼─────┐
     │  Process   │
     │  Request   │
     └───────────┘

  ⚠️ If queue is full → new requests are DROPPED
```

#### Example Use Case

- **Network Traffic Shaping** — ISPs use leaky bucket to smooth out packet transmission.
- **Chat Applications** — Limit how fast a user can send messages (e.g., 1 message/second).

#### Pseudocode

```python
class LeakyBucket:
    def __init__(self, capacity, leak_rate):
        self.capacity = capacity      # Max queue size
        self.queue = []
        self.leak_rate = leak_rate    # Requests processed per second
        self.last_leak = time.now()

    def allow_request(self, request):
        self._leak()
        if len(self.queue) < self.capacity:
            self.queue.append(request)
            return True   # ✅ Queued
        return False      # ❌ Dropped

    def _leak(self):
        now = time.now()
        elapsed = now - self.last_leak
        leaked = int(elapsed * self.leak_rate)
        self.queue = self.queue[leaked:]  # Remove processed requests
        self.last_leak = now
```

---

### 1.3 Fixed Window Counter

#### 💡 Concept

The **Fixed Window Counter** algorithm divides time into **fixed, non-overlapping intervals** (called "windows") — for example, every 1-minute block. A **counter** tracks the number of requests in the current window. At the **start of each new window**, the counter **resets to zero**.

#### How It Works (Step-by-Step)

1. Define a window size (e.g., 60 seconds) and a limit (e.g., 100 requests).
2. When a request arrives:
   - Determine the **current time window** (e.g., `12:00:00 – 12:00:59`).
   - **Increment** the counter for that window.
   - If counter **≤ limit** → allow.
   - If counter **> limit** → reject (HTTP 429).
3. When a new window starts, the counter **resets**.

#### ⚠️ The Boundary Problem

The major flaw of this algorithm is the **boundary burst problem**. A user can send the maximum allowed requests at the **end** of one window and the **beginning** of the next, effectively doubling the rate for a brief period.

```
Window 1: [............100 requests at 12:00:55-12:00:59]
Window 2: [100 requests at 12:01:00-12:01:05............]

→ 200 requests in just 10 seconds! (Double the intended 100/min limit)
```

#### Characteristics

| Property | Detail |
|---|---|
| **Burst Handling** | ⚠️ Vulnerable to boundary bursts |
| **Smoothing** | Poor at window boundaries |
| **Memory Usage** | Very Low — just a counter + window timestamp |
| **Complexity** | Very Simple |

#### Pseudocode

```python
class FixedWindowCounter:
    def __init__(self, window_size, max_requests):
        self.window_size = window_size    # e.g., 60 seconds
        self.max_requests = max_requests  # e.g., 100
        self.counter = 0
        self.window_start = time.now()

    def allow_request(self):
        now = time.now()
        if now - self.window_start >= self.window_size:
            self.counter = 0              # Reset counter
            self.window_start = now
        if self.counter < self.max_requests:
            self.counter += 1
            return True   # ✅ Allowed
        return False      # ❌ Rate Limited
```

---

### 1.4 Sliding Window Log

#### 💡 Concept

The **Sliding Window Log** algorithm keeps a **log (list) of timestamps** for every request made by a client. When a new request arrives, timestamps **older than the window duration** are removed, and the remaining count is checked against the limit.

This approach provides **perfect accuracy** but at a **higher memory cost**.

#### How It Works (Step-by-Step)

1. Maintain a **sorted list of timestamps** for each client.
2. When a request arrives:
   - Remove all timestamps older than `(current_time - window_size)`.
   - Count the remaining timestamps.
   - If count **< limit** → add the new timestamp and allow.
   - If count **≥ limit** → reject (HTTP 429).

#### Characteristics

| Property | Detail |
|---|---|
| **Burst Handling** | ✅ Perfectly handles bursts — no boundary issue |
| **Smoothing** | Excellent — truly sliding window |
| **Memory Usage** | 🔴 High — stores every request timestamp |
| **Complexity** | Moderate |

#### Visual Diagram

```
Timeline:  ──────[──────────── 60 sec window ────────────]───→
                  ↑                                        ↑
            window_start                                  now

Stored Timestamps: [12:00:05, 12:00:12, 12:00:30, 12:00:45, 12:00:58]
                    ↑ These are all within the window → count = 5
```

#### Pseudocode

```python
class SlidingWindowLog:
    def __init__(self, window_size, max_requests):
        self.window_size = window_size
        self.max_requests = max_requests
        self.timestamps = []  # Sorted list of request timestamps

    def allow_request(self):
        now = time.now()
        cutoff = now - self.window_size

        # Remove expired timestamps
        self.timestamps = [t for t in self.timestamps if t > cutoff]

        if len(self.timestamps) < self.max_requests:
            self.timestamps.append(now)
            return True   # ✅ Allowed
        return False      # ❌ Rate Limited
```

---

### 1.5 Sliding Window Counter

#### 💡 Concept

The **Sliding Window Counter** is a **hybrid** of the Fixed Window Counter and the Sliding Window Log. It provides the accuracy benefits of a sliding window without the high memory cost of storing every timestamp.

It does this by using **two adjacent fixed windows** and **weighting** the previous window's count based on how much of it overlaps with the current sliding window.

#### How It Works (Step-by-Step)

1. Track the request count for the **current fixed window** and the **previous fixed window**.
2. When a request arrives, calculate a **weighted count**:
   ```
   weighted_count = (prev_window_count × overlap_percentage) + current_window_count
   ```
3. If `weighted_count < limit` → allow. Otherwise → reject.

#### Example Calculation

```
Window size: 60 seconds
Limit: 100 requests/min
Previous window (12:00 - 12:01): 84 requests
Current window  (12:01 - 12:02): 36 requests
Current time: 12:01:15 (we are 15 seconds into the current window)

Overlap of previous window = 1 - (15/60) = 0.75 (75%)

Weighted count = (84 × 0.75) + 36 = 63 + 36 = 99

99 < 100 → ✅ Request Allowed!
```

#### Characteristics

| Property | Detail |
|---|---|
| **Burst Handling** | ✅ Good — smooths out boundary bursts |
| **Smoothing** | Very Good — approximation of true sliding window |
| **Memory Usage** | Very Low — only 2 counters + timestamps |
| **Complexity** | Moderate |
| **Accuracy** | ~99.7% (according to Cloudflare experiments) |

#### Pseudocode

```python
class SlidingWindowCounter:
    def __init__(self, window_size, max_requests):
        self.window_size = window_size
        self.max_requests = max_requests
        self.prev_count = 0
        self.curr_count = 0
        self.curr_window_start = time.now()

    def allow_request(self):
        now = time.now()
        elapsed = now - self.curr_window_start

        if elapsed >= self.window_size:
            self.prev_count = self.curr_count
            self.curr_count = 0
            self.curr_window_start = now
            elapsed = 0

        overlap = 1 - (elapsed / self.window_size)
        weighted = (self.prev_count * overlap) + self.curr_count

        if weighted < self.max_requests:
            self.curr_count += 1
            return True   # ✅ Allowed
        return False      # ❌ Rate Limited
```

---

### 📊 Algorithm Comparison Summary

| Algorithm | Burst Tolerance | Accuracy | Memory | Complexity | Best For |
|---|---|---|---|---|---|
| **Token Bucket** | ✅ High | Good | Very Low | Simple | API Gateways, general use |
| **Leaky Bucket** | ❌ None | Good | Moderate | Simple | Traffic shaping, chat apps |
| **Fixed Window** | ⚠️ Boundary issue | Low | Very Low | Very Simple | Simple internal services |
| **Sliding Window Log** | ✅ Perfect | Perfect | 🔴 High | Moderate | When accuracy is critical |
| **Sliding Window Counter** | ✅ Good | ~99.7% | Very Low | Moderate | Production APIs (best balance) |

---

## 2. Essential System Components

### 2.1 Client Identifier

The **Client Identifier** is the unique key used to **identify and throttle** individual users or clients. It determines *who* is being rate-limited.

#### Common Identifier Types

| Identifier | Description | When to Use |
|---|---|---|
| **IP Address** | The client's network address (e.g., `192.168.1.1`) | Public APIs with anonymous access |
| **User ID** | The authenticated user's unique ID | Authenticated APIs (post-login) |
| **API Key** | A unique key assigned to each developer/application | Developer platforms, third-party integrations |
| **Session Token** | A session-specific token | Web applications with session management |
| **Composite Key** | Combination (e.g., `user_id + endpoint`) | Per-user, per-endpoint limits |

#### ⚠️ Considerations

- **IP-based limiting** can unfairly throttle users behind a shared NAT or proxy (e.g., an entire office).
- **User ID-based limiting** requires authentication and doesn't protect against pre-login abuse (e.g., brute-force login attempts).
- Best practice: Use a **combination** — IP-based for unauthenticated traffic, User ID for authenticated.

---

### 2.2 Rules / Policies

Rate limiting **rules** (or **policies**) define the specific thresholds for each type of client, endpoint, or service.

#### Where Rules Are Stored

| Storage | Pros | Cons |
|---|---|---|
| **Configuration File** (YAML/JSON) | Simple, version-controlled | Requires redeployment to change |
| **Database** (SQL/NoSQL) | Dynamic, changeable at runtime | Slightly more complex |
| **Environment Variables** | Easy for simple setups | Not scalable for many rules |

#### Example Rule Configuration (YAML)

```yaml
rate_limits:
  - name: "General API"
    client_type: "api_key"
    endpoint: "/api/*"
    limit: 100
    window: 60          # seconds
    action: "reject"    # or "throttle", "queue"

  - name: "Login Endpoint"
    client_type: "ip"
    endpoint: "/auth/login"
    limit: 5
    window: 300         # 5 minutes
    action: "reject"

  - name: "Premium User"
    client_type: "user_id"
    tier: "premium"
    endpoint: "/api/*"
    limit: 1000
    window: 60
    action: "throttle"
```

#### Rule Hierarchy

```
Global Limit (e.g., 10,000 req/min for the entire system)
  └── Per-Service Limit (e.g., 5,000 req/min for the user service)
       └── Per-Endpoint Limit (e.g., 100 req/min for /api/search)
            └── Per-User Limit (e.g., 50 req/min for free-tier users)
```

---

### 2.3 Storage (Redis)

**Redis** is the industry-standard storage for rate limiting because it's an **in-memory data store** that provides **sub-millisecond latency** and supports **atomic operations**.

#### Why Redis?

| Feature | Benefit for Rate Limiting |
|---|---|
| **In-Memory** | Extremely fast reads/writes (< 1ms) |
| **TTL (Time-to-Live)** | Keys auto-expire — perfect for time windows |
| **Atomic Operations** | `INCR`, `DECR` are atomic — prevents race conditions |
| **Lua Scripting** | Execute multiple commands atomically as a single unit |
| **Clustering** | Supports distributed setups for high availability |

#### Redis Commands for Rate Limiting

```redis
# Fixed Window Counter approach
INCR   user:123:rate_limit       # Increment counter atomically
EXPIRE user:123:rate_limit 60    # Set TTL to 60 seconds
GET    user:123:rate_limit       # Check current count
```

#### Lua Script for Atomic Rate Limiting

Using Lua scripts in Redis ensures that the **check-and-increment** operation happens as a **single atomic unit**, preventing race conditions.

```lua
-- rate_limiter.lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = tonumber(redis.call('GET', key) or "0")

if current < limit then
    redis.call('INCR', key)
    if current == 0 then
        redis.call('EXPIRE', key, window)
    end
    return 1  -- Allowed
else
    return 0  -- Rate Limited
end
```

#### Redis Data Structures for Each Algorithm

| Algorithm | Redis Data Structure |
|---|---|
| Token Bucket | `String` (token count) + `String` (last refill time) |
| Leaky Bucket | `List` (queue of requests) |
| Fixed Window | `String` with `INCR` + `EXPIRE` |
| Sliding Window Log | `Sorted Set` (timestamps as scores) |
| Sliding Window Counter | Two `String` counters |

---

## 3. Key Performance & Technical Metrics

### 3.1 High Availability

#### 💡 Concept

A rate limiter must **not become a single point of failure**. If the rate limiter goes down, the entire API could either become:
- **Unprotected** (all requests pass through) — risky for abuse, or
- **Completely blocked** (no requests pass) — catastrophic for business.

#### Strategies for High Availability

| Strategy | Description |
|---|---|
| **Redis Cluster / Sentinel** | Deploy Redis in a clustered or sentinel mode for automatic failover |
| **Local In-Memory Fallback** | If Redis is unreachable, use a local in-memory counter as a temporary fallback |
| **Fail-Open Policy** | If the rate limiter is down, **allow all requests** (favors availability over strictness) |
| **Multi-Region Replication** | Replicate rate limit data across regions for global services |

#### CAP Theorem Trade-off

In distributed rate limiting, there is a trade-off between **Consistency** and **Availability**:

```
         Consistency ←————→ Availability
              ↑                    ↑
     Strict enforcement     Never blocks
     (may reject valid      (may allow some
      requests)              excess requests)
```

**Industry standard**: Most systems favor **Availability** — it's better to let a few extra requests through than to block legitimate users.

---

### 3.2 Latency

#### 💡 Concept

The rate limiter sits in the **critical path** of every request. Its check-and-update operation must be **extremely fast** — ideally under **1 millisecond** — to avoid adding noticeable delay to the user experience.

#### Latency Targets

| Component | Target Latency |
|---|---|
| Redis `INCR` operation | < 0.5ms |
| Lua script execution | < 1ms |
| Full rate-limit check (including network hop to Redis) | < 5ms |
| End-to-end impact on API response | < 200ms total |

#### How to Minimize Latency

1. **Use Redis locally** — co-locate Redis with the application server.
2. **Use connection pooling** — avoid creating new Redis connections per request.
3. **Use pipelining** — batch multiple Redis commands into a single round trip.
4. **Use Lua scripts** — reduce multiple round trips to a single atomic call.
5. **Use local caching** — cache rate limit rules locally to avoid extra lookups.

---

### 3.3 Race Condition

#### 💡 Concept

A **race condition** occurs when multiple concurrent requests try to **read and update** the rate limit counter simultaneously, potentially allowing more requests than the limit.

#### The Problem

```
Thread A: READ counter → 99    (limit is 100)
Thread B: READ counter → 99    (sees same value!)
Thread A: WRITE counter → 100  (allows request)
Thread B: WRITE counter → 100  (also allows request!)

→ Both threads think they are request #100, but 101 requests went through!
```

#### Solutions

| Solution | How It Works |
|---|---|
| **Redis `INCR`** | Atomic increment — reads and writes in a single operation |
| **Lua Scripts** | Multiple Redis commands execute atomically |
| **Redis `WATCH` + `MULTI`** | Optimistic locking — transaction aborts if key changes |
| **Distributed Locks (Redlock)** | Acquire a lock before updating — slower but strict |

#### Atomic Solution with Redis

```redis
-- This is atomic — no race condition possible
MULTI
  INCR user:123:counter
  EXPIRE user:123:counter 60
EXEC
```

---

### 3.4 HTTP 429 (Too Many Requests)

#### 💡 Concept

**HTTP 429** is the standard HTTP status code returned when a client has sent **too many requests** in a given time period.

#### Response Format

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1708012800

{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded. Please retry after 30 seconds.",
    "retry_after": 30
  }
}
```

#### Best Practices for 429 Responses

1. **Always include `Retry-After` header** — tells the client exactly when to retry.
2. **Include a meaningful error message** — help developers understand the limit.
3. **Include rate limit headers** — so clients can self-regulate.
4. **Use exponential backoff** — recommend clients increase wait time with each retry.

---

## 4. HTTP Headers for Rate Limiting

These HTTP headers are included in **every API response** to inform clients about their current rate limit status.

### Header Definitions

#### `X-RateLimit-Limit`

> Defines the **maximum number of requests** allowed in the current time window.

```http
X-RateLimit-Limit: 100
```

This tells the client: *"You are allowed a maximum of 100 requests in this window."*

#### `X-RateLimit-Remaining`

> Shows the **number of requests the client has left** in the current time window.

```http
X-RateLimit-Remaining: 73
```

This tells the client: *"You have 73 requests remaining before you are rate limited."*

#### `X-RateLimit-Reset`

> Indicates the **Unix timestamp** (seconds since epoch) when the current rate limit window **resets**.

```http
X-RateLimit-Reset: 1708012860
```

This tells the client: *"Your rate limit will reset at this Unix timestamp. Convert it to know the exact time."*

### Complete Example

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 1708012860

{
  "data": { ... }
}
```

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1708012860
Retry-After: 45

{
  "error": "Rate limit exceeded. Try again in 45 seconds."
}
```

### Header Usage Flow

```
Client sends request
       │
       ▼
┌──────────────┐     ┌──────────────────────────────────┐
│ Rate Limiter │────▶│ Check: Remaining > 0?            │
└──────────────┘     └────────────┬─────────────────────┘
                           │              │
                        YES ✅          NO ❌
                           │              │
                    ┌──────▼──────┐  ┌────▼──────────────┐
                    │ 200 OK      │  │ 429 Too Many      │
                    │ Remaining:73│  │ Remaining: 0      │
                    │ Limit: 100  │  │ Retry-After: 45   │
                    └─────────────┘  └───────────────────┘
```

---

## 5. Design a Rate Limiter for Real-Life Problems

### 5.1 E-Commerce Flash Sale API

#### 📋 Problem Statement

During a **flash sale** (e.g., on Amazon, Flipkart), millions of users try to purchase a limited-inventory product simultaneously. Without rate limiting:
- The server can crash due to overwhelming traffic.
- Bots can buy all the stock before real users.
- Payment services can get overloaded.

#### 🎯 Requirements

| Requirement | Value |
|---|---|
| **Endpoint** | `POST /api/flash-sale/purchase` |
| **Limit** | 5 purchase attempts per user per minute |
| **Bot Protection** | Max 2 requests per second per IP |
| **Global Limit** | 50,000 requests/second for the entire endpoint |
| **Identifier** | User ID (authenticated) + IP (unauthenticated) |

#### 🏗️ Architecture

```
                    ┌───────────────┐
   Users ──────────▶│  Load Balancer │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ API GW 1 │  │ API GW 2 │  │ API GW 3 │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                   ┌─────────────────┐
                   │  Redis Cluster   │
                   │  (Rate Limiter)  │
                   │                  │
                   │  Layer 1: IP     │
                   │  Layer 2: UserID │
                   │  Layer 3: Global │
                   └────────┬────────┘
                            │
                     ┌──────▼──────┐
                     │ Purchase    │
                     │ Service     │
                     └─────────────┘
```

#### Algorithm Choice: **Token Bucket**

- **Why?** Flash sales have massive bursts. Token Bucket allows users to burst up to their limit while enforcing a refill rate.

#### Multi-Layer Rate Limiting

```
Layer 1 — Per-IP Limit (Bot Protection)
  └── 2 requests/second per IP
  └── Algorithm: Token Bucket (capacity=2, refill=2/sec)

Layer 2 — Per-User Limit (Fair Access)
  └── 5 purchase attempts per minute per user
  └── Algorithm: Sliding Window Counter

Layer 3 — Global Endpoint Limit (Server Protection)
  └── 50,000 requests/second total
  └── Algorithm: Token Bucket (capacity=50000, refill=50000/sec)
```

#### Redis Implementation

```lua
-- flash_sale_limiter.lua
-- Layer 1: IP-based (bot protection)
local ip_key = "ratelimit:ip:" .. KEYS[1]
local ip_count = tonumber(redis.call('GET', ip_key) or "0")
if ip_count >= 2 then
    return {0, "IP rate limit exceeded"}
end

-- Layer 2: User-based (fair access)
local user_key = "ratelimit:user:" .. KEYS[2]
local user_count = tonumber(redis.call('GET', user_key) or "0")
if user_count >= 5 then
    return {0, "User rate limit exceeded"}
end

-- Layer 3: Global limit (server protection)
local global_key = "ratelimit:global:flash_sale"
local global_count = tonumber(redis.call('GET', global_key) or "0")
if global_count >= 50000 then
    return {0, "Global rate limit exceeded"}
end

-- All checks passed — increment all counters
redis.call('INCR', ip_key)
redis.call('EXPIRE', ip_key, 1)     -- 1 second window
redis.call('INCR', user_key)
redis.call('EXPIRE', user_key, 60)  -- 1 minute window
redis.call('INCR', global_key)
redis.call('EXPIRE', global_key, 1) -- 1 second window

return {1, "Request allowed"}
```

#### Response Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1708013400

{"status": "Purchase successful", "order_id": "ORD-12345"}
```

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1708013400
Retry-After: 45

{"error": "Too many purchase attempts. Please wait 45 seconds."}
```

---

### 5.2 Social Media Post/Comment Spam Prevention

#### 📋 Problem Statement

On platforms like **Twitter/X, Instagram, or Reddit**, users (or bots) may try to:
- Post hundreds of comments per minute to spam.
- Create multiple posts to flood feeds.
- Send excessive direct messages.

Without rate limiting, the platform becomes unusable due to spam.

#### 🎯 Requirements

| Requirement | Value |
|---|---|
| **Post Creation** | Max 10 posts per hour per user |
| **Comments** | Max 30 comments per 15 minutes per user |
| **Direct Messages** | Max 50 DMs per hour per user |
| **New Account Restriction** | Accounts < 24 hours old: 50% of normal limits |
| **Identifier** | User ID (primary) + IP (secondary for anonymous actions) |

#### 🏗️ Architecture

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
   │ │ Rule Engine  ││ ← Loads rules from config/DB
   │ └──────┬──────┘│
   │        │       │
   │ ┌──────▼──────┐│
   │ │ Redis Check  ││ ← Sliding Window Counter
   │ └──────┬──────┘│
   └────────┼───────┘
            │
     ┌───────▼───────┐
     │ Application  │
     │ Server       │
     └──────┬───────┘
            │
     ┌───────▼───────┐
     │  Database    │
     │  (Posts, DMs) │
     └─────────────┘
```

#### Algorithm Choice: **Sliding Window Counter**

- **Why?** Social media needs smooth enforcement without the boundary burst problem (a spammer posting 10 times at minute 59 and 10 more at minute 0).

#### Rule Configuration

```yaml
rate_limits:
  post_creation:
    limit: 10
    window: 3600           # 1 hour
    new_account_limit: 5   # 50% for new accounts
    algorithm: "sliding_window_counter"

  comment_creation:
    limit: 30
    window: 900            # 15 minutes
    new_account_limit: 15
    algorithm: "sliding_window_counter"

  direct_message:
    limit: 50
    window: 3600           # 1 hour
    new_account_limit: 25
    algorithm: "sliding_window_counter"
```

#### Middleware Implementation (Node.js)

```javascript
const Redis = require('ioredis');
const redis = new Redis.Cluster([/* cluster nodes */]);

async function rateLimitMiddleware(req, res, next) {
    const userId = req.user.id;
    const action = req.route.action; // 'post', 'comment', or 'dm'
    const rules = await getRules(action);

    // Adjust limit for new accounts
    const accountAge = Date.now() - req.user.created_at;
    const isNewAccount = accountAge < 24 * 60 * 60 * 1000; // < 24 hours
    const limit = isNewAccount ? rules.new_account_limit : rules.limit;

    const key = `ratelimit:${action}:${userId}`;
    const windowStart = Math.floor(Date.now() / 1000 / rules.window) * rules.window;
    const prevKey = `${key}:${windowStart - rules.window}`;
    const currKey = `${key}:${windowStart}`;

    const [prevCount, currCount] = await redis.pipeline()
        .get(prevKey)
        .get(currKey)
        .exec();

    const elapsed = (Date.now() / 1000) - windowStart;
    const overlap = 1 - (elapsed / rules.window);
    const weighted = ((parseInt(prevCount?.[1]) || 0) * overlap)
                   + (parseInt(currCount?.[1]) || 0);

    if (weighted >= limit) {
        const resetTime = windowStart + rules.window;
        res.set({
            'X-RateLimit-Limit': limit,
            'X-RateLimit-Remaining': 0,
            'X-RateLimit-Reset': resetTime,
            'Retry-After': Math.ceil(resetTime - Date.now() / 1000)
        });
        return res.status(429).json({
            error: `Too many ${action}s. Please slow down.`
        });
    }

    // Increment current window
    await redis.pipeline()
        .incr(currKey)
        .expire(currKey, rules.window * 2)
        .exec();

    res.set({
        'X-RateLimit-Limit': limit,
        'X-RateLimit-Remaining': Math.max(0, Math.floor(limit - weighted - 1)),
        'X-RateLimit-Reset': windowStart + rules.window
    });

    next();
}
```

---

### 5.3 Banking / Payment Gateway Transaction Limiter

#### 📋 Problem Statement

In a **banking or payment gateway** system (e.g., Stripe, Razorpay, PayPal), rate limiting is **critical for security**:
- Prevent **brute-force attacks** on card validation (card stuffing).
- Limit **fraudulent transaction attempts**.
- Protect downstream payment processors from overload.
- Comply with **regulatory requirements** (PCI-DSS).

#### 🎯 Requirements

| Requirement | Value |
|---|---|
| **Card Validation** | Max 3 attempts per card per 10 minutes |
| **Transactions per User** | Max 20 transactions per hour |
| **Transactions per Merchant** | Max 1,000 transactions per minute |
| **Global System Limit** | Max 100,000 transactions per minute |
| **Failed Transaction Lockout** | After 5 consecutive failures → lock for 30 minutes |
| **Identifier** | Card hash, User ID, Merchant ID |

#### 🏗️ Architecture

```
  Client (Web/Mobile/POS)
           │
           ▼
   ┌───────────────┐
   │   API Gateway  │
   │   (TLS/mTLS)   │
   └───────┬───────┘
           │
   ┌───────▼───────────────────────────┐
   │        Rate Limiter Service        │
   │                                    │
   │  ┌────────────┐  ┌──────────────┐ │
   │  │ Layer 1:   │  │ Layer 2:     │ │
   │  │ Card Hash  │  │ User ID      │ │
   │  │ 3/10min    │  │ 20/hour      │ │
   │  └────────────┘  └──────────────┘ │
   │                                    │
   │  ┌────────────┐  ┌──────────────┐ │
   │  │ Layer 3:   │  │ Layer 4:     │ │
   │  │ Merchant   │  │ Global       │ │
   │  │ 1000/min   │  │ 100K/min     │ │
   │  └────────────┘  └──────────────┘ │
   │                                    │
   │  ┌────────────────────────────┐   │
   │  │ Layer 5: Failure Lockout   │   │
   │  │ 5 consecutive fails →     │   │
   │  │ 30-min lock               │   │
   │  └────────────────────────────┘   │
   └──────────────┬────────────────────┘
                  │
          ┌───────▼───────┐
          │ Redis Cluster  │
          │ (Primary +     │
          │  Replicas)     │
          └───────┬───────┘
                  │
          ┌───────▼───────┐
          │ Payment        │
          │ Processor      │
          │ (Visa/MC/etc.) │
          └───────────────┘
```

#### Algorithm Choice: **Sliding Window Log** (for card validation) + **Token Bucket** (for throughput)

- **Why Sliding Window Log for card validation?** We need **perfect accuracy** — even one extra fraudulent attempt is unacceptable for financial systems. The higher memory cost is justified for security.
- **Why Token Bucket for throughput?** Merchants and the global system need to handle traffic bursts while maintaining an overall rate.

#### Multi-Layer Redis Implementation

```lua
-- banking_rate_limiter.lua
local card_hash = KEYS[1]
local user_id = KEYS[2]
local merchant_id = KEYS[3]
local now = tonumber(ARGV[1])

-- ============ Layer 5: Failure Lockout Check ============
local lockout_key = "lockout:" .. card_hash
local is_locked = redis.call('GET', lockout_key)
if is_locked then
    local ttl = redis.call('TTL', lockout_key)
    return {0, "LOCKED", ttl}
end

-- ============ Layer 1: Card Validation (Sliding Window Log) ==========
local card_key = "ratelimit:card:" .. card_hash
-- Remove entries older than 10 minutes (600 seconds)
redis.call('ZREMRANGEBYSCORE', card_key, 0, now - 600)
local card_count = redis.call('ZCARD', card_key)
if card_count >= 3 then
    return {0, "Card rate limit exceeded (3/10min)", 0}
end

-- ============ Layer 2: User Transaction Limit ==========
local user_key = "ratelimit:user_txn:" .. user_id
redis.call('ZREMRANGEBYSCORE', user_key, 0, now - 3600)
local user_count = redis.call('ZCARD', user_key)
if user_count >= 20 then
    return {0, "User transaction limit exceeded (20/hour)", 0}
end

-- ============ Layer 3: Merchant Limit ==========
local merchant_key = "ratelimit:merchant:" .. merchant_id
local merchant_count = tonumber(redis.call('GET', merchant_key) or "0")
if merchant_count >= 1000 then
    return {0, "Merchant limit exceeded (1000/min)", 0}
end

-- ============ Layer 4: Global Limit ==========
local global_key = "ratelimit:global:transactions"
local global_count = tonumber(redis.call('GET', global_key) or "0")
if global_count >= 100000 then
    return {0, "Global transaction limit exceeded", 0}
end

-- ============ All Checks Passed — Record Transaction ==========
redis.call('ZADD', card_key, now, now .. ":" .. math.random())
redis.call('EXPIRE', card_key, 600)

redis.call('ZADD', user_key, now, now .. ":" .. math.random())
redis.call('EXPIRE', user_key, 3600)

redis.call('INCR', merchant_key)
redis.call('EXPIRE', merchant_key, 60)

redis.call('INCR', global_key)
redis.call('EXPIRE', global_key, 60)

return {1, "Transaction allowed", 0}
```

#### Failure Lockout Logic

```python
def handle_transaction_result(card_hash, success):
    fail_key = f"failures:{card_hash}"

    if success:
        redis.delete(fail_key)  # Reset on success
    else:
        failures = redis.incr(fail_key)
        redis.expire(fail_key, 600)  # Track failures for 10 min

        if failures >= 5:
            # Lock the card for 30 minutes
            redis.setex(f"lockout:{card_hash}", 1800, "locked")
            redis.delete(fail_key)
            alert_fraud_team(card_hash)  # Trigger fraud alert
```

#### Security-Specific Response

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 3
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1708013400

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many card validation attempts. Please try again later.",
    "retry_after": 600
  }
}
```

> ⚠️ **Security Note**: Never reveal *which* specific limit was hit in production — attackers could use this information to probe the system. Use a generic message.

---

### 📊 Real-Life Design Comparison

| Aspect | Flash Sale | Social Media | Banking |
|---|---|---|---|
| **Primary Goal** | Handle traffic spikes | Prevent spam | Security & fraud prevention |
| **Strictness** | Moderate | Moderate | Very Strict |
| **Algorithm** | Token Bucket | Sliding Window Counter | Sliding Window Log + Token Bucket |
| **Layers** | 3 (IP, User, Global) | 2 (User, Action) | 5 (Card, User, Merchant, Global, Lockout) |
| **Failure Strategy** | Fail-open | Fail-open | Fail-closed (deny if unsure) |
| **Latency Tolerance** | < 10ms | < 5ms | < 2ms |
| **Consistency** | Eventual OK | Eventual OK | Strong consistency required |

---

## 📖 References & Further Reading

- [RFC 6585 — HTTP 429 Status Code](https://tools.ietf.org/html/rfc6585)
- [Redis Documentation — Rate Limiting Pattern](https://redis.io/glossary/rate-limiting)
- [Stripe — Rate Limiting Best Practices](https://stripe.com/docs/rate-limits)
- [Cloudflare — How We Built Rate Limiting](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)
- [System Design Primer — Rate Limiter](https://github.com/donnemartin/system-design-primer)

---

> **Author**: Priyanshu Paikra  
> **Last Updated**: 2026-02-15  
> **License**: MIT