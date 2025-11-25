"""
🌙 Moon Dev's Groq Model Implementation
Built with love by Moon Dev 🚀
"""

from groq import Groq
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
from .base_model import BaseModel, ModelResponse
import time

class GroqModel(BaseModel):
    """Implementation for Groq's models"""
    
    AVAILABLE_MODELS = {
        # Production Models (Actually Available on GROQ)
        "llama-3.3-70b-versatile": {
            "description": "Llama 3.3 70B Versatile - Production - 128k context",
            "input_price": "$0.70/1M tokens",
            "output_price": "$0.90/1M tokens"
        },
        "llama-3.1-8b-instant": {
            "description": "Llama 3.1 8B Instant - Production - 128k context",
            "input_price": "$0.10/1M tokens",
            "output_price": "$0.10/1M tokens"
        },
        "qwen/qwen3-32b": {
            "description": "Qwen 3 32B - Production - 32k context",
            "input_price": "$0.50/1M tokens",
            "output_price": "$0.50/1M tokens"
        },
        # New GROQ Models (2025)
        "groq/compound-mini": {
            "description": "GROQ Compound Mini - Production - Fast",
            "input_price": "$0.10/1M tokens",
            "output_price": "$0.10/1M tokens"
        },
        "groq/compound": {
            "description": "GROQ Compound - Production - Fast",
            "input_price": "$0.20/1M tokens",
            "output_price": "$0.20/1M tokens"
        }
    }

    def __init__(self, api_key: str, model_name: str = "qwen/qwen3-32b", **kwargs):
        try:
            cprint(f"\n[GROQ] Moon Dev's Groq Model Initialization", "cyan")

            # Validate API key
            if not api_key or len(api_key.strip()) == 0:
                raise ValueError("API key is empty or None")

            cprint(f"[KEY] API Key validation:", "cyan")
            cprint(f"  - Length: {len(api_key)} chars", "cyan")
            cprint(f"  - Contains whitespace: {'yes' if any(c.isspace() for c in api_key) else 'no'}", "cyan")
            cprint(f"  - Starts with 'gsk_': {'yes' if api_key.startswith('gsk_') else 'no'}", "cyan")

            # Validate model name
            cprint(f"\n[MODEL] Model validation:", "cyan")
            cprint(f"  - Requested: {model_name}", "cyan")
            if model_name not in self.AVAILABLE_MODELS:
                cprint(f"  - [X] Invalid model name", "red")
                cprint("\nAvailable models:", "yellow")
                for available_model, info in self.AVAILABLE_MODELS.items():
                    cprint(f"  - {available_model}", "yellow")
                    cprint(f"    - {info['description']}", "yellow")
                raise ValueError(f"Invalid model name: {model_name}")
            cprint(f"  - [OK] Model name valid", "green")

            self.model_name = model_name
            self.max_tokens = kwargs.get('max_tokens', 4000)  # Default 4000 tokens

            # Call parent class initialization
            cprint(f"\n[INIT] Parent class initialization...", "cyan")
            super().__init__(api_key, **kwargs)
            cprint(f"[OK] Parent class initialized", "green")

        except Exception as e:
            cprint(f"\n[ERROR] Error in Groq model initialization", "red")
            cprint(f"  - Error type: {type(e).__name__}", "red")
            cprint(f"  - Error message: {str(e)}", "red")
            if "api_key" in str(e).lower():
                cprint(f"  - [KEY] This appears to be an API key issue", "red")
                cprint(f"  - Please check your GROQ_API_KEY in .env", "red")
            elif "model" in str(e).lower():
                cprint(f"  - [MODEL] This appears to be a model name issue", "red")
                cprint(f"  - Available models: {list(self.AVAILABLE_MODELS.keys())}", "red")
            raise
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the Groq client"""
        try:
            cprint(f"\n[INIT] Initializing Groq client...", "cyan")
            cprint(f"  - API Key length: {len(self.api_key)} chars", "cyan")
            cprint(f"  - Model name: {self.model_name}", "cyan")

            cprint(f"\n  - Creating Groq client...", "cyan")
            self.client = Groq(api_key=self.api_key)
            cprint(f"  - [OK] Groq client created", "green")

            # Get list of available models first
            cprint(f"  - Fetching available models from Groq API...", "cyan")
            available_models = self.client.models.list()
            api_models = [model.id for model in available_models.data]
            cprint(f"  - Models available from API: {api_models}", "cyan")

            if self.model_name not in api_models:
                cprint(f"  - [WARN] Requested model not found in API", "yellow")
                cprint(f"  - Falling back to mixtral-8x7b-32768", "yellow")
                self.model_name = "mixtral-8x7b-32768"

            # Test the connection with a simple completion
            cprint(f"  - Testing connection with model: {self.model_name}", "cyan")
            test_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            cprint(f"  - [OK] Test response received", "green")
            cprint(f"  - Response content: {test_response.choices[0].message.content}", "cyan")

            model_info = self.AVAILABLE_MODELS.get(self.model_name, {})
            cprint(f"  - [OK] Groq model initialized: {self.model_name}", "green")
            cprint(f"  - Model info: {model_info.get('description', '')}", "cyan")
            cprint(f"  - Pricing: Input {model_info.get('input_price', '')} | Output {model_info.get('output_price', '')}", "yellow")

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__

            # Check if this is a server error (500, 502, 503, 504)
            is_server_error = (
                'InternalServerError' in error_type or
                '500' in error_msg or
                '502' in error_msg or
                '503' in error_msg or
                'cloudflare' in error_msg.lower() or
                'internal server error' in error_msg.lower()
            )

            if is_server_error:
                cprint(f"\n[WARN] Groq API server temporarily unavailable", "yellow")
                cprint(f"  - This is an external infrastructure issue (not your code)", "yellow")
                cprint(f"  - Error type: {error_type}", "yellow")
                cprint(f"  - System will continue with other working AI models", "yellow")
                self.client = None
                # DO NOT raise - allow system to continue with other models
                return

            # For non-server errors, show detailed debug info and raise
            cprint(f"\n[ERROR] Failed to initialize Groq client", "red")
            cprint(f"  - Error type: {error_type}", "red")
            cprint(f"  - Error message: {error_msg[:500]}", "red")  # Truncate long HTML errors

            # Check for specific error types
            if "api_key" in error_msg.lower():
                cprint(f"  - [KEY] This appears to be an API key issue", "red")
                cprint(f"  - Make sure your GROQ_API_KEY is correct", "red")
                cprint(f"  - Key length: {len(self.api_key)} chars", "red")
            elif "model" in error_msg.lower():
                cprint(f"  - [MODEL] This appears to be a model name issue", "red")
                cprint(f"  - Requested model: {self.model_name}", "red")
                cprint(f"  - Available models: {list(self.AVAILABLE_MODELS.keys())}", "red")

            self.client = None
            raise
    
    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None):
        """Generate response with no caching"""
        try:
            # Force unique request every time
            timestamp = int(time.time() * 1000)  # Millisecond precision

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_content}_{timestamp}"}  # Make each request unique
                ],
                temperature=temperature,
                max_tokens=max_tokens if max_tokens else self.max_tokens,
                stream=False  # Disable streaming to prevent caching
            )

            # Extract content and filter out thinking tags
            raw_content = response.choices[0].message.content

            # Remove <think>...</think> tags and their content (Qwen reasoning)
            import re

            # First, try to remove complete <think>...</think> blocks
            filtered_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()

            # If <think> tag exists but wasn't removed (unclosed tag due to token limit),
            # remove everything from <think> onwards
            if '<think>' in filtered_content:
                filtered_content = filtered_content.split('<think>')[0].strip()

            # If filtering removed everything, return the original (in case it's not a Qwen model)
            final_content = filtered_content if filtered_content else raw_content

            return ModelResponse(
                content=final_content,
                raw_response=response,
                model_name=self.model_name,
                usage=response.usage
            )

        except Exception as e:
            error_str = str(e)
            error_type = type(e).__name__

            # Handle server errors (500, 502, 503, 504) - EXTERNAL INFRASTRUCTURE ISSUES
            is_server_error = (
                'InternalServerError' in error_type or
                '500' in error_str or
                '502' in error_str or
                '503' in error_str or
                '504' in error_str or
                'cloudflare' in error_str.lower() or
                'internal server error' in error_str.lower()
            )

            if is_server_error:
                cprint(f"⚠️  Groq API server temporarily unavailable (external issue)", "yellow")
                cprint(f"   Continuing with other working models...", "cyan")
                return None

            # Handle rate limit errors (413)
            if "413" in error_str or "rate_limit_exceeded" in error_str:
                cprint(f"⚠️  Groq rate limit exceeded (request too large)", "yellow")
                cprint(f"   Model: {self.model_name}", "yellow")
                if "Requested" in error_str and "Limit" in error_str:
                    # Extract token info from error message
                    import re
                    limit_match = re.search(r'Limit (\d+)', error_str)
                    requested_match = re.search(r'Requested (\d+)', error_str)
                    if limit_match and requested_match:
                        cprint(f"   Limit: {limit_match.group(1)} tokens | Requested: {requested_match.group(1)} tokens", "yellow")
                cprint(f"   💡 Skipping this model for this request...", "cyan")
                return None

            # Log other errors (actual code/config issues)
            cprint(f"❌ Groq error: {error_str[:200]}", "red")
            return None
    
    def is_available(self) -> bool:
        """Check if Groq is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "groq" 