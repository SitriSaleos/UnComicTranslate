import requests
import json
from typing import List

class ModelManager:
    @staticmethod
    def fetch_gemini_models(api_key: str) -> List[str]:
        if not api_key:
            return []
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Filter models that support generateContent
            models = [m['name'].replace('models/', '') for m in data.get('models', []) 
                    if 'generateContent' in m.get('supportedGenerationMethods', [])]
            return sorted(models)
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")
            return []

    @staticmethod
    def fetch_openrouter_models(api_key: str) -> List[str]:
        try:
            url = "https://openrouter.ai/api/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [m['id'] for m in data.get('data', [])]
            return sorted(models)
        except Exception as e:
            print(f"Error fetching OpenRouter models: {e}")
            return []

    @staticmethod
    def fetch_openai_models(api_key: str) -> List[str]:
        if not api_key:
            return []
        try:
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Filter for GPT models
            models = [m['id'] for m in data.get('data', []) if 'gpt' in m['id']]
            return sorted(models)
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
            return []

    @staticmethod
    def fetch_anthropic_models(api_key: str) -> List[str]:
        if not api_key:
            return []
        try:
            # Anthropic now has a models endpoint
            url = "https://api.anthropic.com/v1/models"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [m['id'] for m in data.get('data', [])]
            return sorted(models)
        except Exception as e:
            print(f"Error fetching Anthropic models: {e}")
            # Fallback to common models if API fails
            return ["claude-3-5-sonnet-20240620", "claude-3-haiku-20240307", "claude-3-opus-20240229"]

    @staticmethod
    def fetch_deepseek_models(api_key: str) -> List[str]:
        if not api_key:
            return []
        try:
            url = "https://api.deepseek.com/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [m['id'] for m in data.get('data', [])]
            return sorted(models)
        except Exception as e:
            print(f"Error fetching Deepseek models: {e}")
            return ["deepseek-chat", "deepseek-reasoner"]
