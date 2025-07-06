# Quick Start Guide

Get up and running with Prometheus Gateway in just a few minutes!

## 🚀 1-Minute Setup

### Option A: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/ozanunal0/prometheus-gateway.git
cd prometheus-gateway

# Set your API keys
export OPENAI_API_KEY=your-openai-key
export GOOGLE_API_KEY=your-google-key
export ANTHROPIC_API_KEY=your-anthropic-key

# Start all services
docker-compose up -d

# Create your first API key
python create_key.py your-email@example.com
```

### Option B: Local Development

```bash
# Clone and setup
git clone https://github.com/ozanunal0/prometheus-gateway.git
cd prometheus-gateway

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Set environment variables
export OPENAI_API_KEY=your-openai-key

# Run the server
uvicorn app.main:app --reload
```

## 🎯 First API Call

Once running, test with your first API call:

```bash
# Create API key (save the output!)
python create_key.py test-user@example.com

# Test API call
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "max_tokens": 50
  }'
```

## 📊 Access Services

- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)

## ✅ Verify Installation

```bash
# Check health
curl http://localhost:8000/metrics

# Run tests
pytest tests/unit/test_dlp_functionality.py -v
```

## 🔧 Configuration

Basic configuration in `config.yaml`:

```yaml
providers:
  - name: "openai"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo", "gpt-4"]
```

## 📚 Next Steps

- [Configuration Guide](../configuration/overview.md)
- [API Reference](../api/endpoints.md)
- [Features Overview](../features/providers.md)