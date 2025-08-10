from __future__ import annotations

import re
from typing import Iterable, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

from ...core.types import RawKeyword, Config
from ...utils.http import get, polite_delay


class SearchSuggestionsCollector:
    """Collects search-based keyword suggestions from Google."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def collect_suggestions(self, extra_seeds: Optional[Iterable[str]], 
                          max_serp_queries: int) -> List[RawKeyword]:
        """Collect search-based keyword suggestions."""
        keywords = []
        
        # Get seed terms
        seeds = self._get_seed_terms(extra_seeds)
        
        for seed in seeds[:max_serp_queries]:
            # Google Autocomplete
            keywords.extend(self._get_google_autocomplete(seed))
            
            # Google Related Searches
            keywords.extend(self._get_google_related_searches(seed))
            
            # People Also Ask
            keywords.extend(self._get_people_also_ask(seed))
            
            polite_delay(2.0)  # Be respectful
            
        return keywords
    
    def _get_seed_terms(self, extra_seeds: Optional[Iterable[str]]) -> List[str]:
        """Get seed terms from brand, competitors, and extra seeds."""
        seeds = []
        
        # Extract terms from URLs
        brand_terms = self._extract_terms_from_url(self.config.brand_url)
        seeds.extend(brand_terms)
        
        for comp_url in self.config.competitor_urls:
            comp_terms = self._extract_terms_from_url(comp_url)
            seeds.extend(comp_terms)
        
        # Add extra seeds
        if extra_seeds:
            for seed in extra_seeds:
                if isinstance(seed, str) and seed.strip():
                    seeds.append(seed.strip())
        
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
                terms = re.split(r'[-_.]', domain)
                return [term for term in terms if len(term) > 2]
        except Exception:
            pass
        return []
    
    def _get_google_autocomplete(self, seed: str) -> List[RawKeyword]:
        """Get Google Autocomplete suggestions."""
        keywords = []
        
        try:
            # Try the unofficial Google Autocomplete API
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
    
    def _get_people_also_ask(self, seed: str) -> List[RawKeyword]:
        """Get People Also Ask questions from SERP."""
        keywords = []
        
        try:
            url = f"https://www.google.com/search?q={seed.replace(' ', '+')}&hl=en"
            response = get(url, headers={"Accept": "text/html"})
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for People Also Ask questions
            for el in soup.select("div[jsname] div:has(q), div:has(cite)"):
                text = el.get_text(" ", strip=True)
                if text and not text.endswith("...") and len(text.split()) >= 3:
                    keywords.append(RawKeyword(
                        keyword=text.lower(),
                        source="people_also_ask",
                        seed=seed
                    ))
                    
        except Exception as e:
            print(f"People Also Ask failed for {seed}: {e}")
        
        return keywords
