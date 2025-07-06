"""
Semantic Cache Service

This module provides semantic caching functionality using sentence embeddings
and a vector database. It creates a two-level caching system where:
1. ChromaDB stores text embeddings (semantic meaning)
2. Redis stores the full LLM responses
3. ChromaDB entries point to Redis cache keys for retrieval

The system enables finding semantically similar queries even when the exact
text doesn't match, improving cache hit rates and reducing API calls.
"""

from sentence_transformers import SentenceTransformer
import chromadb
from typing import Optional, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize singleton instances at module level
# These are loaded once when the module is imported

# Embedding model - all-MiniLM-L6-v2 is fast and effective for semantic similarity
# It produces 384-dimensional embeddings and has good performance/speed balance
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# ChromaDB client - uses in-memory storage by default
# For production, consider persistent storage with chromadb.PersistentClient()
chroma_client = chromadb.Client()

# Vector collection for storing semantic cache embeddings
# Each document contains: embedding vector, metadata, and Redis cache key as ID
collection = chroma_client.get_or_create_collection(name="semantic_cache")


def add_to_semantic_cache(redis_cache_key: str, text: str) -> None:
    """
    Add a text prompt and its Redis cache key to the semantic cache.
    
    This function generates a vector embedding for the input text and stores it
    in ChromaDB with the Redis cache key as the document ID. This creates a
    mapping from semantic meaning to the cached response location.
    
    Args:
        redis_cache_key: The Redis key where the full LLM response is stored
        text: The input prompt text to generate embeddings for
        
    Raises:
        Exception: If embedding generation or ChromaDB insertion fails
    """
    try:
        # Generate vector embedding for the text
        # The model returns numpy array, convert to list for ChromaDB compatibility
        embedding = embedding_model.encode(text).tolist()
        
        # Add to ChromaDB collection
        # Use Redis cache key as document ID to create the link
        collection.add(
            embeddings=[embedding],
            documents=[text],  # Store original text for debugging/inspection
            ids=[redis_cache_key],
            metadatas=[{"cache_key": redis_cache_key, "text_length": len(text)}]
        )
        
        logger.debug(f"Added semantic cache entry: {redis_cache_key[:10]}... for text: {text[:50]}...")
        
    except Exception as e:
        logger.error(f"Failed to add semantic cache entry: {str(e)}")
        # Don't re-raise - semantic cache failures shouldn't break the main flow
        pass


def search_semantic_cache(text: str, similarity_threshold: float = 0.95) -> Optional[str]:
    """
    Search for semantically similar text in the cache.
    
    This function generates an embedding for the input text and queries ChromaDB
    for the most similar stored embedding. If the similarity exceeds the threshold,
    it returns the Redis cache key for retrieval.
    
    Args:
        text: The input prompt text to search for similar cached entries
        similarity_threshold: Minimum similarity score (0.0-1.0) to consider a hit.
                            Default 0.95 ensures very high semantic similarity.
                            
    Returns:
        str: Redis cache key if similar text found above threshold
        None: If no sufficiently similar text found
        
    Raises:
        Exception: If embedding generation or ChromaDB query fails
    """
    try:
        # Generate embedding for search query
        query_embedding = embedding_model.encode(text).tolist()
        
        # Query ChromaDB for most similar embedding
        # n_results=1 returns only the closest match
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            include=["distances", "metadatas", "documents"]
        )
        
        # Check if we got any results
        if not results['ids'] or not results['ids'][0]:
            logger.debug(f"No semantic cache entries found for: {text[:50]}...")
            return None
            
        # Extract similarity information
        # ChromaDB returns distances (lower = more similar)
        # Convert to similarity score (higher = more similar)
        distance = results['distances'][0][0]
        similarity = 1.0 - distance  # Convert distance to similarity
        
        # Check if similarity meets threshold
        if similarity >= similarity_threshold:
            cache_key = results['ids'][0][0]
            original_text = results['documents'][0][0]
            
            logger.info(f"Semantic cache hit! Similarity: {similarity:.3f}, "
                       f"Query: {text[:50]}..., "
                       f"Match: {original_text[:50]}...")
            
            return cache_key
        else:
            logger.debug(f"Semantic similarity {similarity:.3f} below threshold {similarity_threshold} "
                        f"for: {text[:50]}...")
            return None
            
    except Exception as e:
        logger.error(f"Failed to search semantic cache: {str(e)}")
        # Return None on error - don't break the main flow
        return None


def get_cache_stats() -> dict:
    """
    Get statistics about the semantic cache.
    
    Returns:
        dict: Cache statistics including entry count and collection info
    """
    try:
        count = collection.count()
        return {
            "collection_name": collection.name,
            "total_entries": count,
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimensions": 384
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        return {
            "error": str(e),
            "total_entries": 0
        }


def clear_semantic_cache() -> bool:
    """
    Clear all entries from the semantic cache.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Delete the collection and recreate it
        chroma_client.delete_collection(name="semantic_cache")
        global collection
        collection = chroma_client.get_or_create_collection(name="semantic_cache")
        
        logger.info("Semantic cache cleared successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear semantic cache: {str(e)}")
        return False