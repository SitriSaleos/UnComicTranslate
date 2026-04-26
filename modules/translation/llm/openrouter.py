from typing import Any
import numpy as np
import requests
import json

from .base import BaseLLMTranslation


class OpenRouterTranslation(BaseLLMTranslation):
    """Translation engine using OpenRouter models."""
    
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.api_base_url = "https://openrouter.ai/api/v1"
        self.supports_images = True
    
    def initialize(self, settings: Any, source_lang: str, target_lang: str, model_name: str = None, platform: str = None, **kwargs) -> None:
        """
        Initialize OpenRouter translation engine.
        
        Args:
            settings: Settings object with credentials
            source_lang: Source language name
            target_lang: Target language name
            model_name: Optional model name
        """
        super().initialize(settings, source_lang, target_lang, **kwargs)
        
        credentials = settings.get_credentials(platform or 'OpenRouter')
        self.api_key = credentials.get('api_key', '')
        
        # Priority: model_name from argument, then selected_model from credentials, then manual model field, then fallback
        self.model = model_name or credentials.get('selected_model') or credentials.get('model') or "google/gemini-2.0-flash-001"
    
    def _perform_translation(self, user_prompt: str, system_prompt: str, image: np.ndarray) -> str:
        """
        Perform translation using direct REST API calls to OpenRouter.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/SitriSaleos/UnComicTranslate",
            "X-Title": "UnComicTranslate"
        }
        
        if self.supports_images and self.img_as_llm_input:
            encoded_image, mime_type = self.encode_image(image)
            
            messages = [
                {
                    "role": "system", 
                    "content": [{"type": "text", "text": system_prompt}]
                },
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}}
                    ]
                }
            ]
        else:
            messages = [
                {
                    "role": "system", 
                    "content": [{"type": "text", "text": system_prompt}]
                },
                {
                    "role": "user", 
                    "content": [{"type": "text", "text": user_prompt}]
                }
            ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        return self._make_api_request(payload, headers)
    
    def _make_api_request(self, payload, headers):
        try:
            response = requests.post(
                f"{self.api_base_url}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            else:
                raise RuntimeError(f"Unexpected response format: {json.dumps(response_data)}")
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - {json.dumps(error_details)}"
                except:
                    error_msg += f" - Status code: {e.response.status_code}"
            raise RuntimeError(error_msg)
