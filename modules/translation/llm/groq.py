from typing import Any
import numpy as np
from .gpt import GPTTranslation


class GroqTranslation(GPTTranslation):
    """Translation engine using Groq models through OpenAI-compatible REST API calls."""
    
    def __init__(self):
        super().__init__()
        self.api_base_url = "https://api.groq.com/openai/v1"
        self.supports_images = False  # Groq vision support is limited/experimental in API
    
    def initialize(self, settings: Any, source_lang: str, target_lang: str, model_name: str = None, platform: str = None, **kwargs) -> None:
        """
        Initialize Groq translation engine.
        """
        # We pass 'Groq' as the platform name to get_credentials
        super().initialize(settings, source_lang, target_lang, model_name, platform='Groq', **kwargs)
        
        if not model_name:
            self.model = "llama-3.3-70b-versatile"
