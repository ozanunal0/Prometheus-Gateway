# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Download required spaCy model for PII detection
python -m spacy download en_core_web_lg
```

### Running the Application
```bash
# Run with uvicorn (recommended for development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run with Docker Compose (full stack)
docker-compose up -d

# Run single service
docker-compose up gateway
```

### API Key Management
```bash
# Create new API key
python create_key.py <owner_name>

# Example
python create_key.py user@example.com
```

### Database Operations
```bash
# Initialize database (automatic on startup)
# Database file: gateway.db

# Manual database initialization in Python
python -c "from app.database import create_db_and_tables; create_db_and_tables()"
```

### Monitoring Stack
```bash
# Start full monitoring stack
docker-compose up -d

# Access services
# Gateway: http://localhost:8000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
# Redis: localhost:6379
```

## Architecture Overview

### Core Components

**LLM Gateway with Multi-Provider Architecture:**
- `app/main.py` - FastAPI application with comprehensive middleware stack
- `app/services/` - Core business logic and LLM provider implementations
- `app/providers/` - Abstract provider interface and concrete implementations
- `app/models/` - Pydantic models for request/response validation
- `app/middleware/` - Custom middleware for DLP, rate limiting, authentication

**Data Layer:**
- `app/database.py` - SQLModel database configuration and session management
- `app/db_models/` - Database models for API keys and other entities
- `app/crud/` - Database operations and API key management
- `gateway.db` - SQLite database file (auto-created)

**Security & Privacy:**
- `app/dlp/` - Data Loss Prevention system using Microsoft Presidio
- `app/security.py` - API key hashing and validation
- `app/dependencies.py` - FastAPI dependency injection for authentication
- `app/limiter.py` - Rate limiting configuration

**Monitoring & Observability:**
- `app/metrics.py` - Custom Prometheus metrics definitions
- `prometheus.yml` - Prometheus scraping configuration
- Custom metrics: request counts, latency histograms, token usage

### Key Architectural Patterns

**Provider Pattern:**
- Abstract `LLMProvider` base class in `app/providers/base.py`
- Concrete implementations like `OpenAIProvider` in `app/providers/openai.py`
- Factory pattern for dynamic provider selection based on model name
- Extensible for adding new LLM providers (Anthropic, Google, etc.)

**Cache-Aside Pattern:**
- Redis-based caching with deterministic cache key generation
- SHA-256 hashing of request parameters for consistent cache keys
- Automatic expiration (default 1 hour TTL)
- Fallback to API calls when cache misses occur

**Middleware Chain Architecture:**
```
Request → DLP Middleware → Rate Limiting → Authentication → Core Handler
```

**Comprehensive Monitoring:**
- Prometheus metrics with multi-dimensional labels (owner, model, status)
- Request latency histograms with custom buckets
- Token usage tracking (prompt, completion, total)
- Error rate monitoring and alerting

### Data Flow

**Request Processing:**
1. **DLP Middleware** - Scans and anonymizes PII in request messages
2. **Rate Limiting** - Enforces per-API-key rate limits (10/minute)
3. **Authentication** - Validates API key from X-API-Key header
4. **Cache Check** - Generates cache key and checks Redis
5. **Provider Selection** - Routes to appropriate LLM provider based on model
6. **Response Processing** - Caches successful responses and records metrics

**Cache Key Generation:**
- Deterministic SHA-256 hash of: model, messages, temperature, max_tokens, etc.
- Ensures consistent caching across identical requests
- Includes request parameters that affect response generation

### Environment Configuration

**Required Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `REDIS_HOST` - Redis server hostname (default: localhost)
- `REDIS_PORT` - Redis server port (default: 6379)
- `REDIS_PASSWORD` - Redis password (optional)

**Optional Configuration:**
- `API_KEYS` - Comma-separated list of valid API keys (for development)
- `REDIS_USE_FALLBACK` - Enable fallback to in-memory cache if Redis unavailable

### Database Schema

**API Keys Table:**
- `id` - Primary key (UUID)
- `owner` - API key owner identifier
- `key_hash` - SHA-256 hash of the API key
- `created_at` - Creation timestamp
- `last_used_at` - Last usage timestamp
- `is_active` - Active/inactive status

### Security Model

**API Key Security:**
- Keys are hashed using SHA-256 before storage
- Plaintext keys are never stored or logged
- Keys are generated using cryptographically secure random generation
- Keys are only displayed once during creation

**PII Protection:**
- Automatic detection of emails, phone numbers, SSNs, credit cards
- Presidio-based entity recognition with spaCy NLP model
- Replacement with readable placeholders (e.g., "[EMAIL_ADDRESS]")
- Transparent processing without API changes

### Monitoring & Metrics

**Custom Prometheus Metrics:**
- `gateway_requests_total` - Counter with labels: owner, model, status_code
- `gateway_request_duration_seconds` - Histogram with labels: owner, model
- `gateway_tokens_used_total` - Counter with labels: owner, model, token_type

**Metric Collection:**
- Request latency measured with try/finally blocks
- Token usage extracted from LLM provider responses
- Error rates tracked by status code and model
- All metrics labeled by API key owner and model name

### Development Workflow

**Docker Compose Services:**
- `gateway` - Main FastAPI application
- `redis` - Caching layer
- `prometheus` - Metrics collection
- `grafana` - Monitoring dashboard

**Service Dependencies:**
- Gateway depends on Redis
- Prometheus depends on Gateway
- Grafana depends on Prometheus

**Volume Mounts:**
- `./gateway.db:/code/gateway.db` - Database persistence
- `./prometheus.yml:/etc/prometheus/prometheus.yml` - Prometheus config

### Extension Points

**Adding New LLM Providers:**
1. Create new provider class inheriting from `LLMProvider`
2. Implement `chat_completions` method
3. Add model-to-provider mapping in factory
4. Update environment variables for API keys

**Adding New Metrics:**
1. Define metrics in `app/metrics.py`
2. Record metrics in appropriate request handlers
3. Update Prometheus configuration if needed
4. Create Grafana dashboards for visualization

**Extending DLP Capabilities:**
1. Add new entity types to Presidio configuration
2. Customize anonymization strategies
3. Add custom PII detection rules
4. Configure replacement patterns