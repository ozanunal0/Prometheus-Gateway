from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider
from app.providers.openai.provider import OpenAIProvider
from app.providers.google.provider import GoogleProvider
from app.providers.anthropic.provider import AnthropicProvider
from app.cache import generate_cache_key, get_from_cache, set_to_cache
from app.config import config


def get_provider(model_name: str) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider based on model name.
    
    This function examines the model name and returns the corresponding provider
    instance using the dynamic configuration from config.yaml. It serves as a 
    data-driven routing engine that maps models to their providers.
    
    Args:
        model_name: The name of the model to determine the provider for.
        
    Returns:
        LLMProvider: An instance of the appropriate provider class.
        
    Raises:
        ValueError: If no provider is found for the given model name.
    """
    # Iterate through each provider configuration
    for provider_config in config.providers:
        # Check if the requested model is handled by this provider
        if model_name in provider_config.models:
            # Route based on provider name
            if provider_config.name == "openai":
                return OpenAIProvider(api_key=provider_config.api_key)
            elif provider_config.name == "google":
                return GoogleProvider(api_key=provider_config.api_key)
            elif provider_config.name == "anthropic":
                return AnthropicProvider(api_key=provider_config.api_key)
            # Future providers can be added here:
            # elif provider_config.name == "cohere":
            #     return CohereProvider(api_key=provider_config.api_key)
    
    # No provider found for the model
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