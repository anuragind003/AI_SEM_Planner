from __future__ import annotations

import pandas as pd
from typing import List, Dict, Set, Optional
from dataclasses import asdict
import re

from ...core.types import RawKeyword, Config, KeywordRecord
from ...utils.http import get


class ConsolidationEngine:
    """Consolidates keywords from multiple sources and applies initial filtering."""
    
    def __init__(self, config: Config):
        self.config = config
        self.min_volume_threshold = config.project_settings.min_search_volume_threshold or 500
        
    def consolidate_keywords(self, keywords: List[RawKeyword]) -> List[KeywordRecord]:
        """Merge all keyword sources into a master DataFrame and apply filtering."""
        
        # Convert to DataFrame for easier processing
        df = self._keywords_to_dataframe(keywords)
        
        # Fill missing search volume & bid data
        df = self._enrich_missing_data(df)
        
        # Apply initial filters
        df = self._apply_initial_filters(df)
        
        # Convert back to KeywordRecord objects
        return self._dataframe_to_keywords(df)
    
    def _keywords_to_dataframe(self, keywords: List[RawKeyword]) -> pd.DataFrame:
        """Convert RawKeyword objects to DataFrame."""
        data = []
        for kw in keywords:
            row = {
                'keyword': kw.keyword,
                'source': kw.source,
                'seed': kw.seed,
                'volume': kw.volume or kw.gkp_avg_monthly_searches,
                'competition': kw.competition or kw.gkp_competition,
                'top_bid_low': kw.gkp_top_of_page_bid_low,
                'top_bid_high': kw.gkp_top_of_page_bid_high,
                'origin_url': kw.origin_url,
                'sources': [kw.source]  # Track all sources for this keyword
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Group by keyword and merge sources
        df = df.groupby('keyword').agg({
            'source': lambda x: list(set(x)),
            'seed': 'first',
            'volume': 'max',  # Take highest volume if multiple sources
            'competition': lambda x: self._merge_competition_levels(x),
            'top_bid_low': 'min',  # Take lowest bid
            'top_bid_high': 'max',  # Take highest bid
            'origin_url': 'first'
        }).reset_index()
        
        # Flatten source lists
        df['sources'] = df['source'].apply(lambda x: list(set(x)) if isinstance(x, list) else [x])
        
        return df
    
    def _merge_competition_levels(self, levels) -> str:
        """Merge multiple competition levels into one."""
        level_map = {'low': 1, 'medium': 2, 'high': 3}
        numeric_levels = [level_map.get(level, 2) for level in levels if level]
        
        if not numeric_levels:
            return 'medium'
        
        avg_level = sum(numeric_levels) / len(numeric_levels)
        
        if avg_level <= 1.5:
            return 'low'
        elif avg_level <= 2.5:
            return 'medium'
        else:
            return 'high'
    
    def _enrich_missing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing search volume and bid data using free tools."""
        
        # Estimate missing volumes
        df['volume'] = df['volume'].fillna(df['keyword'].apply(self._estimate_volume))
        
        # Estimate missing CPC data
        df['top_bid_low'] = df['top_bid_low'].fillna(df['keyword'].apply(self._estimate_cpc_low))
        df['top_bid_high'] = df['top_bid_high'].fillna(df['keyword'].apply(self._estimate_cpc_high))
        
        # Estimate missing competition
        df['competition'] = df['competition'].fillna(df['keyword'].apply(self._estimate_competition))
        
        return df
    
    def _estimate_volume(self, keyword: str) -> int:
        """Estimate search volume based on keyword characteristics."""
        words = keyword.lower().split()
        length = len(words)
        
        # Base volume by length
        base_volume = 1000 if length == 1 else 500 if length == 2 else 200 if length == 3 else 100
        
        # Adjust by intent
        intent = self._detect_intent(keyword)
        if intent == "transactional":
            base_volume *= 0.8
        elif intent == "informational":
            base_volume *= 1.2
        
        # Adjust by commercial indicators
        if any(x in keyword.lower() for x in ["buy", "price", "cost", "cheap", "discount"]):
            base_volume *= 1.5
        
        return max(10, int(base_volume))
    
    def _estimate_cpc_low(self, keyword: str) -> float:
        """Estimate low CPC bid."""
        intent = self._detect_intent(keyword)
        base_cpc = {"transactional": 2.5, "commercial": 1.8, "informational": 1.2}.get(intent, 1.5)
        
        # Adjust by competition
        competition = self._estimate_competition(keyword)
        multiplier = {"low": 0.7, "medium": 1.0, "high": 1.5}.get(competition, 1.0)
        
        return round(base_cpc * multiplier, 2)
    
    def _estimate_cpc_high(self, keyword: str) -> float:
        """Estimate high CPC bid."""
        low_cpc = self._estimate_cpc_low(keyword)
        return round(low_cpc * 1.8, 2)  # 80% higher than low bid
    
    def _estimate_competition(self, keyword: str) -> str:
        """Estimate competition level."""
        keyword_lower = keyword.lower()
        
        # High competition indicators
        if any(x in keyword_lower for x in ["best", "top", "near me", "free", "cheap", "discount"]):
            return "high"
        
        # Medium competition indicators
        if any(x in keyword_lower for x in ["vs", "compare", "alternatives", "reviews"]):
            return "medium"
        
        return "low"
    
    def _detect_intent(self, keyword: str) -> str:
        """Detect keyword intent."""
        keyword_lower = keyword.lower()
        
        if any(x in keyword_lower for x in ["buy", "pricing", "price", "demo", "trial", "quote", "order"]):
            return "transactional"
        elif any(x in keyword_lower for x in ["vs", "compare", "alternatives", "competitor", "best", "reviews"]):
            return "commercial"
        elif any(x in keyword_lower for x in ["what is", "how to", "guide", "tutorial", "ideas", "benefits"]):
            return "informational"
        else:
            return "commercial"
    
    def _apply_initial_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply initial filtering criteria."""
        
        # Remove low volume keywords
        df = df[df['volume'] >= self.min_volume_threshold]
        
        # Remove obvious low-commercial-intent queries (unless targeting informational ads)
        df = df[~df['keyword'].str.lower().str.contains(r'^(?:how to make|how to create|how to build|diy|tutorial)')]
        
        # Remove very short or very long keywords
        df = df[df['keyword'].str.len() >= 3]
        df = df[df['keyword'].str.len() <= 100]
        
        # Remove duplicate keywords (case-insensitive)
        df = df.drop_duplicates(subset=['keyword'], keep='first')
        
        return df
    
    def _dataframe_to_keywords(self, df: pd.DataFrame) -> List[KeywordRecord]:
        """Convert DataFrame back to KeywordRecord objects."""
        keywords = []
        
        for _, row in df.iterrows():
            # Determine intent
            intent = self._detect_intent(row['keyword'])
            
            # Determine match type based on intent and volume
            match_type = self._determine_match_type(row['keyword'], intent, row['volume'])
            
            # Create cluster (will be refined later)
            cluster = self._create_initial_cluster(row['keyword'], intent)
            
            kw_record = KeywordRecord(
                keyword=row['keyword'],
                normalized=row['keyword'].lower().strip(),
                intent=intent,
                cluster=cluster,
                match_type=match_type,
                competition=row['competition'],
                volume=row['volume'],
                sources=row['sources'],
                gkp_avg_monthly_searches=row['volume'],
                gkp_top_of_page_bid_low=row['top_bid_low'],
                gkp_top_of_page_bid_high=row['top_bid_high']
            )
            keywords.append(kw_record)
        
        return keywords
    
    def _determine_match_type(self, keyword: str, intent: str, volume: int) -> str:
        """Determine suggested match type."""
        if intent == "transactional" and volume >= 1000:
            return "exact"  # High intent, good volume
        elif intent == "commercial" and volume >= 500:
            return "phrase"  # Medium intent, decent volume
        else:
            return "broad"  # Lower intent or volume
    
    def _create_initial_cluster(self, keyword: str, intent: str) -> str:
        """Create initial semantic cluster."""
        # This will be refined by the clustering engine
        return f"{intent}_cluster"
