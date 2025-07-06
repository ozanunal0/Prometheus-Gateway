"""
Unit tests for Anthropic Claude provider.

Tests the Anthropic provider's request/response translation, message handling,
and OpenAI compatibility without making actual API calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
import time

from app.providers.anthropic.provider import AnthropicProvider
from app.models import ChatCompletionRequest
from tests.conftest import assert_openai_compatible_response, create_mock_anthropic_response


@pytest.mark.unit
@pytest.mark.provider
class TestAnthropicProvider:
    """Test suite for Anthropic Claude provider."""

    def test_provider_initialization(self):
        """Test Anthropic provider initialization with API key."""
        api_key = "test-anthropic-api-key"
        
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            provider = AnthropicProvider(api_key=api_key)
            
            assert provider.api_key == api_key
            mock_anthropic.assert_called_once_with(api_key=api_key)

    def test_prepare_messages_for_anthropic(self):
        """Test message preparation for Anthropic API."""
        provider = AnthropicProvider(api_key="test-key")
        
        openai_messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        anthropic_messages = provider._prepare_messages_for_anthropic(openai_messages)
        
        # Anthropic uses similar format to OpenAI, so messages should be preserved
        assert len(anthropic_messages) == 4
        
        for i, original_msg in enumerate(openai_messages):
            assert anthropic_messages[i]["role"] == original_msg["role"]
            assert anthropic_messages[i]["content"] == original_msg["content"]

    def test_translate_response_to_openai_format(self):
        """Test response translation from Anthropic to OpenAI format."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Create mock Anthropic response
        anthropic_response = create_mock_anthropic_response("This is Claude's response.")
        model_name = "claude-sonnet-4-20250514"
        
        openai_response = provider._translate_response_to_openai(anthropic_response, model_name)
        
        # Verify OpenAI compatibility
        assert_openai_compatible_response(openai_response)
        
        # Check specific fields
        assert openai_response["model"] == model_name
        assert openai_response["choices"][0]["message"]["content"] == "This is Claude's response."
        assert openai_response["choices"][0]["message"]["role"] == "assistant"
        assert openai_response["choices"][0]["finish_reason"] == "stop"
        
        # Check token usage (should use actual counts from Anthropic)
        usage = openai_response["usage"]
        assert usage["prompt_tokens"] == 10  # From mock
        assert usage["completion_tokens"] == 5  # From mock
        assert usage["total_tokens"] == 15

    def test_translate_response_with_empty_content(self):
        """Test handling of empty content in Anthropic response."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Create mock response with empty content
        anthropic_response = Mock()
        anthropic_response.content = []
        anthropic_response.usage = Mock()
        anthropic_response.usage.input_tokens = 5
        anthropic_response.usage.output_tokens = 0
        anthropic_response.stop_reason = "stop"
        
        openai_response = provider._translate_response_to_openai(
            anthropic_response, "claude-sonnet-4-20250514"
        )
        
        assert openai_response["choices"][0]["message"]["content"] == ""
        assert_openai_compatible_response(openai_response)

    def test_translate_response_with_different_stop_reasons(self):
        """Test handling of different stop reasons from Anthropic."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Test with different stop reasons
        stop_reasons = ["stop", "max_tokens", "stop_sequence", None]
        
        for stop_reason in stop_reasons:
            anthropic_response = create_mock_anthropic_response("Test")
            anthropic_response.stop_reason = stop_reason
            
            openai_response = provider._translate_response_to_openai(
                anthropic_response, "claude-sonnet-4-20250514"
            )
            
            expected_finish_reason = stop_reason if stop_reason else "stop"
            assert openai_response["choices"][0]["finish_reason"] == expected_finish_reason

    @pytest.mark.asyncio
    async def test_create_completion_success(self, sample_chat_request_anthropic):
        """Test successful completion creation with Anthropic API."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Mock the Anthropic client
        mock_client = Mock()
        mock_response = create_mock_anthropic_response("Quantum computing utilizes quantum mechanics...")
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, 'client', mock_client):
            result = await provider.create_completion(sample_chat_request_anthropic)
            
            # Verify OpenAI compatibility
            assert_openai_compatible_response(result)
            
            # Check response content
            assert result["model"] == sample_chat_request_anthropic.model
            assert "Quantum computing utilizes" in result["choices"][0]["message"]["content"]
            
            # Verify Anthropic API was called correctly
            mock_client.messages.create.assert_called_once()
            
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == sample_chat_request_anthropic.model
            assert call_kwargs["max_tokens"] == sample_chat_request_anthropic.max_tokens
            assert call_kwargs["temperature"] == sample_chat_request_anthropic.temperature
            assert len(call_kwargs["messages"]) == 3  # All messages from the request

    @pytest.mark.asyncio
    async def test_create_completion_with_default_max_tokens(self):
        """Test completion creation with default max_tokens."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Create request without max_tokens
        request = ChatCompletionRequest(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        mock_client = Mock()
        mock_response = create_mock_anthropic_response("Hello there!")
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, 'client', mock_client):
            await provider.create_completion(request)
            
            # Verify default max_tokens was used
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["max_tokens"] == 4096  # Default value

    @pytest.mark.asyncio
    async def test_create_completion_with_default_temperature(self):
        """Test completion creation with default temperature."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Create request without temperature
        request = ChatCompletionRequest(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100
        )
        
        mock_client = Mock()
        mock_response = create_mock_anthropic_response("Hello there!")
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, 'client', mock_client):
            await provider.create_completion(request)
            
            # Verify default temperature was used
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["temperature"] == 0.7  # Default value

    @pytest.mark.asyncio
    async def test_create_completion_error_handling(self, sample_chat_request_anthropic):
        """Test error handling when Anthropic API fails."""
        provider = AnthropicProvider(api_key="test-key")
        
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(side_effect=Exception("Anthropic API Error"))
        
        with patch.object(provider, 'client', mock_client):
            with pytest.raises(Exception) as exc_info:
                await provider.create_completion(sample_chat_request_anthropic)
            
            assert "Anthropic Claude API error" in str(exc_info.value)

    def test_response_id_and_timestamp_generation(self):
        """Test that response IDs and timestamps are generated correctly."""
        provider = AnthropicProvider(api_key="test-key")
        
        anthropic_response = create_mock_anthropic_response("Test response")
        
        with patch('time.time', return_value=1234567890):
            openai_response = provider._translate_response_to_openai(
                anthropic_response, "claude-sonnet-4-20250514"
            )
            
            assert openai_response["id"] == "chatcmpl-1234567890"
            assert openai_response["created"] == 1234567890
            assert openai_response["object"] == "chat.completion"

    def test_token_usage_accuracy(self):
        """Test that token usage from Anthropic is preserved accurately."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Create response with specific token counts
        anthropic_response = create_mock_anthropic_response("Test response")
        anthropic_response.usage.input_tokens = 25
        anthropic_response.usage.output_tokens = 15
        
        openai_response = provider._translate_response_to_openai(
            anthropic_response, "claude-sonnet-4-20250514"
        )
        
        usage = openai_response["usage"]
        assert usage["prompt_tokens"] == 25
        assert usage["completion_tokens"] == 15
        assert usage["total_tokens"] == 40

    def test_handles_missing_usage_data(self):
        """Test handling when usage data is missing from Anthropic response."""
        provider = AnthropicProvider(api_key="test-key")
        
        anthropic_response = create_mock_anthropic_response("Test response")
        anthropic_response.usage = None
        
        openai_response = provider._translate_response_to_openai(
            anthropic_response, "claude-sonnet-4-20250514"
        )
        
        usage = openai_response["usage"]
        assert usage["prompt_tokens"] == 0
        assert usage["completion_tokens"] == 0
        assert usage["total_tokens"] == 0