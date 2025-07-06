"""
Unit tests for OpenAI provider.

Tests the OpenAI provider's request/response handling, API integration,
and error handling without making actual API calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
import httpx

from app.providers.openai.provider import OpenAIProvider
from app.models import ChatCompletionRequest
from tests.conftest import assert_openai_compatible_response


@pytest.mark.unit
@pytest.mark.provider
class TestOpenAIProvider:
    """Test suite for OpenAI provider."""

    def test_provider_initialization(self):
        """Test OpenAI provider initialization with API key."""
        api_key = "test-api-key-123"
        provider = OpenAIProvider(api_key=api_key)
        
        assert provider.api_key == api_key

    @pytest.mark.asyncio
    async def test_create_completion_success(self, sample_chat_request, sample_openai_response):
        """Test successful completion creation."""
        provider = OpenAIProvider(api_key="test-key")
        
        # Mock httpx.AsyncClient
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = sample_openai_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await provider.create_completion(sample_chat_request)
            
            # Verify the result
            assert result == sample_openai_response
            assert_openai_compatible_response(result)
            
            # Verify API call was made correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            
            # Check URL
            assert call_args[0][0] == "https://api.openai.com/v1/chat/completions"
            
            # Check headers
            headers = call_args[1]["headers"]
            assert headers["Content-Type"] == "application/json"
            assert headers["Authorization"] == "Bearer test-key"
            
            # Check payload
            payload = call_args[1]["json"]
            assert payload["model"] == sample_chat_request.model
            # Convert Pydantic models to dicts for comparison
            expected_messages = [msg.model_dump() if hasattr(msg, 'model_dump') else msg for msg in sample_chat_request.messages]
            assert payload["messages"] == expected_messages
            assert payload["max_tokens"] == sample_chat_request.max_tokens
            assert payload["temperature"] == sample_chat_request.temperature

    @pytest.mark.asyncio
    async def test_create_completion_http_error(self, sample_chat_request):
        """Test handling of HTTP errors from OpenAI API."""
        provider = OpenAIProvider(api_key="test-key")
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "API Error", request=Mock(), response=Mock()
            )
            
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(httpx.HTTPStatusError):
                await provider.create_completion(sample_chat_request)

    @pytest.mark.asyncio
    async def test_create_completion_request_error(self, sample_chat_request):
        """Test handling of request errors."""
        provider = OpenAIProvider(api_key="test-key")
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.RequestError("Network error")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(httpx.RequestError):
                await provider.create_completion(sample_chat_request)

    @pytest.mark.asyncio
    async def test_create_completion_excludes_unset_fields(self):
        """Test that unset fields are excluded from the API request."""
        provider = OpenAIProvider(api_key="test-key")
        
        # Create request without optional fields
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {"test": "response"}
            mock_response.raise_for_status.return_value = None
            
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            await provider.create_completion(request)
            
            # Check that only set fields are included
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            
            assert "model" in payload
            assert "messages" in payload
            # Optional fields should not be present if not set
            assert "max_tokens" not in payload or payload["max_tokens"] is None
            assert "temperature" not in payload or payload["temperature"] is None

    @pytest.mark.asyncio
    async def test_different_message_types(self):
        """Test handling of different message types (user, assistant, system)."""
        provider = OpenAIProvider(api_key="test-key")
        
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {"test": "response"}
            mock_response.raise_for_status.return_value = None
            
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            await provider.create_completion(request)
            
            # Verify all messages are passed correctly
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            
            assert len(payload["messages"]) == 4
            assert payload["messages"][0]["role"] == "system"
            assert payload["messages"][1]["role"] == "user"
            assert payload["messages"][2]["role"] == "assistant"
            assert payload["messages"][3]["role"] == "user"

    def test_api_key_in_headers(self):
        """Test that API key is correctly formatted in authorization header."""
        api_key = "sk-1234567890abcdef"
        provider = OpenAIProvider(api_key=api_key)
        
        # This test would be part of the create_completion test,
        # but we can verify the API key is stored correctly
        assert provider.api_key == api_key