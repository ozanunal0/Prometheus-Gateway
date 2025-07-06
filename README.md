# 🚀 Prometheus Gateway

> Enterprise-grade LLM API Gateway with built-in privacy protection, caching, and observability

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://docker.com)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?logo=redis&logoColor=white)](https://redis.io)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=Prometheus&logoColor=white)](https://prometheus.io)

## ✨ Features

- **🔒 Privacy First**: Automatic PII detection and anonymization using Microsoft Presidio
- **⚡ Smart Caching**: Redis-powered response caching to reduce API costs
- **📊 Full Observability**: Comprehensive Prometheus metrics + Grafana dashboards
- **🛡️ Enterprise Security**: API key authentication with rate limiting
- **🔌 Multi-Provider Ready**: Extensible architecture for multiple LLM providers
- **🚀 OpenAI Compatible**: Drop-in replacement for OpenAI API endpoints

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│     DLP      │───▶│Rate Limiter │───▶│    Auth     │
└─────────────┘    │  Middleware  │    │ Middleware  │    │ Middleware  │
                   └──────────────┘    └─────────────┘    └─────────────┘
                                                                    │
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Redis     │◀───│    Cache     │◀───│   Provider  │◀───│   Gateway   │
│   Cache     │    │    Layer     │    │   Factory   │    │   Handler   │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/prometheus-gateway.git
cd prometheus-gateway

# Set your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env

# Start all services
docker-compose up -d

# Create an API key
docker-compose exec gateway python create_key.py your@email.com
```

### Manual Setup

```bash
# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Run the gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🎯 Usage

```bash
# Make a request (OpenAI compatible)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

## 📊 Monitoring

Access your monitoring stack:

- **Gateway**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `REDIS_HOST` | Redis hostname | localhost |
| `REDIS_PORT` | Redis port | 6379 |
| `REDIS_PASSWORD` | Redis password | None |

## 🛡️ Privacy & Security

- **PII Detection**: Automatically detects and anonymizes emails, phone numbers, SSNs, credit cards
- **Secure API Keys**: SHA-256 hashed storage, never logged in plaintext
- **Rate Limiting**: Configurable per-key rate limits (default: 10/minute)
- **Request Isolation**: Each request is processed independently

## 📈 Metrics

Track your usage with built-in metrics:

- Request counts by owner, model, and status
- Response latency histograms
- Token usage tracking (prompt, completion, total)
- Error rates and performance insights

## 🔌 Extending

Add new LLM providers easily:

```python
from app.providers.base import LLMProvider

class YourProvider(LLMProvider):
    async def chat_completions(self, request):
        # Your implementation
        pass
```

## 🤝 Contributing

This project is in active development. Contributions are welcome!

## 📄 License

MIT License - feel free to use this in your projects.

---

<div align="center">
  <sub>Built with ❤️ for the LLM community</sub>
</div>