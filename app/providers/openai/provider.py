import httpx

from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider implementation for chat completions.
    
    This class implements the LLMProvider interface specifically for OpenAI's
    chat completions API. It handles authentication, request formatting, and
    error handling for OpenAI API calls.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the OpenAI provider with an API key.
        
        Args:
            api_key: The OpenAI API key for authentication.
        """
        self.api_key = api_key
    
    async def create_completion(self, request: ChatCompletionRequest) -> dict:
        """
        Create a chat completion using OpenAI's API.
        
        This method takes a standardized ChatCompletionRequest, constructs the appropriate
        headers and payload, and forwards the request to OpenAI's chat completions endpoint.
        
        Args:
            request: The validated chat completion request containing model, messages, and options.
            
        Returns:
            dict: The JSON response from OpenAI API containing the chat completion.
            
        Raises:
            httpx.HTTPStatusError: If the OpenAI API returns an HTTP error status.
            httpx.RequestError: If there's a network or request-related error.
        """
        OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = request.model_dump(exclude_unset=True)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json() 