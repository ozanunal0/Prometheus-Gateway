# Installation Guide

This guide will help you get Prometheus Gateway up and running in different environments.

## System Requirements

- **Python**: 3.9 or higher
- **Redis**: 6.0 or higher
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 1GB free space for dependencies and models

## Installation Methods

### 🐳 Docker (Recommended)

The easiest way to get started is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/yourusername/prometheus-gateway.git
cd prometheus-gateway

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f gateway
```

**Services included:**
- `gateway`: Main FastAPI application
- `redis`: Caching layer
- `prometheus`: Metrics collection
- `grafana`: Monitoring dashboard

### 🐍 Local Development

For development or customization:

```bash
# Clone the repository
git clone https://github.com/yourusername/prometheus-gateway.git
cd prometheus-gateway

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Download required spaCy model
python -m spacy download en_core_web_lg

# Start Redis (required)
redis-server

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 📦 Production Deployment

For production environments:

```bash
# Install with production dependencies
pip install -r requirements.txt

# Run with production ASGI server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required API Keys
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password  # Optional

# Optional: Pre-defined API Keys for testing
API_KEYS=key1,key2,key3
```

## API Key Setup

Generate your first API key:

```bash
# Create an API key
python create_key.py user@example.com

# Example output:
# API Key: gw_1234567890abcdef1234567890abcdef
# Owner: user@example.com
# Created: 2024-01-01T00:00:00Z
```

## Verification

Test your installation:

```bash
# Health check
curl http://localhost:8000/health

# Test chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "max_tokens": 50
  }'
```

## Access Services

Once running, you can access:

- **Gateway API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Troubleshooting

### Common Issues

**Redis Connection Error**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check Redis logs
redis-cli monitor
```

**spaCy Model Missing**
```bash
# Download the required model
python -m spacy download en_core_web_lg

# Verify installation
python -c "import spacy; nlp = spacy.load('en_core_web_lg'); print('Model loaded successfully')"
```

**Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Memory Issues**
```bash
# Check memory usage
free -h

# Increase swap space if needed
sudo fallocate -l 2G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Docker Issues

**Container Won't Start**
```bash
# Check Docker logs
docker-compose logs gateway

# Restart services
docker-compose restart

# Rebuild containers
docker-compose build --no-cache
```

**Permission Errors**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# On Linux, you might need to adjust SELinux
sudo setsebool -P httpd_can_network_connect 1
```

## Next Steps

1. [Quick Start Guide](quickstart.md) - Test your installation
2. [Configuration Guide](../configuration/overview.md) - Customize your setup
3. [API Reference](../api/endpoints.md) - Explore available endpoints