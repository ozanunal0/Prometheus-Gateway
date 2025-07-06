import json
from typing import Any, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.dlp.dlp_scanner import scrub_text


class DlpMiddleware(BaseHTTPMiddleware):
    """
    Data Loss Prevention (DLP) middleware that automatically detects and anonymizes
    Personally Identifiable Information (PII) in incoming chat completion requests.
    
    This middleware intercepts requests to the chat completions endpoint, scans
    the message content for PII using Microsoft Presidio, and replaces sensitive
    data with placeholder values before forwarding the request to the LLM provider.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request by scanning for PII and anonymizing it before forwarding.
        
        This method handles the complex task of:
        1. Reading the request body without consuming the stream
        2. Parsing JSON and extracting message content
        3. Applying PII detection and anonymization
        4. Reconstructing the request with scrubbed content
        5. Forwarding to the next middleware/handler
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain
            
        Returns:
            Response: The response from the downstream handler
        """
        # Only process POST requests to the chat completions endpoint
        if request.method == "POST" and request.url.path == "/v1/chat/completions":
            try:
                # Read the request body
                body = await request.body()
                
                if body:
                    # Parse the JSON payload
                    try:
                        payload = json.loads(body.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If we can't parse the JSON, pass through unmodified
                        return await call_next(request)
                    
                    # Process messages if they exist
                    if isinstance(payload, dict) and "messages" in payload:
                        messages = payload.get("messages", [])
                        
                        # Scan and scrub each message's content
                        for message in messages:
                            if isinstance(message, dict) and "content" in message:
                                original_content = message["content"]
                                if isinstance(original_content, str):
                                    # Apply DLP scanning and anonymization
                                    scrubbed_content = scrub_text(original_content)
                                    # Log for debugging
                                    if original_content != scrubbed_content:
                                        print(f"DLP: Original: {original_content}")
                                        print(f"DLP: Scrubbed: {scrubbed_content}")
                                    message["content"] = scrubbed_content
                    
                    # Reconstruct the request with the modified payload
                    modified_body = json.dumps(payload).encode('utf-8')
                    
                    # Create a new request with the modified body
                    # We need to handle this carefully to maintain the request stream
                    request._body = modified_body
                    
                    # Update content-length header to match new body size
                    if hasattr(request, "_headers"):
                        # Update headers if accessible
                        request._headers["content-length"] = str(len(modified_body))
                    
            except Exception as e:
                # Log error but don't block the request if DLP fails
                print(f"DLP middleware error: {e}")
                # Continue with original request if DLP processing fails
                pass
        
        # Forward the request to the next handler
        response = await call_next(request)
        return response