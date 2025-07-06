from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider
from app.providers.openai.provider import OpenAIProvider


def get_provider(model_name: str) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider based on model name.
    
    This function examines the model name and returns the corresponding provider
    instance. It serves as a central point for provider selection logic.
    
    Args:
        model_name: The name of the model to determine the provider for.
        
    Returns:
        LLMProvider: An instance of the appropriate provider class.
        
    Raises:
        ValueError: If no provider is found for the given model name.
    """
    if model_name.startswith("gpt-"):
        return OpenAIProvider()
    
    raise ValueError(f"No provider found for model: {model_name}")


async def process_chat_completion(request: ChatCompletionRequest) -> dict:
    """
    Process a chat completion request using the appropriate provider.
    
    This function serves as the main service orchestrator. It uses the factory
    to get the correct provider based on the model name and delegates the
    actual completion generation to the selected provider.
    
    Args:
        request: The validated chat completion request containing model, messages, and options.
        
    Returns:
        dict: The JSON response from the selected LLM provider.
        
    Raises:
        ValueError: If no provider is found for the requested model.
        httpx.HTTPStatusError: If the provider's API returns an HTTP error status.
        httpx.RequestError: If there's a network or request-related error.
    """
    provider = get_provider(request.model)
    result = await provider.create_completion(request)
    return result 