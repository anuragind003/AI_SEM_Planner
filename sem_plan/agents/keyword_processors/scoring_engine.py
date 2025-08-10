from __future__ import annotations

from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ...core.types import RawKeyword, Config
from ...utils.cache import load_cache, save_cache


class ScoringEngine:
    """Scores and prioritizes keywords based on multiple factors."""
    
    def __init__(self, config: Config):
        self.config = config
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache = load_cache()
        self.updated_cache = False
    
    def score_and_prioritize(self, keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Score and prioritize keywords."""
        scored_keywords = []
        
        # Get brand terms for relevance scoring
        brand_terms = set(self._extract_terms_from_url(self.config.brand_url))
        
        for kw in keywords:
            score = self._calculate_keyword_score(kw, brand_terms)
            kw.gkp_avg_monthly_searches = score.get('volume', 100)
            kw.gkp_top_of_page_bid_low = score.get('cpc_low', 1.0)
            kw.gkp_top_of_page_bid_high = score.get('cpc_high', 2.0)
            kw.gkp_competition = score.get('competition', 'medium')
            
            scored_keywords.append(kw)
        
        # Sort by score
        scored_keywords.sort(key=lambda x: x.gkp_avg_monthly_searches or 0, reverse=True)
        
        # Save cache if updated
        if self.updated_cache:
            save_cache(self.cache)
        
        return scored_keywords
    
    def _calculate_keyword_score(self, keyword: RawKeyword, brand_terms: Set[str]) -> Dict:
        """Calculate comprehensive keyword score."""
        key = keyword.keyword.lower().strip()
        
        # Check cache first
        if key in self.cache:
            return self.cache[key]
        
        # Calculate frequency score
        frequency_score = self._calculate_frequency_score(keyword)
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(keyword.keyword, brand_terms)
        
        # Calculate search volume estimate
        volume_estimate = self._estimate_search_volume(keyword)
        
        # Calculate CPC estimate
        cpc_low, cpc_high = self._estimate_cpc(keyword)
        
        # Calculate competition
        competition = self._estimate_competition(keyword)
        
        # Final score
        final_score = (0.5 * frequency_score) + (0.3 * relevance_score) + (0.2 * (volume_estimate / 10000))
        
        result = {
            'volume': int(volume_estimate),
            'cpc_low': cpc_low,
            'cpc_high': cpc_high,
            'competition': competition,
            'final_score': final_score
        }
        
        # Cache the result
        self.cache[key] = result
        self.updated_cache = True
        
        return result
    
    def _calculate_frequency_score(self, keyword: RawKeyword) -> float:
        """Calculate frequency score based on source diversity."""
        sources = [kw.source for kw in [keyword] if hasattr(kw, 'source')]
        unique_sources = len(set(sources))
        return min(1.0, unique_sources / 3.0)  # Normalize to 0-1
    
    def _calculate_relevance_score(self, keyword: str, brand_terms: Set[str]) -> float:
        """Calculate relevance score using semantic similarity."""
        if not brand_terms:
            return 0.5  # Default score
        
        try:
            keyword_embedding = self.embedding_model.encode([keyword.lower()])
            brand_embeddings = self.embedding_model.encode(list(brand_terms))
            
            similarities = cosine_similarity(keyword_embedding, brand_embeddings)[0]
            max_similarity = max(similarities)
            
            return float(max_similarity)
        except Exception:
            return 0.5
    
    def _estimate_search_volume(self, keyword: RawKeyword) -> int:
        """Estimate search volume."""
        if keyword.volume:
            return keyword.volume
        
        # Heuristic estimation
        words = keyword.keyword.split()
        length = len(words)
        
        # Base volume by length
        base_volume = 1000 if length == 1 else 500 if length == 2 else 200 if length == 3 else 100
        
        # Adjust by intent
        intent = self._detect_intent(keyword.keyword)
        if intent == "transactional":
            base_volume *= 0.8  # Lower volume for transactional
        elif intent == "informational":
            base_volume *= 1.2  # Higher volume for informational
        
        return max(10, int(base_volume))
    
    def _detect_intent(self, keyword: str) -> str:
        """Detect keyword intent."""
        keyword_lower = keyword.lower()
        
        if any(x in keyword_lower for x in ["buy", "pricing", "price", "demo", "trial", "quote"]):
            return "transactional"
        elif any(x in keyword_lower for x in ["vs", "compare", "alternatives", "competitor", "best"]):
            return "commercial"
        elif any(x in keyword_lower for x in ["what is", "how to", "guide", "tutorial", "ideas", "benefits"]):
            return "informational"
        else:
            return "commercial"
    
    def _estimate_cpc(self, keyword: RawKeyword) -> Tuple[float, float]:
        """Estimate CPC range."""
        intent = self._detect_intent(keyword.keyword)
        competition = keyword.competition or "medium"
        
        # Base CPC by intent
        base_cpc = 1.0
        if intent == "transactional":
            base_cpc = 3.0
        elif intent == "commercial":
            base_cpc = 2.0
        elif intent == "informational":
            base_cpc = 0.8
        
        # Adjust by competition
        competition_multiplier = {"low": 0.8, "medium": 1.2, "high": 1.8}.get(competition, 1.0)
        
        adjusted_cpc = base_cpc * competition_multiplier
        
        return round(adjusted_cpc * 0.9, 2), round(adjusted_cpc * 1.3, 2)
    
    def _estimate_competition(self, keyword: RawKeyword) -> str:
        """Estimate competition level."""
        if keyword.competition:
            return keyword.competition
        
        keyword_lower = keyword.keyword.lower()
        
        # High competition indicators
        if any(x in keyword_lower for x in ["best", "top", "near me", "free"]):
            return "high"
        
        # Check volume for competition estimation
        volume = keyword.volume or self._estimate_search_volume(keyword)
        if volume >= 5000:
            return "high"
        elif volume >= 1000:
            return "medium"
        else:
            return "low"
    
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
