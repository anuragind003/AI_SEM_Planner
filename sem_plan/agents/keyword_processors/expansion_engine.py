from __future__ import annotations

from typing import List

from ...core.types import RawKeyword, Config
from ...utils.http import polite_delay


class ExpansionEngine:
    """Expands keywords without using paid APIs."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def expand_keywords(self, keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Expand keywords without paid APIs."""
        expanded = []
        
        for kw in keywords[:20]:  # Limit to avoid too many expansions
            # Google Autocomplete expansion
            expanded.extend(self._expand_with_autocomplete(kw.keyword))
            
            # Related searches expansion
            expanded.extend(self._expand_with_related_searches(kw.keyword))
            
            # Question expansion
            expanded.extend(self._expand_with_questions(kw.keyword))
            
            polite_delay(1.0)
        
        return expanded
    
    def _expand_with_autocomplete(self, keyword: str) -> List[RawKeyword]:
        """Expand keyword with Google Autocomplete."""
        expanded = []
        
        try:
            # Try different suffixes
            suffixes = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]
            
            for suffix in suffixes[:5]:  # Limit expansions
                query = f"{keyword} {suffix}"
                suggestions = self._get_google_autocomplete(query)
                expanded.extend(suggestions)
                
        except Exception as e:
            print(f"Autocomplete expansion failed for {keyword}: {e}")
        
        return expanded
    
    def _expand_with_related_searches(self, keyword: str) -> List[RawKeyword]:
        """Expand keyword with related searches."""
        return self._get_google_related_searches(keyword)
    
    def _expand_with_questions(self, keyword: str) -> List[RawKeyword]:
        """Expand keyword with question patterns."""
        questions = []
        
        question_patterns = [
            f"what is {keyword}",
            f"how to {keyword}",
            f"why {keyword}",
            f"when {keyword}",
            f"where {keyword}",
            f"which {keyword}",
            f"best {keyword}",
            f"{keyword} vs",
            f"{keyword} alternatives",
            f"{keyword} pricing"
        ]
        
        for pattern in question_patterns:
            questions.append(RawKeyword(
                keyword=pattern,
                source="question_expansion",
                seed=keyword
            ))
        
        return questions
    
    def _get_google_autocomplete(self, seed: str) -> List[RawKeyword]:
        """Get Google Autocomplete suggestions."""
        keywords = []
        
        try:
            # Try the unofficial Google Autocomplete API
            import requests
            url = f"http://suggestqueries.google.com/complete/search"
            params = {
                'client': 'firefox',
                'q': seed
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    suggestions = data[1]
                    for suggestion in suggestions:
                        if len(suggestion.split()) >= 2:
                            keywords.append(RawKeyword(
                                keyword=suggestion.lower(),
                                source="google_autocomplete",
                                seed=seed
                            ))
        except Exception as e:
            print(f"Google Autocomplete failed for {seed}: {e}")
        
        return keywords
    
    def _get_google_related_searches(self, seed: str) -> List[RawKeyword]:
        """Get Google Related Searches from SERP."""
        keywords = []
        
        try:
            from bs4 import BeautifulSoup
            from ...utils.http import get
            
            url = f"https://www.google.com/search?q={seed.replace(' ', '+')}&hl=en"
            response = get(url, headers={"Accept": "text/html"})
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for related searches
            for el in soup.select("a[aria-level] span, a[href*='search?q='] span"):
                text = el.get_text(" ", strip=True)
                if text and len(text.split()) >= 2:
                    keywords.append(RawKeyword(
                        keyword=text.lower(),
                        source="google_related",
                        seed=seed
                    ))
                    
        except Exception as e:
            print(f"Google Related Searches failed for {seed}: {e}")
        
        return keywords
