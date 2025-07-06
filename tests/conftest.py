"""
Test fixtures and configuration for pytest.

This module provides common fixtures and test utilities used across
unit and integration tests for the Prometheus Gateway.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Generator
import os
import tempfile
import fakeredis
import json

# Import application modules
from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider
from app.config import Config, ProviderConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_chat_request() -> ChatCompletionRequest:
    """Sample chat completion request for testing."""
    return ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "What is the weather like today?"}
        ],
        max_tokens=100,
        temperature=0.7
    )


@pytest.fixture
def sample_chat_request_anthropic() -> ChatCompletionRequest:
    """Sample chat completion request for Anthropic testing."""
    return ChatCompletionRequest(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "user", "content": "Explain quantum computing"},
            {"role": "assistant", "content": "Quantum computing is..."},
            {"role": "user", "content": "Can you elaborate more?"}
        ],
        max_tokens=200,
        temperature=0.5
    )


@pytest.fixture
def sample_openai_response() -> Dict[str, Any]:
    """Sample OpenAI API response for testing."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "The weather today is sunny with a high of 75°F."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }


@pytest.fixture
def sample_pii_text() -> str:
    """Sample text with PII for DLP testing."""
    return """
    Hello, my name is John Doe and my email is john.doe@example.com.
    My phone number is (555) 123-4567 and my SSN is 123-45-6789.
    Please contact me at my credit card number 4111-1111-1111-1111.
    """


@pytest.fixture
def mock_redis():
    """Mock Redis client using fakeredis."""
    fake_redis = fakeredis.FakeAsyncRedis(decode_responses=True)
    return fake_redis


@pytest.fixture
def mock_openai_provider():
    """Mock OpenAI provider for testing."""
    provider = Mock(spec=LLMProvider)
    provider.create_completion = AsyncMock()
    return provider


@pytest.fixture
def mock_google_provider():
    """Mock Google provider for testing."""
    provider = Mock(spec=LLMProvider)
    provider.create_completion = AsyncMock()
    return provider


@pytest.fixture
def mock_anthropic_provider():
    """Mock Anthropic provider for testing."""
    provider = Mock(spec=LLMProvider)
    provider.create_completion = AsyncMock()
    return provider


@pytest.fixture
def test_config() -> Config:
    """Test configuration with all three providers."""
    providers = [
        ProviderConfig(
            name="openai",
            api_key_env="TEST_OPENAI_API_KEY",
            models=["gpt-4o", "gpt-3.5-turbo"]
        ),
        ProviderConfig(
            name="google",
            api_key_env="TEST_GOOGLE_API_KEY",
            models=["gemini-2.5-flash", "gemini-2.5-pro"]
        ),
        ProviderConfig(
            name="anthropic",
            api_key_env="TEST_ANTHROPIC_API_KEY",
            models=["claude-sonnet-4-20250514", "claude-opus-4-20250514"]
        )
    ]
    return Config(providers=providers)


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model for testing."""
    mock_model = Mock()
    mock_model.encode.return_value = [0.1] * 384  # 384-dimensional embedding
    return mock_model


@pytest.fixture
def mock_chroma_collection():
    """Mock ChromaDB collection for testing."""
    collection = Mock()
    collection.add = Mock()
    collection.query = Mock()
    collection.count = Mock(return_value=0)
    collection.name = "test_semantic_cache"
    return collection


@pytest.fixture
def temp_config_file():
    """Create a temporary config.yaml file for testing."""
    config_content = """
providers:
  - name: "openai"
    api_key_env: "TEST_OPENAI_API_KEY"
    models:
      - "gpt-3.5-turbo"
      - "gpt-4"
  - name: "google"
    api_key_env: "TEST_GOOGLE_API_KEY"
    models:
      - "gemini-2.5-flash"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    test_env = {
        "TEST_OPENAI_API_KEY": "test-openai-key-123",
        "TEST_GOOGLE_API_KEY": "test-google-key-456",
        "TEST_ANTHROPIC_API_KEY": "test-anthropic-key-789",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379"
    }
    
    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_env
    
    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


class MockAsyncContextManager:
    """Mock async context manager for HTTP clients."""
    
    def __init__(self, response_data: Dict[str, Any], status_code: int = 200):
        self.response_data = response_data
        self.status_code = status_code
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def json(self):
        return self.response_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_httpx_client():
    """Mock HTTPX client for testing HTTP requests."""
    mock_client = Mock()
    mock_client.post = AsyncMock()
    return mock_client


@pytest.fixture
def mock_vector_cache(monkeypatch):
    """Mock vector cache functions for testing."""
    mock_search = AsyncMock(return_value=None)
    mock_add = Mock()
    
    monkeypatch.setattr("app.vector_cache.search_semantic_cache", mock_search)
    monkeypatch.setattr("app.vector_cache.add_to_semantic_cache", mock_add)
    
    return {"search": mock_search, "add": mock_add}


# Test utilities
def assert_openai_compatible_response(response: Dict[str, Any]):
    """Assert that a response follows OpenAI API format."""
    assert "id" in response
    assert "object" in response
    assert "created" in response
    assert "model" in response
    assert "choices" in response
    assert "usage" in response
    
    # Check choices structure
    assert isinstance(response["choices"], list)
    assert len(response["choices"]) > 0
    
    choice = response["choices"][0]
    assert "index" in choice
    assert "message" in choice
    assert "finish_reason" in choice
    
    # Check message structure
    message = choice["message"]
    assert "role" in message
    assert "content" in message
    assert message["role"] == "assistant"
    
    # Check usage structure
    usage = response["usage"]
    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage
    assert "total_tokens" in usage


def create_mock_anthropic_response(text: str = "Test response") -> Mock:
    """Create a mock Anthropic API response."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = text
    mock_response.usage = Mock()
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    mock_response.stop_reason = "stop"
    return mock_response


def create_mock_google_response(text: str = "Test response") -> Mock:
    """Create a mock Google Gemini API response."""
    mock_response = Mock()
    mock_response.text = text
    return mock_response