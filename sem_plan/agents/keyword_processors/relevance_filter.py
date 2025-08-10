from __future__ import annotations

from typing import List, Set
from urllib.parse import urlparse

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ...core.types import RawKeyword, Config


class RelevanceFilter:
    """Filters keywords for relevance to the brand and business."""
    
    def __init__(self, config: Config):
        self.config = config
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def filter_keywords(self, keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Filter keywords for relevance."""
        filtered = []
        
        # Get brand and competitor terms for relevance checking
        brand_terms = self._extract_terms_from_url(self.config.brand_url)
        competitor_terms = []
        for comp_url in self.config.competitor_urls:
            competitor_terms.extend(self._extract_terms_from_url(comp_url))
        
        all_relevant_terms = set(brand_terms + competitor_terms)
        
        for kw in keywords:
            if self._is_relevant_keyword(kw.keyword, all_relevant_terms):
                filtered.append(kw)
        
        return filtered
    
    def _is_relevant_keyword(self, keyword: str, relevant_terms: Set[str]) -> bool:
        """Check if a keyword is relevant."""
        keyword_lower = keyword.lower()
        
        # Remove extremely generic terms
        generic_terms = {
            "website", "shop", "about", "contact", "home", "page", "site",
            "click", "read", "more", "learn", "here", "this", "that"
        }
        
        if any(term in keyword_lower for term in generic_terms):
            return False
        
        # Check minimum frequency (at least 2 words for multi-word phrases)
        words = keyword_lower.split()
        if len(words) == 1 and len(keyword) < 4:
            return False
        
        # Check if it's too long
        if len(words) > 4:
            return False
        
        # Check relevance to brand/competitor terms
        if relevant_terms:
            keyword_words = set(words)
            if keyword_words.intersection(relevant_terms):
                return True
        
        # If no direct match, check semantic similarity
        if relevant_terms:
            try:
                keyword_embedding = self.embedding_model.encode([keyword_lower])
                relevant_embeddings = self.embedding_model.encode(list(relevant_terms))
                
                similarities = cosine_similarity(keyword_embedding, relevant_embeddings)[0]
                max_similarity = max(similarities)
                
                return max_similarity > 0.3  # Threshold for relevance
            except Exception:
                pass
        
        return True  # Default to keeping if we can't determine relevance
    
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
