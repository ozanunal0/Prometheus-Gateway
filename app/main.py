import time
import httpx
from fastapi import FastAPI, HTTPException, Depends, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.models import ChatCompletionRequest
from app.db_models.api_key import APIKey
from app.services import process_chat_completion
from app.database import create_db_and_tables
from app.dependencies import get_valid_api_key
from app.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from app.middleware.dlp_middleware import DlpMiddleware
from app.metrics import REQUESTS_TOTAL, REQUEST_LATENCY_SECONDS, TOKENS_USED_TOTAL

app = FastAPI()

# Add DLP middleware for PII detection and anonymization (first in chain)
app.add_middleware(DlpMiddleware)

# Add SlowAPI middleware for rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Add Prometheus metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Expose Prometheus metrics endpoint."""
    from starlette.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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
    All requests are instrumented with Prometheus metrics for observability.
    
    Args:
        request: The HTTP request object (required for rate limiting).
        payload: The chat completion request containing model, messages, and options.
        api_key: The authenticated API key (injected by dependency).
        
    Returns:
        dict: The JSON response from the selected LLM provider.
        
    Raises:
        HTTPException: If no provider is found for the model, or if the provider's API returns an error.
    """
    # Start timing the request for latency metrics
    start_time = time.time()
    
    # Extract labels for metrics
    owner = api_key.owner
    model = payload.model
    status_code = 200  # Default to success, will be updated on error
    
    try:
        result = await process_chat_completion(request=payload)
        
        # Record token usage metrics from the LLM response
        if 'usage' in result:
            usage = result['usage']
            
            # Record prompt tokens
            if 'prompt_tokens' in usage:
                TOKENS_USED_TOTAL.labels(
                    owner=owner,
                    model=model,
                    token_type='prompt'
                ).inc(usage['prompt_tokens'])
            
            # Record completion tokens
            if 'completion_tokens' in usage:
                TOKENS_USED_TOTAL.labels(
                    owner=owner,
                    model=model,
                    token_type='completion'
                ).inc(usage['completion_tokens'])
            
            # Record total tokens
            if 'total_tokens' in usage:
                TOKENS_USED_TOTAL.labels(
                    owner=owner,
                    model=model,
                    token_type='total'
                ).inc(usage['total_tokens'])
        
        return result
        
    except ValueError as exc:
        status_code = 400
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.json()
        )
    except Exception as exc:
        status_code = 500
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    finally:
        # Always record latency and request count, regardless of success/failure
        duration = time.time() - start_time
        
        # Record request latency
        REQUEST_LATENCY_SECONDS.labels(
            owner=owner,
            model=model
        ).observe(duration)
        
        # Record request count with status code
        REQUESTS_TOTAL.labels(
            owner=owner,
            model=model,
            status_code=str(status_code)
        ).inc()

 