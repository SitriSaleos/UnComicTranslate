from typing import Any
import numpy as np
import requests
import json

from .base import BaseLLMTranslation
from ...utils.translator_utils import MODEL_MAP


class GPTTranslation(BaseLLMTranslation):
    """Translation engine using OpenAI GPT models through direct REST API calls."""
    
    def __init__(self):
        super().__init__()
        self.model_name = None
        self.api_key = None
        self.api_base_url = "https://api.openai.com/v1"
        self.supports_images = True
    
    def initialize(self, settings: Any, source_lang: str, target_lang: str, model_name: str = None, platform: str = None, **kwargs) -> None:
        """
        Initialize GPT translation engine.
        
        Args:
            settings: Settings object with credentials
            source_lang: Source language name
            target_lang: Target language name
            model_name: Optional specific model name
        """
        super().initialize(settings, source_lang, target_lang, **kwargs)
        
        self.model_name = model_name or "gpt-4o"
        credentials = settings.get_credentials(platform or settings.ui.tr('Open AI GPT'))
        self.api_key = credentials.get('api_key', '')
        self.model = MODEL_MAP.get(self.model_name, self.model_name)
    
    def _perform_translation(self, user_prompt: str, system_prompt: str, image: np.ndarray) -> str:
        """
        Perform translation using direct REST API calls to OpenAI.
        
        Args:
            user_prompt: Text prompt from user
            system_prompt: System instructions
            image: Image as numpy array
            
        Returns:
            Translated text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        if self.supports_images and self.img_as_llm_input:
            # Use the base class method to encode the image
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
            "max_completion_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        return self._make_api_request(payload, headers)
    
    def _make_api_request(self, payload, headers):
        """
        Make API request and process response
        """
        try:
            response = requests.post(
                f"{self.api_base_url}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            response.raise_for_status()
            
            # Force utf-8 encoding to prevent Unicode errors (e.g., mojibake) 
            # when headers don't specify charset=utf-8
            response.encoding = 'utf-8'
            
            # Check if the response is a streaming SSE response
            text_response = response.text.strip()
            if text_response.startswith("data:"):
                full_content = ""
                for line in text_response.splitlines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    full_content += delta["content"]
                        except Exception:
                            pass
                return full_content
            
            try:
                response_data = response.json()
            except Exception as e:
                error_msg = f"API returned non-JSON response. Status: {response.status_code}, Response: {response.text}"
                raise RuntimeError(error_msg)
            
            return response_data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - {json.dumps(error_details)}"
                except:
                    error_msg += f" - Status code: {e.response.status_code}, Response: {e.response.text}"
            raise RuntimeError(error_msg)