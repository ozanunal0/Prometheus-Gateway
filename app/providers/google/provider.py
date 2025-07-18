import google.generativeai as genai
from typing import Dict, List, Any
import time

from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider


class GoogleProvider(LLMProvider):
    """
    Google Gemini provider implementation for chat completions.
    
    This class implements the LLMProvider interface specifically for Google's
    Gemini API. It handles authentication, request/response translation, and
    provides a unified OpenAI-compatible API interface.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Google provider with an API key.
        
        Args:
            api_key: The Google AI API key for authentication.
        """
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
    
    def _translate_messages_to_google(self, messages: List) -> List[Dict[str, str]]:
        """
        Translate OpenAI-format messages to Google Gemini format.
        
        OpenAI uses: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        Google uses: [{"role": "user", "parts": ["..."]}, {"role": "model", "parts": ["..."]}]
        
        Args:
            messages: List of ChatMessage objects.
            
        Returns:
            List of messages in Google Gemini format.
        """
        translated_messages = []
        
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
            
            # Map OpenAI roles to Google roles
            if role == "user":
                google_role = "user"
            elif role == "assistant":
                google_role = "model"
            elif role == "system":
                # Google doesn't have a direct system role, treat as user message
                google_role = "user"
            else:
                # Default to user for unknown roles
                google_role = "user"
            
            translated_messages.append({
                "role": google_role,
                "parts": [content]
            })
        
        return translated_messages
    
    def _translate_response_to_openai(self, google_response, model_name: str, prompt_tokens: int) -> Dict[str, Any]:
        """
        Translate Google Gemini response to OpenAI-compatible format.
        
        Args:
            google_response: The response from Google Gemini API.
            model_name: The model name used for the request.
            prompt_tokens: Estimated prompt tokens (Google doesn't provide this).
            
        Returns:
            Dictionary in OpenAI response format.
        """
        # Extract the response text with safety handling
        response_text = ""
        try:
            if hasattr(google_response, 'text') and google_response.text:
                response_text = google_response.text
            elif hasattr(google_response, 'candidates') and google_response.candidates:
                # Try to extract from candidates if direct text access fails
                candidate = google_response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
        except (ValueError, AttributeError) as e:
            # Handle cases where content was blocked or empty
            if "finish_reason" in str(e) and "2" in str(e):
                response_text = "I cannot provide a response to that request due to safety guidelines."
            else:
                response_text = "I apologize, but I cannot generate a response at this time."
        
        # Estimate completion tokens (rough approximation)
        completion_tokens = len(response_text.split())
        total_tokens = prompt_tokens + completion_tokens
        
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
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        }
        
        return openai_response
    
    async def create_completion(self, request: ChatCompletionRequest) -> dict:
        """
        Create a chat completion using Google Gemini API.
        
        This method translates the OpenAI-compatible request to Google's format,
        calls the Gemini API, and translates the response back to OpenAI format.
        
        Args:
            request: The validated chat completion request containing model, messages, and options.
            
        Returns:
            dict: The JSON response in OpenAI-compatible format.
            
        Raises:
            Exception: If the Google API call fails or returns an error.
        """
        try:
            # Initialize the model
            model = genai.GenerativeModel(request.model)
            
            # Translate messages from OpenAI format to Google format
            google_messages = self._translate_messages_to_google(request.messages)
            
            # Estimate prompt tokens (rough approximation)
            prompt_text = " ".join([
                msg.content if hasattr(msg, 'content') else msg["content"] 
                for msg in request.messages
            ])
            prompt_tokens = len(prompt_text.split())
            
            # Configure generation parameters
            max_tokens = getattr(request, 'max_tokens', None)
            if max_tokens is None:
                max_tokens = 1000
                
            temperature = getattr(request, 'temperature', None)
            if temperature is None:
                temperature = 0.7
                
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Call Google Gemini API
            response = await model.generate_content_async(
                google_messages,
                generation_config=generation_config
            )
            
            # Translate response back to OpenAI format
            openai_response = self._translate_response_to_openai(
                response, request.model, prompt_tokens
            )
            
            return openai_response
            
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Google Gemini API error: {str(e)}")