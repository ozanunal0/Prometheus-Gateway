import httpx
from fastapi import FastAPI, HTTPException

from app.models import ChatCompletionRequest
from app.services import process_chat_completion

app = FastAPI()


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> dict:
    """
    Process chat completion requests using the appropriate LLM provider.
    
    This endpoint receives chat completion requests, validates them using Pydantic models,
    and forwards them to the appropriate LLM provider based on the model name.
    
    Args:
        request: The chat completion request containing model, messages, and options.
        
    Returns:
        dict: The JSON response from the selected LLM provider.
        
    Raises:
        HTTPException: If no provider is found for the model, or if the provider's API returns an error.
    """
    try:
        result = await process_chat_completion(request=request)
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

 