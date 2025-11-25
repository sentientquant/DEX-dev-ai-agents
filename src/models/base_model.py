"""
🌙 Moon Dev's Model Interface
Built with love by Moon Dev 🚀

This module defines the base interface for all AI models.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import random
import time
# Make termcolor optional
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text

@dataclass
class ModelResponse:
    """
    Standardized response format for ALL models.
    CRITICAL: All models MUST return this type, not raw strings or message objects.
    This ensures consistent parsing across the entire system.
    """
    content: str                    # ALWAYS a string - the actual response text
    model_name: str                 # Which model generated this
    raw_response: Any = None        # Original response object for debugging
    usage: Optional[Dict] = None    # Token usage stats
    error: Optional[str] = None     # Error message if request failed

    def __str__(self) -> str:
        """String representation returns content for backward compatibility"""
        return self.content
    
class BaseModel(ABC):
    """Base interface for all AI models"""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.client = None
        self.initialize_client(**kwargs)
    
    @abstractmethod
    def initialize_client(self, **kwargs) -> None:
        """Initialize the model's client"""
        pass
    
    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None) -> ModelResponse:
        """
        Generate a response from the model.

        CRITICAL: This method MUST return ModelResponse, not raw response objects.
        All subclasses should override this to ensure ModelResponse is returned.

        Returns:
            ModelResponse: Standardized response object with content, model_name, usage, etc.
        """
        try:
            # Add random nonce to prevent caching
            nonce = f"_{random.randint(1, 1000000)}"
            current_time = int(time.time())

            # Each request will be unique
            unique_content = f"{user_content}_{nonce}_{current_time}"

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": f"{system_prompt}_{current_time}"},
                    {"role": "user", "content": unique_content}
                ],
                temperature=temperature,
                max_tokens=max_tokens if max_tokens else self.max_tokens
            )

            # CRITICAL FIX: Always return ModelResponse, not raw message
            return ModelResponse(
                content=response.choices[0].message.content,
                model_name=self.model_name,
                raw_response=response,
                usage={
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            )

        except Exception as e:
            if "503" in str(e):
                raise e  # Let the retry logic handle 503s
            cprint(f"❌ Model error: {str(e)}", "red")
            # Return error ModelResponse instead of None
            return ModelResponse(
                content="",
                model_name=getattr(self, 'model_name', 'unknown'),
                error=str(e)
            )
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available and properly configured"""
        pass
    
    @property
    @abstractmethod
    def model_type(self) -> str:
        """Return the type/name of the model"""
        pass 