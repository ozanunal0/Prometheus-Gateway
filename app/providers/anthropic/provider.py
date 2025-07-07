import anthropic
from typing import Dict, List, Any
import time

from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude provider implementation for chat completions.
    
    This class implements the LLMProvider interface specifically for Anthropic's
    Claude API. It handles authentication, request/response translation, and
    provides a unified OpenAI-compatible API interface.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Anthropic provider with an API key.
        
        Args:
            api_key: The Anthropic API key for authentication.
        """
        self.api_key = api_key
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    def _prepare_messages_for_anthropic(self, messages: List) -> List[Dict[str, str]]:
        """
        Prepare messages for Anthropic API format.
        
        Anthropic's Messages API uses a similar format to OpenAI, but we need to
        ensure proper structure and handle any system messages appropriately.
        
        Args:
            messages: List of ChatMessage objects.
            
        Returns:
            List of messages formatted for Anthropic API.
        """
        anthropic_messages = []
        
        for message in messages:
            # Handle both dict and Pydantic model formats
            if hasattr(message, 'role'):
                # Pydantic model
                role = message.role
                content = message.content
            else:
                # Dictionary format (for testing)
                role = message["role"]
                content = message["content"]
            
            # Anthropic supports user, assistant, and system roles
            # System messages can be passed directly
            anthropic_messages.append({
                "role": role,
                "content": content
            })
        
        return anthropic_messages
    
    def _translate_response_to_openai(self, anthropic_response, model_name: str) -> Dict[str, Any]:
        """
        Translate Anthropic response to OpenAI-compatible format.
        
        Args:
            anthropic_response: The response from Anthropic Claude API.
            model_name: The model name used for the request.
            
        Returns:
            Dictionary in OpenAI response format.
        """
        # Extract the response text from Anthropic's content structure
        response_text = ""
        if anthropic_response.content and len(anthropic_response.content) > 0:
            response_text = anthropic_response.content[0].text
        
        # Extract token usage information
        input_tokens = anthropic_response.usage.input_tokens if anthropic_response.usage else 0
        output_tokens = anthropic_response.usage.output_tokens if anthropic_response.usage else 0
        total_tokens = input_tokens + output_tokens
        
        # Create OpenAI-compatible response structure
        openai_response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": anthropic_response.stop_reason or "stop"
                }
            ],
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        }
        
        return openai_response
    
    async def create_completion(self, request: ChatCompletionRequest) -> dict:
        """
        Create a chat completion using Anthropic Claude API.
        
        This method translates the OpenAI-compatible request to Anthropic's format,
        calls the Claude API, and translates the response back to OpenAI format.
        
        Args:
            request: The validated chat completion request containing model, messages, and options.
            
        Returns:
            dict: The JSON response in OpenAI-compatible format.
            
        Raises:
            Exception: If the Anthropic API call fails or returns an error.
        """
        try:
            # Prepare messages for Anthropic API
            anthropic_messages = self._prepare_messages_for_anthropic(request.messages)
            
            # Ensure max_tokens is provided (required by Anthropic)
            max_tokens = getattr(request, 'max_tokens', 4096)
            if max_tokens is None:
                max_tokens = 4096
            
            # Prepare other parameters
            temperature = getattr(request, 'temperature', None)
            if temperature is None:
                temperature = 0.7
            
            # Call Anthropic Claude API
            response = await self.client.messages.create(
                model=request.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=anthropic_messages
            )
            
            # Translate response back to OpenAI format
            openai_response = self._translate_response_to_openai(response, request.model)
            
            return openai_response
            
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Anthropic Claude API error: {str(e)}")