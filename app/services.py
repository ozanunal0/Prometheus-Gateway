from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider
from app.providers.openai.provider import OpenAIProvider
from app.cache import generate_cache_key, get_from_cache, set_to_cache


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
    Process a chat completion request using the appropriate provider with caching.
    
    This function implements the Cache-Aside pattern: it first checks the cache
    for a previously computed response, and only calls the LLM provider on a cache miss.
    
    Args:
        request: The validated chat completion request containing model, messages, and options.
        
    Returns:
        dict: The JSON response from the cache or the selected LLM provider.
        
    Raises:
        ValueError: If no provider is found for the requested model.
        httpx.HTTPStatusError: If the provider's API returns an HTTP error status.
        httpx.RequestError: If there's a network or request-related error.
    """
    # Generate cache key for this request
    cache_key = generate_cache_key(request)
    
    # Check cache first (Cache-Aside pattern)
    cached_response = await get_from_cache(cache_key)
    if cached_response is not None:
        print("CACHE HIT!")
        return cached_response
    
    # Cache miss - call the provider
    print("CACHE MISS: Calling provider...")
    provider = get_provider(request.model)
    llm_response = await provider.create_completion(request)
    
    # Store the response in cache for future requests
    await set_to_cache(cache_key, llm_response)
    
    # Return the fresh response
    return llm_response 