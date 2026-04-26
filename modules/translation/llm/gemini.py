from typing import Any
import numpy as np
import requests
import os
import tempfile
import asyncio
import imkit as imk

from .base import BaseLLMTranslation
from ...utils.translator_utils import MODEL_MAP


class GeminiTranslation(BaseLLMTranslation):
    """Translation engine using Google Gemini models via official API."""
    
    def __init__(self):
        super().__init__()
        self.model_name = None
        self.api_key = None
        self.api_base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def initialize(self, settings: Any, source_lang: str, target_lang: str, model_name: str = None, platform: str = None, **kwargs) -> None:
        super().initialize(settings, source_lang, target_lang, **kwargs)
        
        self.model_name = model_name or "gemini-2.0-flash"
        credentials = settings.get_credentials(platform or "Google Gemini")
        
        self.api_key = credentials.get('api_key', '')
        # If it's a known mapped model name, use the API name, otherwise use it directly
        self.model_api_name = MODEL_MAP.get(self.model_name, self.model_name)
    
    def _perform_translation(self, user_prompt: str, system_prompt: str, image: np.ndarray) -> str:
        return self._perform_translation_api(user_prompt, system_prompt, image)

    def _perform_translation_api(self, user_prompt: str, system_prompt: str, image: np.ndarray) -> str:
        url = f"{self.api_base_url}/{self.model_api_name}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": user_prompt}]
            }],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            }
        }
        
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        
        max_retries = 3
        retry_delay = 15  # seconds

        for attempt in range(max_retries + 1):
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                candidates = response_data.get("candidates", [])
                if not candidates:
                    return "No response"
                
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                return "".join(p.get("text", "") for p in parts)
            
            elif response.status_code == 429:
                if attempt < max_retries:
                    print(f"[Gemini API] Quota exceeded. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise Exception(f"API Error 429: Quota exhausted after {max_retries} retries. Please wait a minute or change the model.")
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        return "No response"