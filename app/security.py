import secrets
import hashlib


def generate_api_key() -> str:
    """
    Generate a new, secure API key with sk- prefix.
    
    Returns:
        str: A secure random API key prefixed with 'sk-'.
    """
    return f"sk-{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256 for secure database storage.
    
    Args:
        api_key: The plaintext API key to hash.
        
    Returns:
        str: The SHA-256 hash of the API key as a hexadecimal string.
    """
    return hashlib.sha256(api_key.encode()).hexdigest() 