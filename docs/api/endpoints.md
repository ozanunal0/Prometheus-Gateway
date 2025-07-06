# API Endpoints

Prometheus Gateway provides OpenAI-compatible endpoints plus additional management and monitoring endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints require authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/v1/chat/completions
```

## Chat Completions

### `POST /v1/chat/completions`

Main endpoint for chat completions, compatible with OpenAI API.

**Request Format:**
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello, world!"}
  ],
  "max_tokens": 150,
  "temperature": 0.7,
  "top_p": 1.0,
  "n": 1,
  "stream": false,
  "stop": null
}
```

**Response Format:**
```json
{
  "id": "chatcmpl-1234567890",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  }
}
```

**Supported Models:**

| Provider | Models |
|----------|--------|
| OpenAI | `gpt-4o`, `gpt-3.5-turbo`, `gpt-4-turbo`, `gpt-4` |
| Google | `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-pro` |
| Anthropic | `claude-sonnet-4-20250514`, `claude-opus-4-20250514` |

**Example with curl:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "What is the capital of France?"}],
    "max_tokens": 50
  }'
```

**Example with Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key"
    },
    json={
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}],
        "max_tokens": 50
    }
)

print(response.json())
```

## Health and Status

### `GET /health`

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "redis": "connected",
    "database": "connected",
    "providers": {
      "openai": "available",
      "google": "available",
      "anthropic": "available"
    }
  },
  "version": "1.0.0"
}
```

### `GET /health/ready`

Kubernetes-style readiness probe.

**Response:**
```json
{
  "ready": true,
  "checks": {
    "redis": true,
    "database": true,
    "config": true
  }
}
```

### `GET /health/live`

Kubernetes-style liveness probe.

**Response:**
```json
{
  "alive": true,
  "uptime": 86400
}
```

## Metrics and Monitoring

### `GET /metrics`

Prometheus metrics endpoint.

**Response:**
```
# HELP gateway_requests_total Total number of requests
# TYPE gateway_requests_total counter
gateway_requests_total{method="POST",endpoint="/v1/chat/completions",status="200"} 42

# HELP gateway_request_duration_seconds Request duration in seconds
# TYPE gateway_request_duration_seconds histogram
gateway_request_duration_seconds_bucket{le="0.1"} 10
gateway_request_duration_seconds_bucket{le="0.5"} 25
gateway_request_duration_seconds_bucket{le="1.0"} 35
gateway_request_duration_seconds_bucket{le="+Inf"} 42

# HELP gateway_cache_hits_total Total number of cache hits
# TYPE gateway_cache_hits_total counter
gateway_cache_hits_total{cache_type="exact"} 120
gateway_cache_hits_total{cache_type="semantic"} 45

# HELP gateway_tokens_used_total Total number of tokens used
# TYPE gateway_tokens_used_total counter
gateway_tokens_used_total{provider="openai",model="gpt-3.5-turbo",type="prompt"} 5000
gateway_tokens_used_total{provider="openai",model="gpt-3.5-turbo",type="completion"} 3000
```

### `GET /stats`

Gateway statistics and analytics.

**Response:**
```json
{
  "total_requests": 1000,
  "cache_stats": {
    "exact_cache": {
      "hits": 120,
      "misses": 30,
      "hit_rate": 0.8
    },
    "semantic_cache": {
      "hits": 45,
      "misses": 105,
      "hit_rate": 0.3
    }
  },
  "provider_stats": {
    "openai": {
      "requests": 500,
      "tokens": 75000,
      "avg_latency": 0.8
    },
    "google": {
      "requests": 300,
      "tokens": 45000,
      "avg_latency": 0.6
    },
    "anthropic": {
      "requests": 200,
      "tokens": 30000,
      "avg_latency": 1.2
    }
  },
  "rate_limit_stats": {
    "requests_throttled": 25,
    "top_users": [
      {"api_key": "masked_key_1", "requests": 150},
      {"api_key": "masked_key_2", "requests": 120}
    ]
  }
}
```

## Management

### `POST /admin/reload-config`

Reload configuration without restarting the service.

**Headers:**
- `X-API-Key`: Admin API key

**Response:**
```json
{
  "status": "success",
  "message": "Configuration reloaded successfully",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### `GET /admin/cache/stats`

Detailed cache statistics.

**Response:**
```json
{
  "redis": {
    "connected": true,
    "memory_usage": "150MB",
    "keys": 1250,
    "hits": 850,
    "misses": 400,
    "evictions": 5
  },
  "semantic_cache": {
    "collection_size": 500,
    "index_size": "25MB",
    "queries": 150,
    "hits": 45,
    "avg_similarity": 0.87
  }
}
```

### `POST /admin/cache/clear`

Clear all caches.

**Request:**
```json
{
  "cache_type": "all"  // Options: "all", "exact", "semantic"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Cache cleared successfully",
  "cleared": {
    "exact_cache": 1250,
    "semantic_cache": 500
  }
}
```

## Error Responses

All endpoints return structured error responses:

```json
{
  "error": {
    "code": "invalid_api_key",
    "message": "Invalid API key provided",
    "type": "authentication_error"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_1234567890"
}
```

**Common Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_api_key` | 401 | Invalid or missing API key |
| `rate_limit_exceeded` | 429 | Rate limit exceeded |
| `model_not_found` | 400 | Unsupported model |
| `invalid_request` | 400 | Malformed request |
| `provider_error` | 502 | Upstream provider error |
| `internal_error` | 500 | Internal server error |

## Rate Limiting

Rate limiting is enforced per API key:

- **Default**: 10 requests per minute
- **Headers**: Rate limit info in response headers
- **Retry**: Use exponential backoff when rate limited

**Rate Limit Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1677652348
```

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Client Libraries

### Python

```python
# Using OpenAI client (compatible)
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Node.js

```javascript
// Using OpenAI SDK
const OpenAI = require('openai');

const openai = new OpenAI({
  apiKey: 'your-api-key',
  baseURL: 'http://localhost:8000/v1'
});

const response = await openai.chat.completions.create({
  model: 'gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Hello!' }]
});
```

### cURL

```bash
# Basic request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# With streaming
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

## Next Steps

- [Request Format](requests.md) - Detailed request specifications
- [Response Format](responses.md) - Response structure details
- [Error Handling](errors.md) - Error codes and handling