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
    @staticmethod
    def fetch_official_models(api_key: str) -> List[str]:
        # The official API uses virtual model names. 
        # These are extracted from the original project's supported translators.
        return [
            "Gemini-3.0-Flash",
            "Gemini-2.5-Pro",
            "GPT-4.1",
            "GPT-4.1-mini",
            "Claude-4.6-Sonnet",
            "Claude-4.5-Haiku",
            "Deepseek-v3",
            "Deepseek-R1"
        ]

    @staticmethod
    def fetch_9router_models(base_url: str, api_key: str) -> List[str]:
        try:
            url = base_url.rstrip('/') if base_url else "http://localhost:20128/v1"
            url = f"{url}/models"
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [m['id'] for m in data.get('data', [])]
            return sorted(models)
        except Exception as e:
            print(f"Error fetching 9Router models: {e}")
            return []

    @staticmethod
    def fetch_ollama_models(base_url: str) -> List[str]:
        """Fetch models from local Ollama instance."""
        try:
            # Try to use the base URL if provided, otherwise default to localhost
            url = base_url.rstrip('/') if base_url else "http://localhost:11434"
            # Ollama tags endpoint
            response = requests.get(f"{url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            return sorted(models)
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []
