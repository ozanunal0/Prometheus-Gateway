"""
Integration tests for caching systems.

Tests the two-level caching system including Redis exact cache,
semantic vector cache, and their integration in the main service flow.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
import hashlib

from app.services import process_chat_completion
from app.cache import generate_cache_key, get_from_cache, set_to_cache
from app.models import ChatCompletionRequest


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.asyncio
class TestRedisCaching:
    """Integration tests for Redis exact caching."""

    async def test_redis_cache_hit_flow(self, sample_chat_request, sample_openai_response, mock_redis):
        """Test complete cache hit flow with Redis."""
        # Pre-populate cache
        cache_key = generate_cache_key(sample_chat_request)
        await set_to_cache(cache_key, sample_openai_response)
        
        with patch('app.cache.redis_client', mock_redis):
            # Mock the cache to return our response
            mock_redis.get.return_value = json.dumps(sample_openai_response, sort_keys=True)
            
            cached_response = await get_from_cache(cache_key)
            
            assert cached_response == sample_openai_response
            mock_redis.get.assert_called_once_with(cache_key)

    async def test_redis_cache_miss_flow(self, sample_chat_request, mock_redis):
        """Test cache miss flow with Redis."""
        cache_key = generate_cache_key(sample_chat_request)
        
        with patch('app.cache.redis_client', mock_redis):
            mock_redis.get.return_value = None
            
            cached_response = await get_from_cache(cache_key)
            
            assert cached_response is None
            mock_redis.get.assert_called_once_with(cache_key)

    async def test_redis_cache_set_flow(self, sample_chat_request, sample_openai_response, mock_redis):
        """Test setting cache in Redis."""
        cache_key = generate_cache_key(sample_chat_request)
        
        with patch('app.cache.redis_client', mock_redis):
            mock_redis.setex.return_value = True
            
            result = await set_to_cache(cache_key, sample_openai_response)
            
            assert result is True
            mock_redis.setex.assert_called_once()
            
            # Verify the call arguments
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == cache_key  # Key
            assert call_args[0][1] == 3600  # TTL (1 hour)
            
            # Verify the stored data is JSON
            stored_data = call_args[0][2]
            parsed_data = json.loads(stored_data)
            assert parsed_data == sample_openai_response

    async def test_redis_error_handling(self, sample_chat_request, mock_redis):
        """Test Redis error handling."""
        cache_key = generate_cache_key(sample_chat_request)
        
        with patch('app.cache.redis_client', mock_redis):
            # Simulate Redis error
            mock_redis.get.side_effect = Exception("Redis connection error")
            
            cached_response = await get_from_cache(cache_key)
            
            # Should return None on error
            assert cached_response is None

    def test_cache_key_generation_consistency(self):
        """Test that cache key generation is consistent."""
        request1 = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            temperature=0.7
        )
        
        request2 = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            temperature=0.7
        )
        
        key1 = generate_cache_key(request1)
        key2 = generate_cache_key(request2)
        
        # Same requests should produce same cache key
        assert key1 == key2

    def test_cache_key_generation_uniqueness(self):
        """Test that different requests produce different cache keys."""
        request1 = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        request2 = ChatCompletionRequest(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": "Goodbye"}]
        )
        
        key1 = generate_cache_key(request1)
        key2 = generate_cache_key(request2)
        
        # Different requests should produce different cache keys
        assert key1 != key2


@pytest.mark.integration
@pytest.mark.vector
@pytest.mark.asyncio
class TestSemanticCaching:
    """Integration tests for semantic vector caching."""

    async def test_semantic_cache_add_and_search(self, mock_embedding_model, mock_chroma_collection):
        """Test adding to and searching semantic cache."""
        with patch('app.vector_cache.embedding_model', mock_embedding_model), \
             patch('app.vector_cache.collection', mock_chroma_collection):
            
            from app.vector_cache import add_to_semantic_cache, search_semantic_cache
            
            # Test adding to semantic cache
            redis_key = "test_cache_key_123"
            text = "What is the weather today?"
            
            add_to_semantic_cache(redis_key, text)
            
            # Verify embedding generation and storage
            mock_embedding_model.encode.assert_called_once_with(text)
            mock_chroma_collection.add.assert_called_once()
            
            # Check add call arguments
            add_call = mock_chroma_collection.add.call_args
            assert add_call[1]["ids"] == [redis_key]
            assert add_call[1]["documents"] == [text]
            assert add_call[1]["embeddings"] == [[0.1] * 384]

    async def test_semantic_cache_search_hit(self, mock_embedding_model, mock_chroma_collection):
        """Test semantic cache search with high similarity hit."""
        with patch('app.vector_cache.embedding_model', mock_embedding_model), \
             patch('app.vector_cache.collection', mock_chroma_collection):
            
            from app.vector_cache import search_semantic_cache
            
            # Mock successful search result with high similarity
            mock_chroma_collection.query.return_value = {
                'ids': [['cached_key_456']],
                'distances': [[0.02]],  # Low distance = high similarity
                'documents': [['How is the weather right now?']],
                'metadatas': [[{'cache_key': 'cached_key_456'}]]
            }
            
            search_text = "What's the weather like today?"
            result = await search_semantic_cache(search_text, similarity_threshold=0.95)
            
            # Should find the similar cached entry
            assert result == "cached_key_456"
            
            # Verify search was performed
            mock_embedding_model.encode.assert_called_once_with(search_text)
            mock_chroma_collection.query.assert_called_once()

    async def test_semantic_cache_search_miss(self, mock_embedding_model, mock_chroma_collection):
        """Test semantic cache search with low similarity miss."""
        with patch('app.vector_cache.embedding_model', mock_embedding_model), \
             patch('app.vector_cache.collection', mock_chroma_collection):
            
            from app.vector_cache import search_semantic_cache
            
            # Mock search result with low similarity
            mock_chroma_collection.query.return_value = {
                'ids': [['cached_key_789']],
                'distances': [[0.8]],  # High distance = low similarity
                'documents': [['What is quantum computing?']],
                'metadatas': [[{'cache_key': 'cached_key_789'}]]
            }
            
            search_text = "What's the weather like today?"
            result = await search_semantic_cache(search_text, similarity_threshold=0.95)
            
            # Should not find similar entry due to low similarity
            assert result is None

    async def test_semantic_cache_empty_results(self, mock_embedding_model, mock_chroma_collection):
        """Test semantic cache search with no results."""
        with patch('app.vector_cache.embedding_model', mock_embedding_model), \
             patch('app.vector_cache.collection', mock_chroma_collection):
            
            from app.vector_cache import search_semantic_cache
            
            # Mock empty search results
            mock_chroma_collection.query.return_value = {
                'ids': [[]],
                'distances': [[]],
                'documents': [[]],
                'metadatas': [[]]
            }
            
            search_text = "What's the weather like today?"
            result = await search_semantic_cache(search_text)
            
            # Should return None for empty results
            assert result is None


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestTwoLevelCachingFlow:
    """Integration tests for the complete two-level caching system."""

    async def test_exact_cache_hit_flow(self, sample_chat_request, sample_openai_response, mock_vector_cache):
        """Test that exact cache hit bypasses semantic cache and provider."""
        with patch('app.cache.get_from_cache', AsyncMock(return_value=sample_openai_response)), \
             patch('app.services.get_provider') as mock_get_provider:
            
            result = await process_chat_completion(sample_chat_request)
            
            # Should return cached response
            assert result == sample_openai_response
            
            # Should not call provider or semantic cache
            mock_get_provider.assert_not_called()
            mock_vector_cache["search"].assert_not_called()

    async def test_semantic_cache_hit_flow(self, sample_chat_request, sample_openai_response, mock_vector_cache):
        """Test semantic cache hit after exact cache miss."""
        semantic_cache_key = "semantic_key_123"
        
        with patch('app.cache.get_from_cache') as mock_get_cache, \
             patch('app.services.get_provider') as mock_get_provider:
            
            # Exact cache miss, semantic cache hit
            mock_get_cache.side_effect = [None, sample_openai_response]
            mock_vector_cache["search"].return_value = semantic_cache_key
            
            result = await process_chat_completion(sample_chat_request)
            
            # Should return cached response from semantic cache
            assert result == sample_openai_response
            
            # Should call semantic cache but not provider
            mock_vector_cache["search"].assert_called_once()
            mock_get_provider.assert_not_called()
            
            # Should call get_from_cache twice (exact + semantic)
            assert mock_get_cache.call_count == 2

    async def test_full_cache_miss_flow(self, sample_chat_request, sample_openai_response, mock_vector_cache):
        """Test full cache miss requiring provider call."""
        with patch('app.cache.get_from_cache', AsyncMock(return_value=None)), \
             patch('app.cache.set_to_cache', AsyncMock()), \
             patch('app.services.get_provider') as mock_get_provider:
            
            # Mock provider response
            mock_provider = Mock()
            mock_provider.create_completion = AsyncMock(return_value=sample_openai_response)
            mock_get_provider.return_value = mock_provider
            
            # No semantic cache hit
            mock_vector_cache["search"].return_value = None
            
            result = await process_chat_completion(sample_chat_request)
            
            # Should return provider response
            assert result == sample_openai_response
            
            # Should call provider
            mock_get_provider.assert_called_once()
            mock_provider.create_completion.assert_called_once()
            
            # Should update both caches
            mock_vector_cache["add"].assert_called_once()

    async def test_semantic_cache_expired_redis_entry(self, sample_chat_request, sample_openai_response, mock_vector_cache):
        """Test semantic cache hit but expired Redis entry."""
        semantic_cache_key = "expired_key_456"
        
        with patch('app.cache.get_from_cache') as mock_get_cache, \
             patch('app.cache.set_to_cache', AsyncMock()), \
             patch('app.services.get_provider') as mock_get_provider:
            
            # Exact cache miss, semantic hit but expired Redis entry
            mock_get_cache.side_effect = [None, None]  # Both cache lookups miss
            mock_vector_cache["search"].return_value = semantic_cache_key
            
            # Mock provider response
            mock_provider = Mock()
            mock_provider.create_completion = AsyncMock(return_value=sample_openai_response)
            mock_get_provider.return_value = mock_provider
            
            result = await process_chat_completion(sample_chat_request)
            
            # Should still get provider response
            assert result == sample_openai_response
            
            # Should call provider despite semantic cache hit
            mock_provider.create_completion.assert_called_once()
            
            # Should update both caches
            mock_vector_cache["add"].assert_called_once()

    async def test_cache_update_after_provider_call(self, sample_chat_request, sample_openai_response, mock_vector_cache):
        """Test that both caches are updated after provider call."""
        with patch('app.cache.get_from_cache', AsyncMock(return_value=None)), \
             patch('app.cache.set_to_cache', AsyncMock()) as mock_set_cache, \
             patch('app.services.get_provider') as mock_get_provider:
            
            # Mock provider
            mock_provider = Mock()
            mock_provider.create_completion = AsyncMock(return_value=sample_openai_response)
            mock_get_provider.return_value = mock_provider
            
            # No semantic cache hit
            mock_vector_cache["search"].return_value = None
            
            await process_chat_completion(sample_chat_request)
            
            # Should update exact cache
            mock_set_cache.assert_called_once()
            set_cache_args = mock_set_cache.call_args
            assert set_cache_args[0][1] == sample_openai_response
            
            # Should update semantic cache
            mock_vector_cache["add"].assert_called_once()
            add_cache_args = mock_vector_cache["add"].call_args
            assert add_cache_args[1]["text"] == "What is the weather like today?"

    async def test_error_handling_in_caching_flow(self, sample_chat_request, sample_openai_response, mock_vector_cache):
        """Test error handling when cache operations fail."""
        with patch('app.cache.get_from_cache', AsyncMock(side_effect=Exception("Cache error"))), \
             patch('app.services.get_provider') as mock_get_provider:
            
            # Mock provider to succeed
            mock_provider = Mock()
            mock_provider.create_completion = AsyncMock(return_value=sample_openai_response)
            mock_get_provider.return_value = mock_provider
            
            # Semantic cache also fails
            mock_vector_cache["search"].side_effect = Exception("Vector cache error")
            
            # Should still work and call provider
            result = await process_chat_completion(sample_chat_request)
            
            assert result == sample_openai_response
            mock_provider.create_completion.assert_called_once()

    async def test_prompt_text_extraction(self, mock_vector_cache):
        """Test correct extraction of prompt text for semantic caching."""
        # Multi-message conversation
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Follow-up question"}
            ]
        )
        
        with patch('app.cache.get_from_cache', AsyncMock(return_value=None)), \
             patch('app.cache.set_to_cache', AsyncMock()), \
             patch('app.services.get_provider') as mock_get_provider:
            
            mock_provider = Mock()
            mock_provider.create_completion = AsyncMock(return_value={"test": "response"})
            mock_get_provider.return_value = mock_provider
            
            mock_vector_cache["search"].return_value = None
            
            await process_chat_completion(request)
            
            # Should extract the last user message for semantic cache
            mock_vector_cache["add"].assert_called_once()
            add_call_args = mock_vector_cache["add"].call_args
            assert add_call_args[1]["text"] == "Follow-up question"