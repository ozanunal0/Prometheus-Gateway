from abc import ABC, abstractmethod

from app.models import ChatCompletionRequest


class LLMProvider(ABC):
    """
    Abstract base class defining the interface for all LLM providers.
    
    This class establishes a common contract that all concrete LLM provider 
    implementations must follow. It ensures consistency and interchangeability
    across different LLM services (OpenAI, Anthropic, etc.).
    """
    
    @abstractmethod
    async def create_completion(self, request: ChatCompletionRequest) -> dict:
        """
        Create a chat completion using the provider's API.
        
        This method takes a standardized ChatCompletionRequest and returns
        the provider's JSON response. Each concrete provider implementation
        will handle the specifics of their respective API calls.
        
        Args:
            request: The chat completion request containing model, messages, and options.
            
        Returns:
            dict: The JSON response from the LLM provider's API.
            
        Raises:
            NotImplementedError: If the concrete provider doesn't implement this method.
        """
        pass 