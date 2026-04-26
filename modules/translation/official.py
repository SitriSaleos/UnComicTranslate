import requests
import base64
import numpy as np
import logging
import time
from typing import List, Optional, Any

from .base import LLMTranslation
from ..utils.textblock import TextBlock
from app.account.config import WEB_API_TRANSLATE_URL
from ..utils.platform_utils import get_client_os
from app.account.auth.token_storage import get_token

logger = logging.getLogger(__name__)

OFFICIAL_MODEL_MAP = {
    "Custom": "",  
    "Deepseek-v3": "deepseek-chat", 
    "Deepseek-R1": "deepseek-reasoner",
    "GPT-4.1": "gpt-4.1",
    "GPT-4.1-mini": "gpt-4.1-mini",
    "Claude-4.6-Sonnet": "claude-sonnet-4-6",
    "Claude-4.5-Haiku": "claude-haiku-4-5-20251001",
    "Gemini-2.0-Flash": "gemini-2.0-flash",
    "Gemini-3.0-Flash": "gemini-3-flash-preview",
    "Gemini-2.5-Pro": "gemini-2.5-pro"
}

class OfficialTranslation(LLMTranslation):
    """
    Translation engine that proxies requests to the official Comic Translate web API,
    utilizing the user's access token (API Key).
    """

    def __init__(self):
        self.api_url = WEB_API_TRANSLATE_URL
        self.source_lang: str = None
        self.target_lang: str = None
        self.model_name: str = None
        self.api_key: str = None
        self._session = requests.Session()

    def initialize(self, settings: Any, source_lang: str, target_lang: str, **kwargs) -> None:
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Priority: kwargs > settings > default
        self.model_name = kwargs.get('model_name')
        if not self.model_name:
            creds = settings.get_credentials("Comic Translate (Official)")
            self.model_name = creds.get('selected_model') if creds else None
            
        if not self.model_name:
            self.model_name = "Gemini-3.0-Flash" # Default fallback
        
        # Get API key from credentials
        creds = settings.get_credentials("Comic Translate (Official)")
        self.api_key = creds.get('api_key') if creds else None
        
        # Fallback to global access token if not set specifically
        if not self.api_key:
            self.api_key = get_token("access_token")

    def translate(self, blk_list: List[TextBlock], image: np.ndarray = None, extra_context: str = "") -> List[TextBlock]:
        if not self.api_key:
            logger.error("OfficialTranslation: No API Key (Access Token) provided.")
            for blk in blk_list:
                blk.translation = "Error: No API Key provided in settings."
            return blk_list

        logger.info(f"OfficialTranslation: Translating via official API for model {self.model_name}")

        # Prepare Request Body
        texts_payload = []
        for i, blk in enumerate(blk_list):
            block_id = getattr(blk, 'id', i)
            texts_payload.append({"id": block_id, "text": blk.text})

        # Handle Image Encoding
        image_base64_payload = None
        if image is not None:
            import cv2
            _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            image_base64_payload = base64.b64encode(buffer).decode('utf-8')

        # Construct Full Payload
        request_payload = {
            "translator": OFFICIAL_MODEL_MAP.get(self.model_name, self.model_name),
            "source_language": self.source_lang,
            "target_language": self.target_lang,
            "texts": texts_payload,
        }

        if image_base64_payload is not None:
            request_payload["image_base64"] = image_base64_payload
            request_payload["llm_options"] = {"image_input_enabled": True}
        
        if extra_context:
            request_payload["extra_context"] = extra_context

        # Make the HTTP Request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Client-OS": get_client_os()
        }

        try:
            response = self._session.post(
                self.api_url, 
                headers=headers, 
                json=request_payload, 
                timeout=120
            ) 
            
            if response.status_code != 200:
                try:
                    error_detail = response.json()
                    logger.error(f"OfficialTranslation: API Error {response.status_code}: {error_detail}")
                except Exception:
                    logger.error(f"OfficialTranslation: API Error {response.status_code}: {response.text}")
            
            response.raise_for_status()
            
            response_data = response.json()
            translations_map = {item['id']: item['translation'] for item in response_data.get('translations', [])}

            # Update TextBlock objects
            for i, blk in enumerate(blk_list):
                block_id = getattr(blk, 'id', i)
                blk.translation = translations_map.get(block_id, "")

        except Exception as e:
            logger.error(f"OfficialTranslation: Request failed: {e}")
            for blk in blk_list:
                blk.translation = f"Error: {str(e)}"

        return blk_list
