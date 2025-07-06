# Troubleshooting Guide

Common issues and solutions for Prometheus Gateway.

## 🔧 Installation Issues

### Python Version Errors

**Problem**: `python: command not found` or version conflicts
```bash
# Solution: Use specific Python version
python3.11 -m venv venv
# or
pyenv install 3.11.13 && pyenv local 3.11.13
```

### Dependency Installation Failures

**Problem**: `pip install` fails with compilation errors
```bash
# Solution: Update pip and use binary wheels
python -m pip install --upgrade pip setuptools wheel
pip install --only-binary=all -r requirements.txt
```

### spaCy Model Download Issues

**Problem**: `python -m spacy download en_core_web_lg` fails
```bash
# Solution: Manual download
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl
```

## 🚀 Runtime Issues

### Server Won't Start

**Problem**: `uvicorn` fails to start
```bash
# Check port availability
lsof -i :8000

# Kill existing processes
pkill -f uvicorn

# Start with different port
uvicorn app.main:app --port 8001
```

### API Key Errors

**Problem**: `Environment variable OPENAI_API_KEY not set`
```bash
# Solution: Set environment variables
export OPENAI_API_KEY=your-key-here
# or create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
```

### Database Issues

**Problem**: SQLite database errors
```bash
# Solution: Reset database
rm gateway.db
python -c "from app.database import create_db_and_tables; create_db_and_tables()"
```

## 🐳 Docker Issues

### Container Build Failures

**Problem**: Docker build fails
```bash
# Solution: Clean build
docker system prune -f
docker-compose build --no-cache
```

### Redis Connection Issues

**Problem**: Redis connection refused
```bash
# Check Redis status
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Permission Errors

**Problem**: File permission denied in containers
```bash
# Solution: Fix ownership
sudo chown -R $USER:$USER .
# or use Docker with user mapping
docker-compose run --user "$(id -u):$(id -g)" gateway
```

## 📊 Performance Issues

### High Memory Usage

**Problem**: Application uses too much RAM
```bash
# Monitor memory
docker stats

# Solution: Adjust container limits
# In docker-compose.yml:
services:
  gateway:
    mem_limit: 1G
    memswap_limit: 1G
```

### Slow Response Times

**Problem**: API responses are slow
```bash
# Check metrics
curl http://localhost:8000/metrics | grep duration

# Solutions:
# 1. Enable Redis caching
# 2. Optimize database queries
# 3. Scale horizontally
```

## 🔍 Testing Issues

### Tests Failing

**Problem**: `pytest` tests fail
```bash
# Solution: Check environment
source venv/bin/activate
pip install -r requirements-dev.txt

# Run specific test
pytest tests/unit/test_dlp_functionality.py -v

# Skip integration tests
pytest tests/unit/ -v
```

### Import Errors in Tests

**Problem**: `ModuleNotFoundError` in tests
```bash
# Solution: Install in development mode
pip install -e .

# or adjust PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 🌐 Network Issues

### External API Timeouts

**Problem**: Provider APIs timing out
```bash
# Check connectivity
curl -I https://api.openai.com/v1/models

# Solution: Configure timeouts in app/providers/
```

### Firewall/Proxy Issues

**Problem**: Blocked outbound connections
```bash
# Solution: Configure proxy
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=http://proxy:8080
```

## 📝 Logging and Debugging

### Enable Debug Logging

```python
# In app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Application Logs

```bash
# Docker logs
docker-compose logs -f gateway

# Local logs
tail -f server.log
```

### Monitor with Prometheus

```bash
# Check metrics
curl http://localhost:9090/api/v1/query?query=gateway_requests_total
```

## 🆘 Getting Help

### Gather Debug Information

```bash
# System info
python --version
docker --version
pip list | grep -E "(fastapi|uvicorn|redis)"

# Check configuration
cat config.yaml
env | grep -E "(OPENAI|GOOGLE|ANTHROPIC)_API_KEY"
```

### Report Issues

When reporting issues, include:

1. **Environment**: OS, Python version, Docker version
2. **Error message**: Full traceback
3. **Steps to reproduce**: Exact commands used
4. **Configuration**: Sanitized config files
5. **Logs**: Relevant log excerpts

### Community Resources

- 📖 [Documentation](https://ozanunal0.github.io/prometheus-gateway)
- 🐛 [Issue Tracker](https://github.com/ozanunal0/prometheus-gateway/issues)
- 💬 [Discussions](https://github.com/ozanunal0/prometheus-gateway/discussions)

## 📋 Common Solutions Checklist

- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Environment variables set
- [ ] API keys valid and active
- [ ] Ports not conflicting
- [ ] Database initialized
- [ ] Redis running (if using Docker)
- [ ] Firewall/proxy configured
- [ ] Sufficient disk space and memory