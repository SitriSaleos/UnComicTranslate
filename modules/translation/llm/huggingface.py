from typing import Any
from .gpt import GPTTranslation


class HuggingFaceTranslation(GPTTranslation):
    """Translation engine using Hugging Face models through OpenAI-compatible REST API calls."""
    
    def __init__(self):
        super().__init__()
        # Hugging Face OpenAI-compatible router
        self.api_base_url = "https://router.huggingface.co/v1"
        self.supports_images = False
    
    def initialize(self, settings: Any, source_lang: str, target_lang: str, model_name: str = None, platform: str = None, **kwargs) -> None:
        """
        Initialize Hugging Face translation engine.
        """
        # Always use 'HuggingFace' as the platform key to match settings
        super().initialize(settings, source_lang, target_lang, model_name, platform='HuggingFace', **kwargs)
        
        # If model_name was provided by the factory, it will be in self.model
        # but we ensure a default if it's empty
        if not self.model:
            credentials = settings.get_credentials('HuggingFace')
            self.model = credentials.get('selected_model') or "meta-llama/Llama-3.3-70B-Instruct"
