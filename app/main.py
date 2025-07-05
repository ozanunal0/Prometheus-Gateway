import httpx
from fastapi import FastAPI, HTTPException

from app.models import ChatCompletionRequest
from app.services import forward_request_to_openai

app = FastAPI()


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> dict:
    """
    Forward chat completion requests to OpenAI API.
    
    This endpoint receives chat completion requests, validates them using Pydantic models,
    and forwards them to the OpenAI API while handling errors gracefully.
    
    Args:
        request: The chat completion request containing model, messages, and options.
        
    Returns:
        dict: The JSON response from OpenAI API containing the chat completion.
        
    Raises:
        HTTPException: If the OpenAI API returns an error or if there's a network issue.
    """
    try:
        result = await forward_request_to_openai(request=request)
        return result
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.json()
        )

 