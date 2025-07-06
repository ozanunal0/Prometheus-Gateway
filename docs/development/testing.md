# Testing Guide

Comprehensive testing strategy for Prometheus Gateway including unit tests, integration tests, and end-to-end testing.

## Overview

Our testing strategy covers:
- **Unit Tests**: Individual components and functions
- **Integration Tests**: Multi-component interactions
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability scanning

## Test Structure

```
tests/
├── unit/                          # Unit tests
│   ├── test_openai_provider.py     # OpenAI provider tests
│   ├── test_google_provider.py     # Google provider tests
│   ├── test_anthropic_provider.py  # Anthropic provider tests
│   ├── test_routing_engine.py      # Routing logic tests
│   └── test_dlp_functionality.py   # DLP scanning tests
├── integration/                   # Integration tests
│   ├── test_caching_systems.py    # Cache system tests
│   ├── test_end_to_end.py         # Complete workflows
│   └── test_provider_integration.py # Provider integration
├── performance/                   # Performance tests
│   ├── test_load.py               # Load testing
│   └── test_stress.py             # Stress testing
├── security/                      # Security tests
│   ├── test_auth.py               # Authentication tests
│   └── test_vulnerabilities.py    # Security scanning
└── conftest.py                    # Test configuration
```

## Running Tests

### All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_openai_provider.py
```

### Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Performance tests
pytest tests/performance/

# Security tests
pytest tests/security/

# Tests by marker
pytest -m "unit"
pytest -m "integration"
pytest -m "slow"
pytest -m "provider"
```

### Parallel Testing

```bash
# Run tests in parallel
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

## Unit Tests

### Provider Tests

Testing individual provider implementations:

```python
@pytest.mark.unit
@pytest.mark.provider
class TestOpenAIProvider:
    """Test OpenAI provider functionality."""
    
    def test_provider_initialization(self):
        """Test provider initialization with API key."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.api_key == "test-key"
    
    @pytest.mark.asyncio
    async def test_create_completion_success(self, sample_chat_request):
        """Test successful completion creation."""
        provider = OpenAIProvider(api_key="test-key")
        
        with patch.object(provider, 'client') as mock_client:
            mock_response = create_mock_openai_response("Test response")
            mock_client.chat.completions.create.return_value = mock_response
            
            result = await provider.create_completion(sample_chat_request)
            
            assert_openai_compatible_response(result)
            assert result["choices"][0]["message"]["content"] == "Test response"
```

### Routing Engine Tests

Testing intelligent routing logic:

```python
@pytest.mark.unit
@pytest.mark.routing
class TestRoutingEngine:
    """Test routing engine functionality."""
    
    def test_get_provider_openai_models(self, test_config):
        """Test routing for OpenAI models."""
        with patch('app.services.config', test_config):
            for model in ["gpt-4o", "gpt-3.5-turbo"]:
                provider = get_provider(model)
                assert isinstance(provider, OpenAIProvider)
    
    def test_get_provider_unsupported_model(self, test_config):
        """Test error handling for unsupported models."""
        with patch('app.services.config', test_config):
            with pytest.raises(ValueError) as exc_info:
                get_provider("unsupported-model")
            assert "No provider found" in str(exc_info.value)
```

### DLP Tests

Testing data loss prevention:

```python
@pytest.mark.unit
@pytest.mark.dlp
class TestDLPScanner:
    """Test DLP scanning functionality."""
    
    def test_scan_and_anonymize_email_addresses(self):
        """Test email detection and anonymization."""
        text = "Contact john.doe@example.com for info"
        result = scan_and_anonymize_text(text)
        
        assert "[EMAIL_ADDRESS]" in result
        assert "john.doe@example.com" not in result
    
    def test_scan_and_anonymize_multiple_pii_types(self):
        """Test multiple PII type detection."""
        text = "Email: john@example.com, Phone: (555) 123-4567, SSN: 123-45-6789"
        result = scan_and_anonymize_text(text)
        
        assert "[EMAIL_ADDRESS]" in result
        assert "[PHONE_NUMBER]" in result
        assert "[US_SSN]" in result
```

## Integration Tests

### Cache System Tests

Testing two-level caching:

```python
@pytest.mark.integration
@pytest.mark.asyncio
class TestTwoLevelCaching:
    """Test complete caching system."""
    
    async def test_exact_cache_hit_flow(self, sample_request, mock_response):
        """Test exact cache hit bypasses providers."""
        with patch('app.cache.get_from_cache', return_value=mock_response):
            result = await process_chat_completion(sample_request)
            assert result == mock_response
    
    async def test_semantic_cache_hit_flow(self, sample_request):
        """Test semantic cache hit after exact cache miss."""
        with patch('app.cache.get_from_cache', side_effect=[None, mock_response]):
            with patch('app.vector_cache.search_semantic_cache', return_value="cache_key"):
                result = await process_chat_completion(sample_request)
                assert result == mock_response
```

### End-to-End Tests

Testing complete workflows:

```python
@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end workflow tests."""
    
    @pytest.mark.asyncio
    async def test_complete_chat_workflow(self, client, valid_api_key):
        """Test complete chat completion workflow."""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50
            },
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert data["choices"][0]["message"]["content"]
```

## Performance Tests

### Load Testing

```python
@pytest.mark.performance
@pytest.mark.slow
class TestLoadPerformance:
    """Load testing scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client, valid_api_key):
        """Test handling of concurrent requests."""
        async def make_request():
            return await client.post(
                "/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Test"}],
                    "max_tokens": 10
                },
                headers={"X-API-Key": valid_api_key}
            )
        
        # Send 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Check response times
        response_times = [r.elapsed.total_seconds() for r in responses]
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 5.0  # Average under 5 seconds
```

### Memory Testing

```python
@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage testing."""
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in long-running processes."""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Simulate heavy usage
        for i in range(1000):
            # Simulate request processing
            large_data = [{"content": "test" * 1000} for _ in range(100)]
            del large_data
            
            if i % 100 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable
        assert memory_growth < 100 * 1024 * 1024  # Less than 100MB growth
```

## Security Tests

### Authentication Tests

```python
@pytest.mark.security
class TestAuthentication:
    """Security testing for authentication."""
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client):
        """Test rejection of invalid API keys."""
        response = await client.post(
            "/v1/chat/completions",
            json={"model": "gpt-3.5-turbo", "messages": []},
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401
        assert "invalid_api_key" in response.json()["error"]["code"]
    
    @pytest.mark.asyncio
    async def test_missing_api_key(self, client):
        """Test rejection of requests without API key."""
        response = await client.post(
            "/v1/chat/completions",
            json={"model": "gpt-3.5-turbo", "messages": []}
        )
        
        assert response.status_code == 401
```

### Vulnerability Tests

```python
@pytest.mark.security
class TestVulnerabilities:
    """Security vulnerability testing."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client, valid_api_key):
        """Test SQL injection protection."""
        malicious_input = "'; DROP TABLE users; --"
        
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": malicious_input}]
            },
            headers={"X-API-Key": valid_api_key}
        )
        
        # Should not crash or expose sensitive info
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_xss_protection(self, client, valid_api_key):
        """Test XSS protection."""
        xss_payload = "<script>alert('xss')</script>"
        
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": xss_payload}]
            },
            headers={"X-API-Key": valid_api_key}
        )
        
        # Should handle safely
        assert response.status_code == 200
        data = response.json()
        # Response should not contain executable script
        assert "<script>" not in str(data)
```

## Test Configuration

### Fixtures

```python
# conftest.py
@pytest.fixture
def sample_chat_request():
    """Sample chat completion request."""
    return ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "What is the weather like today?"}],
        max_tokens=100,
        temperature=0.7
    )

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('redis.Redis') as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def test_config():
    """Test configuration."""
    return Config(
        providers=[
            ProviderConfig(
                name="openai",
                api_key_env="TEST_OPENAI_API_KEY",
                models=["gpt-4o", "gpt-3.5-turbo"]
            ),
            ProviderConfig(
                name="google",
                api_key_env="TEST_GOOGLE_API_KEY",
                models=["gemini-2.5-flash", "gemini-2.5-pro"]
            )
        ]
    )
```

### Environment Setup

```python
# pytest.ini
[tool:pytest]
testpaths = tests
addopts = --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
    slow: Slow tests
    provider: Provider tests
    dlp: DLP tests
    routing: Routing tests
    redis: Redis tests
    vector: Vector cache tests
    e2e: End-to-end tests
asyncio_mode = auto
```

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Data Management

### Fixtures and Mocks

```python
# Test data for consistent testing
SAMPLE_RESPONSES = {
    "openai": {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
}

# Mock responses for different providers
def create_mock_openai_response(content: str) -> dict:
    """Create mock OpenAI response."""
    response = SAMPLE_RESPONSES["openai"].copy()
    response["choices"][0]["message"]["content"] = content
    return response
```

## Best Practices

### Test Organization

1. **Group related tests** in classes
2. **Use descriptive test names** that explain what's being tested
3. **Test one thing at a time** - focused assertions
4. **Use fixtures** for common test data
5. **Mock external dependencies** to avoid flaky tests

### Test Quality

1. **Test edge cases** and error conditions
2. **Verify both positive and negative scenarios**
3. **Test with realistic data** that matches production
4. **Include performance assertions** for critical paths
5. **Test security boundaries** and input validation

### Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: Critical paths covered
- **E2E Tests**: Main user workflows
- **Performance Tests**: Load and stress scenarios
- **Security Tests**: Authentication and input validation

## Running Tests Locally

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run quick unit tests
pytest tests/unit/

# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest -m "unit and not slow"
pytest -m "integration"
pytest -m "security"

# Run with test output
pytest -v -s

# Run failed tests only
pytest --lf

# Run tests in parallel
pytest -n auto
```

## Debugging Tests

```bash
# Run with debugger
pytest --pdb

# Run with extra output
pytest -vvs

# Run specific test with debugging
pytest -vvs tests/unit/test_openai_provider.py::TestOpenAIProvider::test_create_completion_success

# Profile test performance
pytest --profile
```

## Next Steps

- [Configuration Guide](../configuration/overview.md) - Configuration reference
- [API Reference](../api/endpoints.md) - API documentation
- [Troubleshooting](../troubleshooting.md) - Common issues and solutions