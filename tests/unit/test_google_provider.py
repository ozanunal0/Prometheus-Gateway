"""
Unit tests for Google Gemini provider.

Tests the Google provider's request/response translation, message format
conversion, and OpenAI compatibility without making actual API calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
import time

from app.providers.google.provider import GoogleProvider
from app.models import ChatCompletionRequest
from tests.conftest import assert_openai_compatible_response, create_mock_google_response


@pytest.mark.unit
@pytest.mark.provider
class TestGoogleProvider:
    """Test suite for Google Gemini provider."""

    def test_provider_initialization(self):
        """Test Google provider initialization with API key."""
        api_key = "test-google-api-key"
        
        with patch('google.generativeai.configure') as mock_configure:
            provider = GoogleProvider(api_key=api_key)
            
            assert provider.api_key == api_key
            mock_configure.assert_called_once_with(api_key=api_key)

    def test_translate_messages_to_google_format(self):
        """Test message translation from OpenAI to Google format."""
        provider = GoogleProvider(api_key="test-key")
        
        openai_messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        google_messages = provider._translate_messages_to_google(openai_messages)
        
        assert len(google_messages) == 4
        
        # Check system message (converted to user)
        assert google_messages[0]["role"] == "user"
        assert google_messages[0]["parts"] == ["You are helpful."]
        
        # Check user message
        assert google_messages[1]["role"] == "user"
        assert google_messages[1]["parts"] == ["Hello"]
        
        # Check assistant message (converted to model)
        assert google_messages[2]["role"] == "model"
        assert google_messages[2]["parts"] == ["Hi there!"]
        
        # Check another user message
        assert google_messages[3]["role"] == "user"
        assert google_messages[3]["parts"] == ["How are you?"]

    def test_translate_response_to_openai_format(self):
        """Test response translation from Google to OpenAI format."""
        provider = GoogleProvider(api_key="test-key")
        
        # Create mock Google response
        google_response = create_mock_google_response("This is a test response.")
        model_name = "gemini-2.5-flash"
        prompt_tokens = 15
        
        openai_response = provider._translate_response_to_openai(
            google_response, model_name, prompt_tokens
        )
        
        # Verify OpenAI compatibility
        assert_openai_compatible_response(openai_response)
        
        # Check specific fields
        assert openai_response["model"] == model_name
        assert openai_response["choices"][0]["message"]["content"] == "This is a test response."
        assert openai_response["choices"][0]["message"]["role"] == "assistant"
        assert openai_response["choices"][0]["finish_reason"] == "stop"
        
        # Check token estimation
        usage = openai_response["usage"]
        assert usage["prompt_tokens"] == prompt_tokens
        assert usage["completion_tokens"] > 0  # Should estimate based on response length
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    def test_translate_empty_response(self):
        """Test handling of empty Google response."""
        provider = GoogleProvider(api_key="test-key")
        
        # Create mock empty response
        google_response = Mock()
        google_response.text = ""
        
        openai_response = provider._translate_response_to_openai(
            google_response, "gemini-2.5-flash", 10
        )
        
        assert openai_response["choices"][0]["message"]["content"] == ""
        assert_openai_compatible_response(openai_response)

    @pytest.mark.asyncio
    async def test_create_completion_success(self, sample_chat_request):
        """Test successful completion creation with Google API."""
        provider = GoogleProvider(api_key="test-key")
        
        # Mock the Google GenerativeModel
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_response = create_mock_google_response("Test response from Gemini")
            mock_model.generate_content_async.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            result = await provider.create_completion(sample_chat_request)
            
            # Verify OpenAI compatibility
            assert_openai_compatible_response(result)
            
            # Check response content
            assert result["model"] == sample_chat_request.model
            assert result["choices"][0]["message"]["content"] == "Test response from Gemini"
            
            # Verify Google API was called correctly
            mock_model_class.assert_called_once_with(sample_chat_request.model)
            mock_model.generate_content_async.assert_called_once()
            
            # Check the call arguments
            call_args = mock_model.generate_content_async.call_args
            google_messages = call_args[0][0]  # First positional argument
            generation_config = call_args[1]["generation_config"]
            
            # Verify message translation
            assert len(google_messages) == 1
            assert google_messages[0]["role"] == "user"
            assert google_messages[0]["parts"] == ["What is the weather like today?"]
            
            # Verify generation config
            assert generation_config.max_output_tokens == sample_chat_request.max_tokens
            assert generation_config.temperature == sample_chat_request.temperature

    @pytest.mark.asyncio
    async def test_create_completion_with_defaults(self):
        """Test completion creation with default parameters."""
        provider = GoogleProvider(api_key="test-key")
        
        # Create request without max_tokens and temperature
        request = ChatCompletionRequest(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_response = create_mock_google_response("Hello there!")
            mock_model.generate_content_async.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            result = await provider.create_completion(request)
            
            # Verify defaults were applied
            call_args = mock_model.generate_content_async.call_args
            generation_config = call_args[1]["generation_config"]
            
            assert generation_config.max_output_tokens == 1000  # Default
            assert generation_config.temperature == 0.7  # Default

    @pytest.mark.asyncio
    async def test_create_completion_error_handling(self, sample_chat_request):
        """Test error handling when Google API fails."""
        provider = GoogleProvider(api_key="test-key")
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content_async.side_effect = Exception("Google API Error")
            mock_model_class.return_value = mock_model
            
            with pytest.raises(Exception) as exc_info:
                await provider.create_completion(sample_chat_request)
            
            assert "Google Gemini API error" in str(exc_info.value)

    def test_unknown_role_handling(self):
        """Test handling of unknown message roles."""
        provider = GoogleProvider(api_key="test-key")
        
        messages_with_unknown_role = [
            {"role": "unknown_role", "content": "Some content"}
        ]
        
        google_messages = provider._translate_messages_to_google(messages_with_unknown_role)
        
        # Unknown roles should default to "user"
        assert google_messages[0]["role"] == "user"
        assert google_messages[0]["parts"] == ["Some content"]

    def test_token_estimation_accuracy(self):
        """Test that token estimation is reasonable."""
        provider = GoogleProvider(api_key="test-key")
        
        # Test with known text
        response_text = "This is a test response with multiple words for token estimation."
        google_response = create_mock_google_response(response_text)
        
        openai_response = provider._translate_response_to_openai(
            google_response, "gemini-2.5-flash", 10
        )
        
        # Token count should be approximately equal to word count
        word_count = len(response_text.split())
        estimated_tokens = openai_response["usage"]["completion_tokens"]
        
        # Allow some variance in token estimation
        assert estimated_tokens >= word_count * 0.5
        assert estimated_tokens <= word_count * 2

    def test_response_id_generation(self):
        """Test that response IDs are generated correctly."""
        provider = GoogleProvider(api_key="test-key")
        
        google_response = create_mock_google_response("Test")
        
        with patch('time.time', return_value=1234567890):
            openai_response = provider._translate_response_to_openai(
                google_response, "gemini-2.5-flash", 10
            )
            
            assert openai_response["id"] == "chatcmpl-1234567890"
            assert openai_response["created"] == 1234567890