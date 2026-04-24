import requests
import time
from .base import TranslationEngine
from modules.utils.textblock import TextBlock

class DeeLXTranslation(TranslationEngine):
    """DeeLX translation engine using self-hosted DeeLX instances."""
    
    def __init__(self):
        super().__init__()
        self.url = None
        self.self_hosted = False
        self.lang_map = {
            'English': 'EN',
            '한국어': 'KO',
            'Français': 'FR',
            '日本語': 'JA',
            '简体中文': 'ZH',
            '繁體中文': 'ZH',
            'русский': 'RU',
            'Deutsch': 'DE',
            'Nederlands': 'NL',
            'Español': 'ES',
            'Italiano': 'IT',
            'Türkçe': 'TR'
        }

    def initialize(self, settings, source_lang: str, target_lang: str, **kwargs) -> None:
        super().initialize(settings, source_lang, target_lang)
        credentials = settings.get_credentials("DeeLX")
        self.url = credentials.get('url', '')
        self.self_hosted = credentials.get('self_hosted', False)

    def translate(self, blk_list: list[TextBlock]) -> list[TextBlock]:
        source_code = self.lang_map.get(self.source_lang, "auto")
        target_code = self.lang_map.get(self.target_lang, "EN")
        
        # Filter blocks with text
        valid_blks = [blk for blk in blk_list if blk.text and blk.text.strip()]
        if not valid_blks:
            return blk_list
            
        if not self.self_hosted or not self.url:
            print("[DeeLX Error] DeeLX is not configured or URL is missing.")
            return blk_list
            
        try:
            # Batch strategy: Combine all texts with a unique separator to avoid 503/429 errors
            separator = "\n<||>\n"
            combined_text = separator.join([blk.text for blk in valid_blks])
            
            payload = {
                "text": combined_text,
                "source_lang": source_code,
                "target_lang": target_code
            }
            
            response = requests.post(self.url, json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                translated_combined = ""
                if "data" in data:
                    translated_combined = data["data"]
                elif "text" in data:
                    translated_combined = data["text"]
                else:
                    translated_combined = str(data)
                
                # Split back
                translated_parts = translated_combined.split(separator.strip())
                translated_parts = [p.strip() for p in translated_parts if p.strip()]
                
                if len(translated_parts) == len(valid_blks):
                    for blk, trans in zip(valid_blks, translated_parts):
                        blk.translation = trans
                else:
                    # Fallback
                    for blk in valid_blks:
                        single_payload = {"text": blk.text, "source_lang": source_code, "target_lang": target_code}
                        res = requests.post(self.url, json=single_payload, timeout=10)
                        if res.status_code == 200:
                            blk.translation = res.json().get("data") or res.json().get("text")
                        time.sleep(0.5)
            elif response.status_code == 503:
                print("[DeeLX Error] 503: Service Unavailable.")
            elif response.status_code == 429:
                print("[DeeLX Error] 429: Too Many Requests.")
            else:
                print(f"[DeeLX Error] API returned status {response.status_code}")
                
        except Exception as e:
            print(f"[DeeLX Error] {str(e)}")
                
        return blk_list
