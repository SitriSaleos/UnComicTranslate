from typing import Any
from .gpt import GPTTranslation


class OllamaTranslation(GPTTranslation):
    """Translation engine using Ollama with OpenAI-compatible API."""
    
    def __init__(self):
        super().__init__()
        self.api_base_url = "http://localhost:11434/v1"
        self.supports_images = False
    
    def initialize(self, settings: Any, source_lang: str, target_lang: str, model_name: str = None, platform: str = None, **kwargs) -> None:
        """
        Initialize Ollama translation engine.
        
        Args:
            settings: Settings object with credentials
            source_lang: Source language name
            target_lang: Target language name
        """
        # Call BaseLLMTranslation's initialize (which is GPTTranslation's grandparent)
        super(GPTTranslation, self).initialize(settings, source_lang, target_lang, **kwargs)
        
        # Get Ollama credentials
        credentials = settings.get_credentials(platform or "Ollama")
        self.api_key = credentials.get('api_key', 'ollama')  # Ollama usually doesn't need a key
        self.model = model_name or credentials.get('selected_model', 'llama3')
        
        # Override the API base URL if provided
        custom_url = credentials.get('api_url', '').rstrip('/')
        if custom_url:
            self.api_base_url = custom_url
        
        # Ensure it ends with /v1 if not present, as we inherit from GPTTranslation which expects OpenAI format
        if not self.api_base_url.endswith('/v1'):
            # If it ends with /v1/, it was already rstripped to /v1
            # If it's just the base URL, append /v1
            self.api_base_url = f"{self.api_base_url}/v1"
