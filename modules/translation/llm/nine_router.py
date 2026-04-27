from typing import Any
from .gpt import GPTTranslation


class NineRouterTranslation(GPTTranslation):
    """Translation engine using 9Router API."""
    
    def __init__(self):
        super().__init__()
    
    def initialize(self, settings: Any, source_lang: str, target_lang: str, model_name: str = None, platform: str = None, **kwargs) -> None:
        """
        Initialize 9Router translation engine.
        
        Args:
            settings: Settings object with credentials
            source_lang: Source language name
            target_lang: Target language name
        """
        # Call BaseLLMTranslation's initialize
        super(GPTTranslation, self).initialize(settings, source_lang, target_lang, **kwargs)
        
        # Get 9Router credentials
        credentials = settings.get_credentials(platform or "9Router")
        self.api_key = credentials.get('api_key', '')
        self.model = model_name or credentials.get('selected_model', '')
        
        # Override the API base URL with the custom one
        api_url = credentials.get('api_url', '')
        if api_url:
            self.api_base_url = api_url.rstrip('/')
        else:
            self.api_base_url = "http://localhost:20128/v1"

    def _make_api_request(self, payload, headers):
        if not self.api_key and "Authorization" in headers:
            del headers["Authorization"]
        return super()._make_api_request(payload, headers)
