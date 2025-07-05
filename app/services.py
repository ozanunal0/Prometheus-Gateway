# Core business logic and external API calls will be defined here 

import httpx

from app.config import settings
from app.models import ChatCompletionRequest


async def forward_request_to_openai(request: ChatCompletionRequest) -> dict:
    """
    Forward a chat completion request to the OpenAI API.
    
    This function takes a validated ChatCompletionRequest, constructs the appropriate
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
        'Authorization': f'Bearer {settings.OPENAI_API_KEY}'
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