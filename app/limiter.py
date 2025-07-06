from slowapi import Limiter
from starlette.requests import Request


def get_api_key_from_header(request: Request) -> str:
    """
    Key function for rate limiting that identifies clients by their API key.
    
    This function extracts the API key from the X-API-Key header and uses it
    as the identifier for rate limiting. If no API key is present, it falls
    back to the client's IP address.
    
    Args:
        request: The incoming HTTP request object.
        
    Returns:
        str: The API key from the header, or the client's IP address as fallback.
    """
    # Use the API key from the header for rate limiting.
    # Fallback to the IP address if the header is not present.
    return request.headers.get("x-api-key", request.client.host)


# Create the Limiter instance with our key function
limiter = Limiter(key_func=get_api_key_from_header)