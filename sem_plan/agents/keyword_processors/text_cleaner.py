from __future__ import annotations

import re
from typing import List

from ...core.types import RawKeyword


class TextCleaner:
    """Cleans and structures collected keywords."""
    
    def __init__(self):
        pass
    
    def clean_and_structure(self, keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Clean and structure the collected keywords."""
        cleaned = []
        
        for kw in keywords:
            # Clean the keyword
            cleaned_text = self._clean_keyword_text(kw.keyword)
            if cleaned_text and len(cleaned_text.split()) <= 6:  # Max 6 words
                kw.keyword = cleaned_text
                cleaned.append(kw)
        
        return cleaned
    
    def _clean_keyword_text(self, text: str) -> str:
        """Clean keyword text."""
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Remove common junk
        junk_patterns = [
            r'\b(click|read|more|learn|here|this|that|these|those)\b',
            r'\b(website|site|page|link|url)\b',
            r'\b(menu|navigation|header|footer)\b'
        ]
        
        for pattern in junk_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Final cleanup
        text = ' '.join(text.split())
        
        return text.lower().strip()
