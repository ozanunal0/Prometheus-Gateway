import json
import hashlib
import os
import redis.asyncio as aioredis
from typing import Optional

from app.models import ChatCompletionRequest


# Single, reusable asynchronous Redis client instance
redis_client = aioredis.from_url(
    f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}",
    decode_responses=True
)


def generate_cache_key(request: ChatCompletionRequest) -> str:
    """
    Generate a consistent cache key for a ChatCompletionRequest.
    
    This function creates a stable hash based on the request parameters,
    ensuring identical requests produce the same cache key.
    
    Args:
        request: The chat completion request to generate a key for.
        
    Returns:
        str: A SHA-256 hexadecimal digest as the cache key.
    """
    # Serialize request to JSON with sorted keys for consistency
    request_dict = request.model_dump()
    request_json = json.dumps(request_dict, sort_keys=True)
    
    # Generate SHA-256 hash of the serialized request
    hash_object = hashlib.sha256(request_json.encode('utf-8'))
    cache_key = hash_object.hexdigest()
    
    return cache_key


async def get_from_cache(key: str) -> Optional[dict]:
    """
    Retrieve a value from Redis cache.
    
    Args:
        key: The cache key to retrieve.
        
    Returns:
        dict | None: The cached value as a dictionary if found, None otherwise.
    """
    try:
        cached_value = await redis_client.get(key)
        if cached_value is not None:
            # Deserialize JSON back to Python dictionary
            return json.loads(cached_value)
        return None
    except (json.JSONDecodeError, aioredis.RedisError):
        # Return None if there's any error with cache retrieval
        return None


async def set_to_cache(key: str, value: dict, expire_seconds: int = 3600) -> bool:
    """
    Store a value in Redis cache with expiration.
    
    Args:
        key: The cache key to store the value under.
        value: The dictionary value to cache.
        expire_seconds: TTL in seconds (default: 1 hour).
        
    Returns:
        bool: True if successfully cached, False otherwise.
    """
    try:
        # Serialize dictionary to JSON string
        serialized_value = json.dumps(value, sort_keys=True)
        
        # Store in Redis with expiration
        await redis_client.setex(key, expire_seconds, serialized_value)
        return True
    except (ValueError, aioredis.RedisError):
        # Return False if there's any error with cache storage
        return False 