# Configuration Overview

Prometheus Gateway uses a flexible configuration system that supports both YAML files and environment variables.

## Configuration Files

### Main Configuration: `config.yaml`

The primary configuration file defines providers, models, and routing rules:

```yaml
providers:
  - name: "openai"
    api_key_env: "OPENAI_API_KEY"
    models:
      - "gpt-4o"
      - "gpt-3.5-turbo"
      - "gpt-4-turbo"
      - "gpt-4"
  
  - name: "google"
    api_key_env: "GOOGLE_API_KEY"
    models:
      - "gemini-2.5-flash"
      - "gemini-2.5-pro"
      - "gemini-1.5-pro"
  
  - name: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      - "claude-sonnet-4-20250514"
      - "claude-opus-4-20250514"
      - "claude-haiku-4-20250514"
```

### Docker Compose: `docker-compose.yml`

Service orchestration and dependencies:

```yaml
version: '3.8'
services:
  gateway:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - gateway
    
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus

volumes:
  redis_data:
```

## Environment Variables

### Required Variables

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-...                    # OpenAI API key
GOOGLE_API_KEY=AI...                     # Google AI Studio API key
ANTHROPIC_API_KEY=sk-ant-...             # Anthropic API key
```

### Optional Variables

```bash
# Redis Configuration
REDIS_HOST=localhost                     # Redis hostname
REDIS_PORT=6379                         # Redis port
REDIS_PASSWORD=your-password            # Redis password (optional)
REDIS_DB=0                              # Redis database number

# Caching Configuration
CACHE_TTL=3600                          # Cache TTL in seconds
SEMANTIC_CACHE_THRESHOLD=0.95           # Semantic similarity threshold
SEMANTIC_CACHE_ENABLED=true             # Enable semantic caching

# Rate Limiting
RATE_LIMIT_REQUESTS=10                  # Requests per minute per API key
RATE_LIMIT_WINDOW=60                    # Rate limit window in seconds

# DLP Configuration
DLP_ENABLED=true                        # Enable DLP scanning
DLP_CONFIDENCE_THRESHOLD=0.8            # PII detection confidence threshold

# Monitoring
PROMETHEUS_METRICS_ENABLED=true         # Enable Prometheus metrics
METRICS_PORT=8000                       # Metrics endpoint port

# Logging
LOG_LEVEL=INFO                          # Logging level
LOG_FORMAT=json                         # Log format (json|text)

# Development
DEBUG=false                             # Enable debug mode
RELOAD=false                            # Auto-reload on code changes
```

## Configuration Validation

The configuration is validated using Pydantic models:

```python
from pydantic import BaseModel, Field
from typing import List

class ProviderConfig(BaseModel):
    name: str = Field(..., description="Provider name")
    api_key_env: str = Field(..., description="Environment variable name for API key")
    models: List[str] = Field(..., description="List of supported models")

class Config(BaseModel):
    providers: List[ProviderConfig] = Field(..., description="List of provider configurations")
```

## Runtime Configuration

### Adding New Providers

To add a new provider:

1. **Update `config.yaml`**:
```yaml
providers:
  - name: "new_provider"
    api_key_env: "NEW_PROVIDER_API_KEY"
    models:
      - "new-model-1"
      - "new-model-2"
```

2. **Create provider implementation**:
```python
# app/providers/new_provider/provider.py
from app.providers.base import LLMProvider

class NewProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def create_completion(self, request: ChatCompletionRequest) -> dict:
        # Implementation here
        pass
```

3. **Update factory in `app/services.py`**:
```python
def get_provider(model: str) -> LLMProvider:
    # Add new provider mapping
    if provider_config.name == "new_provider":
        return NewProvider(api_key=api_key)
```

### Dynamic Configuration Reload

The gateway supports configuration hot-reloading:

```bash
# Send SIGHUP to reload configuration
kill -HUP $(pgrep -f "python.*main.py")

# Or use the API endpoint
curl -X POST http://localhost:8000/admin/reload-config \
  -H "X-API-Key: your-admin-key"
```

## Configuration Best Practices

### Security

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys regularly**
4. **Use different keys** for different environments

### Performance

1. **Tune cache TTL** based on your use case
2. **Monitor cache hit rates** and adjust thresholds
3. **Configure appropriate rate limits**
4. **Use connection pooling** for database connections

### Monitoring

1. **Enable all metrics** in production
2. **Set up alerting** for key metrics
3. **Monitor resource usage** regularly
4. **Keep logs structured** for easy analysis

## Example Configurations

### Development
```yaml
# config.yaml
providers:
  - name: "openai"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo"]

# .env
OPENAI_API_KEY=sk-test-key
DEBUG=true
LOG_LEVEL=DEBUG
CACHE_TTL=300
```

### Production
```yaml
# config.yaml
providers:
  - name: "openai"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-4o", "gpt-3.5-turbo"]
  - name: "google"
    api_key_env: "GOOGLE_API_KEY"
    models: ["gemini-2.5-flash", "gemini-2.5-pro"]
  - name: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    models: ["claude-sonnet-4-20250514"]

# .env
OPENAI_API_KEY=sk-prod-key
GOOGLE_API_KEY=AI-prod-key
ANTHROPIC_API_KEY=sk-ant-prod-key
DEBUG=false
LOG_LEVEL=INFO
CACHE_TTL=3600
PROMETHEUS_METRICS_ENABLED=true
```

### High-Availability
```yaml
# docker-compose.yml
version: '3.8'
services:
  gateway:
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

## Next Steps

- [Provider Configuration](providers.md) - Detailed provider setup
- [Caching Configuration](caching.md) - Cache optimization
- [Security Configuration](security.md) - Security hardening
- [Monitoring Configuration](monitoring.md) - Observability setup