from app.models import ChatCompletionRequest
from app.providers.base import LLMProvider
from app.providers.openai.provider import OpenAIProvider
from app.providers.google.provider import GoogleProvider
from app.providers.anthropic.provider import AnthropicProvider
from app.cache import generate_cache_key, get_from_cache, set_to_cache
from app.vector_cache import search_semantic_cache, add_to_semantic_cache
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
    Process a chat completion request using the appropriate provider with two-level caching.
    
    This function implements a sophisticated two-level caching system:
    1. Level 1: Exact cache check (Redis with deterministic keys)
    2. Level 2: Semantic cache check (ChromaDB with vector similarity)
    Only calls the LLM provider if both cache levels miss.
    
    Args:
        request: The validated chat completion request containing model, messages, and options.
        
    Returns:
        dict: The JSON response from the cache or the selected LLM provider.
        
    Raises:
        ValueError: If no provider is found for the requested model.
        httpx.HTTPStatusError: If the provider's API returns an HTTP error status.
        httpx.RequestError: If there's a network or request-related error.
    """
    # Generate cache key for this request (deterministic based on request parameters)
    cache_key = generate_cache_key(request)
    
    # LEVEL 1: Exact Cache Check (Fastest - Direct Redis lookup)
    cached_response = await get_from_cache(cache_key)
    if cached_response is not None:
        print("🎯 EXACT CACHE HIT!")
        return cached_response
    
    # LEVEL 2: Semantic Cache Check (Smart - Vector similarity search)
    # Extract the user's prompt text (typically the last message)
    prompt_text = ""
    if request.messages and len(request.messages) > 0:
        # Get the last user message content
        prompt_text = request.messages[-1].get("content", "")
    
    # Search for semantically similar cached responses
    semantic_redis_key = await search_semantic_cache(prompt_text)
    if semantic_redis_key is not None:
        print("✅ SEMANTIC CACHE HIT!")
        # Retrieve the full response using the semantic cache's Redis key
        semantic_response = await get_from_cache(semantic_redis_key)
        if semantic_response is not None:
            return semantic_response
        else:
            # Semantic cache pointed to expired Redis entry - continue to provider
            print("⚠️  Semantic cache hit but Redis entry expired")
    
    # FULL CACHE MISS: Call the LLM provider
    print("🔄 CACHE MISS: Calling provider...")
    provider = get_provider(request.model)
    llm_response = await provider.create_completion(request)
    
    # UPDATE BOTH CACHE LEVELS after getting fresh response
    
    # Update Level 1: Store exact response in Redis cache
    await set_to_cache(cache_key, llm_response)
    
    # Update Level 2: Add semantic embedding linked to Redis key
    if prompt_text:  # Only if we have valid prompt text
        add_to_semantic_cache(redis_cache_key=cache_key, text=prompt_text)
    
    # Return the fresh response
    return llm_response 