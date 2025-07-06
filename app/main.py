import httpx
from fastapi import FastAPI, HTTPException, Depends, Request

from app.models import ChatCompletionRequest
from app.db_models.api_key import APIKey
from app.services import process_chat_completion
from app.database import create_db_and_tables
from app.dependencies import get_valid_api_key
from app.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from app.middleware.dlp_middleware import DlpMiddleware

app = FastAPI()

# Add DLP middleware for PII detection and anonymization (first in chain)
app.add_middleware(DlpMiddleware)

# Add SlowAPI middleware for rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/v1/chat/completions")
@limiter.limit("10/minute")
async def chat_completions(
    request: Request,
    payload: ChatCompletionRequest,
    api_key: APIKey = Depends(get_valid_api_key)
) -> dict:
    """
    Process chat completion requests using the appropriate LLM provider.
    
    This endpoint receives chat completion requests, validates them using Pydantic models,
    and forwards them to the appropriate LLM provider based on the model name.
    Access requires a valid API key in the X-API-Key header and is rate limited to 10 requests per minute.
    PII in user messages is automatically detected and anonymized before processing.
    
    Args:
        request: The HTTP request object (required for rate limiting).
        payload: The chat completion request containing model, messages, and options.
        api_key: The authenticated API key (injected by dependency).
        
    Returns:
        dict: The JSON response from the selected LLM provider.
        
    Raises:
        HTTPException: If no provider is found for the model, or if the provider's API returns an error.
    """
    try:
        result = await process_chat_completion(request=payload)
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.json()
        )

 