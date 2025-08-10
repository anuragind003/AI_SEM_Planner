from __future__ import annotations

import random
from typing import List
from urllib.parse import urlparse

from ...core.types import RawKeyword, Config


class PublicToolsCollector:
    """Simulates free public keyword tools."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def collect_from_tools(self) -> List[RawKeyword]:
        """Collect keywords from public tools."""
        keywords = []
        
        # Ubersuggest free tier (simulated)
        keywords.extend(self._simulate_ubersuggest())
        
        # AnswerThePublic (simulated)
        keywords.extend(self._simulate_answer_the_public())
        
        # KeywordTool.io (simulated)
        keywords.extend(self._simulate_keyword_tool())
        
        return keywords
    
    def _simulate_ubersuggest(self) -> List[RawKeyword]:
        """Simulate Ubersuggest free tier results."""
        keywords = []
        
        # Generate some common keyword patterns
        base_terms = self._get_seed_terms()
        
        for term in base_terms[:3]:  # Limit to avoid overuse
            # Add common modifiers
            modifiers = ["best", "top", "free", "online", "software", "tool", "platform"]
            for modifier in modifiers:
                keyword = f"{modifier} {term}"
                keywords.append(RawKeyword(
                    keyword=keyword,
                    source="ubersuggest",
                    volume=random.randint(100, 5000)
                ))
        
        return keywords
    
    def _simulate_answer_the_public(self) -> List[RawKeyword]:
        """Simulate AnswerThePublic question phrases."""
        keywords = []
        
        base_terms = self._get_seed_terms()
        
        for term in base_terms[:2]:
            # Add question patterns
            questions = [
                f"what is {term}",
                f"how to use {term}",
                f"why use {term}",
                f"when to use {term}",
                f"where to find {term}",
                f"which {term} is best"
            ]
            
            for question in questions:
                keywords.append(RawKeyword(
                    keyword=question,
                    source="answer_the_public",
                    volume=random.randint(50, 2000)
                ))
        
        return keywords
    
    def _simulate_keyword_tool(self) -> List[RawKeyword]:
        """Simulate KeywordTool.io autocomplete expansion."""
        keywords = []
        
        base_terms = self._get_seed_terms()
        
        for term in base_terms[:2]:
            # Add autocomplete patterns
            suffixes = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", 
                       "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
            
            for suffix in suffixes[:10]:  # Limit to avoid too many
                keyword = f"{term} {suffix}"
                keywords.append(RawKeyword(
                    keyword=keyword,
                    source="keyword_tool",
                    volume=random.randint(10, 500)
                ))
        
        return keywords
    
    def _get_seed_terms(self) -> List[str]:
        """Get seed terms from brand and competitors."""
        seeds = []
        
        # Extract terms from URLs
        brand_terms = self._extract_terms_from_url(self.config.brand_url)
        seeds.extend(brand_terms)
        
        for comp_url in self.config.competitor_urls:
            comp_terms = self._extract_terms_from_url(comp_url)
            seeds.extend(comp_terms)
        
        return list(set(seeds))  # Remove duplicates
    
    def _extract_terms_from_url(self, url: str) -> List[str]:
        """Extract meaningful terms from URL."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            
            # Remove common TLDs and www
            parts = hostname.replace("www.", "").split(".")
            if len(parts) >= 2:
                domain = parts[-2]
                # Split by common separators
                import re
                terms = re.split(r'[-_.]', domain)
                return [term for term in terms if len(term) > 2]
        except Exception:
            pass
        return []
