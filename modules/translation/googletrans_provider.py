from typing import Any

from .base import TraditionalTranslation
from ..utils.textblock import TextBlock


class GoogletransTranslation(TraditionalTranslation):
    """Translation engine using the unofficial googletrans library (scraper)."""
    
    def __init__(self):
        self.source_lang_code = None
        self.target_lang_code = None
        self.translator = None
        
    def initialize(self, settings: Any, source_lang: str, target_lang: str) -> None:
        """
        Initialize Googletrans engine.
        
        Args:
            settings: Settings object (ignored)
            source_lang: Source language name
            target_lang: Target language name
        """
        self.source_lang_code = self.get_language_code(source_lang)
        self.target_lang_code = self.get_language_code(target_lang)
        import googletrans
        self.translator = googletrans.Translator()
        
    def translate(self, blk_list: list[TextBlock]) -> list[TextBlock]:
        if not blk_list:
            return blk_list
            
        texts = [self.preprocess_text(blk.text, self.source_lang_code) for blk in blk_list]
        
        # Filter out empty texts to avoid API issues, but keep track of indices
        valid_indices = [i for i, text in enumerate(texts) if text.strip()]
        valid_texts = [texts[i] for i in valid_indices]
        
        if not valid_texts:
            for blk in blk_list:
                blk.translation = ''
            return blk_list

        try:
            # googletrans supports translating a list of strings
            translations = self.translator.translate(valid_texts, dest=self.target_lang_code)
            
            # Map back to original list
            for i, translation in zip(valid_indices, translations):
                blk_list[i].translation = translation.text
                
            # Set empty for non-valid indices
            all_valid_indices = set(valid_indices)
            for i in range(len(blk_list)):
                if i not in all_valid_indices:
                    blk_list[i].translation = ''
                    
        except Exception as e:
            print(f"Googletrans translation error: {e}")
            # Fallback to empty translations on error
            for blk in blk_list:
                if not hasattr(blk, 'translation') or blk.translation is None:
                    blk.translation = ''
            
        return blk_list
