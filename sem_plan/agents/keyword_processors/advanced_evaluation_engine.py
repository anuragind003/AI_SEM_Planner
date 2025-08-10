from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans

from ...core.types import KeywordRecord, Config


class AdvancedEvaluationEngine:
    """Advanced keyword evaluation with sophisticated scoring and filtering."""
    
    def __init__(self, config: Config):
        self.config = config
        self.conversion_rate = config.project_settings.assumed_conversion_rate
        self.target_cpa = self._calculate_target_cpa()
        
    def evaluate_and_score(self, keywords: List[KeywordRecord]) -> List[KeywordRecord]:
        """Apply advanced evaluation criteria and scoring."""
        
        # Convert to DataFrame for easier processing
        df = self._keywords_to_dataframe(keywords)
        
        # Calculate advanced metrics
        df = self._calculate_advanced_metrics(df)
        
        # Apply sophisticated scoring
        df = self._apply_scoring_model(df)
        
        # Apply competition-aware filtering
        df = self._apply_competition_filtering(df)
        
        # Flag goldmine opportunities
        df = self._identify_goldmines(df)
        
        # Sort by final score
        df = df.sort_values('final_score', ascending=False)
        
        # Convert back to KeywordRecord objects
        return self._dataframe_to_keywords(df)
    
    def _calculate_target_cpa(self) -> float:
        """Calculate target CPA based on budget and conversion rate."""
        total_budget = (
            self.config.ad_budgets.search_ads_budget +
            self.config.ad_budgets.shopping_ads_budget +
            self.config.ad_budgets.pmax_ads_budget
        )
        
        # Assume 10% of budget for testing/learning
        effective_budget = total_budget * 0.9
        
        # Target CPA = Budget / (Expected Conversions)
        # Expected Conversions = Budget * Conversion Rate / Average CPC
        # For initial calculation, assume average CPC of $2
        avg_cpc = 2.0
        expected_conversions = effective_budget * self.conversion_rate / avg_cpc
        
        return effective_budget / expected_conversions if expected_conversions > 0 else 50.0
    
    def _keywords_to_dataframe(self, keywords: List[KeywordRecord]) -> pd.DataFrame:
        """Convert KeywordRecord objects to DataFrame."""
        data = []
        for kw in keywords:
            row = {
                'keyword': kw.keyword,
                'normalized': kw.normalized,
                'intent': kw.intent,
                'cluster': kw.cluster,
                'match_type': kw.match_type,
                'competition': kw.competition,
                'volume': kw.volume or 0,
                'sources': kw.sources,
                'gkp_avg_monthly_searches': kw.gkp_avg_monthly_searches or 0,
                'gkp_top_of_page_bid_low': kw.gkp_top_of_page_bid_low or 0,
                'gkp_top_of_page_bid_high': kw.gkp_top_of_page_bid_high or 0
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def _calculate_advanced_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced metrics for evaluation."""
        
        # Commercial intent score
        df['commercial_intent_score'] = df['keyword'].apply(self._calculate_commercial_intent)
        
        # Bid spread (indicates advertiser willingness to pay)
        df['bid_spread'] = df['gkp_top_of_page_bid_high'] - df['gkp_top_of_page_bid_low']
        df['bid_spread_ratio'] = df['bid_spread'] / df['gkp_top_of_page_bid_low'].replace(0, 1)
        
        # Volume-to-cost ratio
        df['volume_cost_ratio'] = df['gkp_avg_monthly_searches'] / df['gkp_top_of_page_bid_low'].replace(0, 1)
        
        # Competition score (numeric)
        competition_map = {'low': 1, 'medium': 2, 'high': 3}
        df['competition_score'] = df['competition'].map(competition_map)
        
        # Intent score (numeric)
        intent_map = {'informational': 1, 'commercial': 2, 'transactional': 3}
        df['intent_score'] = df['intent'].map(intent_map)
        
        # Target CPC based on ROI
        df['target_cpc'] = self.target_cpa * self.conversion_rate
        
        # ROI potential (how much we can afford vs actual bids)
        df['roi_potential'] = (df['target_cpc'] - df['gkp_top_of_page_bid_low']) / df['gkp_top_of_page_bid_low'].replace(0, 1)
        
        return df
    
    def _calculate_commercial_intent(self, keyword: str) -> float:
        """Calculate commercial intent score (0-1)."""
        keyword_lower = keyword.lower()
        score = 0.5  # Base score
        
        # Transactional indicators (highest intent)
        transactional_terms = ['buy', 'purchase', 'order', 'price', 'cost', 'cheap', 'discount', 'deal', 'sale']
        if any(term in keyword_lower for term in transactional_terms):
            score += 0.4
        
        # Commercial indicators (medium intent)
        commercial_terms = ['best', 'top', 'reviews', 'compare', 'vs', 'alternatives', 'competitor']
        if any(term in keyword_lower for term in commercial_terms):
            score += 0.2
        
        # Informational indicators (lower intent)
        informational_terms = ['what is', 'how to', 'guide', 'tutorial', 'ideas', 'benefits', 'tips']
        if any(term in keyword_lower for term in informational_terms):
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _apply_scoring_model(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the sophisticated scoring model."""
        
        # Normalize features
        scaler = MinMaxScaler()
        
        # Prepare features for normalization
        features_to_normalize = [
            'gkp_avg_monthly_searches',
            'volume_cost_ratio',
            'commercial_intent_score',
            'bid_spread_ratio',
            'roi_potential'
        ]
        
        # Invert competition score (lower competition = higher score)
        df['inverse_competition_score'] = 4 - df['competition_score']
        
        # Normalize features
        normalized_features = scaler.fit_transform(df[features_to_normalize + ['inverse_competition_score']])
        
        # Apply scoring formula
        df['normalized_volume'] = normalized_features[:, 0]
        df['normalized_volume_cost'] = normalized_features[:, 1]
        df['normalized_commercial_intent'] = normalized_features[:, 2]
        df['normalized_bid_spread'] = normalized_features[:, 3]
        df['normalized_roi_potential'] = normalized_features[:, 4]
        df['normalized_inverse_competition'] = normalized_features[:, 5]
        
        # Final score using the formula from your approach
        df['final_score'] = (
            0.4 * df['normalized_volume'] +
            0.3 * df['normalized_inverse_competition'] +
            0.3 * df['normalized_commercial_intent']
        )
        
        return df
    
    def _apply_competition_filtering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply competition-aware filtering."""
        
        # High competition + high bid → keep only if high relevance & proven conversion potential
        high_comp_high_bid = (
            (df['competition'] == 'high') & 
            (df['gkp_top_of_page_bid_high'] > 5.0) &
            (df['commercial_intent_score'] < 0.7)
        )
        df = df[~high_comp_high_bid]
        
        # Low competition + decent search volume → often cost-efficient
        low_comp_good_volume = (
            (df['competition'] == 'low') & 
            (df['gkp_avg_monthly_searches'] >= 200)
        )
        # Keep these (they're good)
        
        # Medium competition + good ROI potential → keep
        medium_comp_good_roi = (
            (df['competition'] == 'medium') & 
            (df['roi_potential'] > 0.2)
        )
        # Keep these
        
        return df
    
    def _identify_goldmines(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify high-volume, low-bid opportunities."""
        
        # Goldmine criteria: high volume, low bid, decent commercial intent
        df['is_goldmine'] = (
            (df['gkp_avg_monthly_searches'] >= 1000) &
            (df['gkp_top_of_page_bid_low'] <= 2.0) &
            (df['commercial_intent_score'] >= 0.6) &
            (df['competition'] != 'high')
        )
        
        # Boost goldmine scores
        df.loc[df['is_goldmine'], 'final_score'] *= 1.5
        
        return df
    
    def _dataframe_to_keywords(self, df: pd.DataFrame) -> List[KeywordRecord]:
        """Convert DataFrame back to KeywordRecord objects."""
        keywords = []
        
        for _, row in df.iterrows():
            # Update match type based on final evaluation
            updated_match_type = self._update_match_type(row)
            
            # Update cluster based on scoring
            updated_cluster = self._update_cluster(row)
            
            kw_record = KeywordRecord(
                keyword=row['keyword'],
                normalized=row['normalized'],
                intent=row['intent'],
                cluster=updated_cluster,
                match_type=updated_match_type,
                competition=row['competition'],
                volume=row['volume'],
                sources=row['sources'],
                gkp_avg_monthly_searches=row['gkp_avg_monthly_searches'],
                gkp_top_of_page_bid_low=row['gkp_top_of_page_bid_low'],
                gkp_top_of_page_bid_high=row['gkp_top_of_page_bid_high']
            )
            keywords.append(kw_record)
        
        return keywords
    
    def _update_match_type(self, row) -> str:
        """Update match type based on final evaluation."""
        score = row['final_score']
        volume = row['gkp_avg_monthly_searches']
        intent = row['intent']
        
        if score >= 0.8 and volume >= 1000 and intent == "transactional":
            return "exact"
        elif score >= 0.6 and volume >= 500:
            return "phrase"
        else:
            return "broad"
    
    def _update_cluster(self, row) -> str:
        """Update cluster based on scoring and characteristics."""
        score = row['final_score']
        intent = row['intent']
        is_goldmine = row.get('is_goldmine', False)
        
        if is_goldmine:
            return f"goldmine_{intent}"
        elif score >= 0.8:
            return f"high_performing_{intent}"
        elif score >= 0.6:
            return f"medium_performing_{intent}"
        else:
            return f"low_performing_{intent}"
