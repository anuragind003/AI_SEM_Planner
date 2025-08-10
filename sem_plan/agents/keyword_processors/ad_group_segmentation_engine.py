from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import re

from ...core.types import KeywordRecord, Config, CampaignOutputs


class AdGroupSegmentationEngine:
    """Creates optimized ad groups and campaign themes."""
    
    def __init__(self, config: Config):
        self.config = config
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.brand_terms = self._extract_brand_terms()
        
    def create_campaign_outputs(self, keywords: List[KeywordRecord]) -> CampaignOutputs:
        """Create final campaign outputs with ad groups and themes."""
        
        # Convert to DataFrame
        df = self._keywords_to_dataframe(keywords)
        
        # Create semantic clusters
        df = self._create_semantic_clusters(df)
        
        # Segment into ad groups
        ad_groups = self._create_ad_groups(df)
        
        # Generate PMax themes
        pmax_themes = self._generate_pmax_themes(df)
        
        # Calculate shopping target CPC
        shopping_target_cpc = self._calculate_shopping_target_cpc(df)
        
        # Convert back to KeywordRecord objects
        search_keywords = self._create_search_keywords(df, ad_groups)
        
        return CampaignOutputs(
            search_keywords=search_keywords,
            pmax_themes=pmax_themes,
            shopping_target_cpc=shopping_target_cpc
        )
    
    def _extract_brand_terms(self) -> List[str]:
        """Extract brand terms from URL."""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(self.config.brand_url)
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
    
    def _create_semantic_clusters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create semantic clusters using embeddings."""
        
        # Create embeddings for all keywords
        keywords_list = df['keyword'].tolist()
        embeddings = self.embedding_model.encode(keywords_list)
        
        # Determine optimal number of clusters
        n_clusters = min(20, max(5, len(keywords_list) // 50))
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        df['semantic_cluster'] = cluster_labels
        
        # Create cluster centroids for naming
        cluster_centroids = kmeans.cluster_centers_
        df['cluster_centroid'] = df['semantic_cluster'].apply(lambda x: cluster_centroids[x])
        
        return df
    
    def _create_ad_groups(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Create ad groups based on semantic clusters and intent."""
        
        ad_groups = {}
        
        # Brand terms ad group
        brand_keywords = []
        for _, row in df.iterrows():
            if any(brand_term in row['keyword'].lower() for brand_term in self.brand_terms):
                brand_keywords.append(row['keyword'])
        
        if brand_keywords:
            ad_groups['Brand Terms'] = brand_keywords
        
        # Intent-based ad groups
        for intent in ['transactional', 'commercial', 'informational']:
            intent_keywords = df[df['intent'] == intent]['keyword'].tolist()
            if intent_keywords:
                ad_groups[f'{intent.title()} Intent'] = intent_keywords
        
        # Performance-based ad groups
        high_performing = df[df['cluster'].str.contains('high_performing', na=False)]['keyword'].tolist()
        if high_performing:
            ad_groups['High Performing'] = high_performing
        
        goldmine_keywords = df[df['cluster'].str.contains('goldmine', na=False)]['keyword'].tolist()
        if goldmine_keywords:
            ad_groups['Goldmine Opportunities'] = goldmine_keywords
        
        # Competition-based ad groups
        low_competition = df[df['competition'] == 'low']['keyword'].tolist()
        if low_competition:
            ad_groups['Low Competition'] = low_competition
        
        # Volume-based ad groups
        high_volume = df[df['gkp_avg_monthly_searches'] >= 1000]['keyword'].tolist()
        if high_volume:
            ad_groups['High Volume'] = high_volume
        
        # Semantic cluster-based ad groups
        for cluster_id in df['semantic_cluster'].unique():
            cluster_keywords = df[df['semantic_cluster'] == cluster_id]['keyword'].tolist()
            if len(cluster_keywords) >= 3:  # Only create ad groups with 3+ keywords
                ad_groups[f'Semantic Cluster {cluster_id}'] = cluster_keywords
        
        return ad_groups
    
    def _generate_pmax_themes(self, df: pd.DataFrame) -> List[str]:
        """Generate Performance Max themes from high-performing clusters."""
        
        themes = []
        
        # Extract themes from high-performing keywords
        high_performing = df[df['cluster'].str.contains('high_performing', na=False)]
        
        if not high_performing.empty:
            # Group by semantic cluster and extract common themes
            for cluster_id in high_performing['semantic_cluster'].unique():
                cluster_keywords = high_performing[high_performing['semantic_cluster'] == cluster_id]['keyword'].tolist()
                
                if len(cluster_keywords) >= 3:
                    # Extract common terms
                    common_terms = self._extract_common_terms(cluster_keywords)
                    if common_terms:
                        themes.append(' '.join(common_terms[:3]))  # Top 3 terms
        
        # Add intent-based themes
        for intent in ['transactional', 'commercial']:
            intent_keywords = df[df['intent'] == intent]['keyword'].tolist()
            if intent_keywords:
                common_terms = self._extract_common_terms(intent_keywords)
                if common_terms:
                    themes.append(f"{intent.title()}: {' '.join(common_terms[:2])}")
        
        # Add product category themes
        product_themes = self._extract_product_themes(df)
        themes.extend(product_themes)
        
        return list(set(themes))  # Remove duplicates
    
    def _extract_common_terms(self, keywords: List[str]) -> List[str]:
        """Extract common terms from a list of keywords."""
        from collections import Counter
        
        # Tokenize and count terms
        all_terms = []
        for keyword in keywords:
            terms = keyword.lower().split()
            all_terms.extend(terms)
        
        # Count frequency
        term_counts = Counter(all_terms)
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
        
        # Get most common terms (excluding stop words)
        common_terms = [term for term, count in term_counts.most_common(10) 
                       if term not in stop_words and len(term) > 2]
        
        return common_terms
    
    def _extract_product_themes(self, df: pd.DataFrame) -> List[str]:
        """Extract product category themes."""
        
        themes = []
        
        # Look for product-related terms
        product_indicators = ['product', 'service', 'tool', 'software', 'app', 'platform', 'solution']
        
        for indicator in product_indicators:
            product_keywords = df[df['keyword'].str.contains(indicator, case=False, na=False)]['keyword'].tolist()
            if product_keywords:
                common_terms = self._extract_common_terms(product_keywords)
                if common_terms:
                    themes.append(f"{indicator.title()}: {' '.join(common_terms[:2])}")
        
        return themes
    
    def _calculate_shopping_target_cpc(self, df: pd.DataFrame) -> float:
        """Calculate target CPC for shopping campaigns."""
        
        # Focus on transactional keywords for shopping
        transactional = df[df['intent'] == 'transactional']
        
        if transactional.empty:
            # Fallback to all keywords
            transactional = df
        
        # Calculate weighted average CPC based on volume
        total_volume = transactional['gkp_avg_monthly_searches'].sum()
        
        if total_volume > 0:
            weighted_cpc = (
                (transactional['gkp_top_of_page_bid_low'] * transactional['gkp_avg_monthly_searches']).sum() / total_volume
            )
        else:
            weighted_cpc = 2.0  # Default CPC
        
        # Adjust based on target CPA
        target_cpa = self.config.project_settings.assumed_conversion_rate * 50  # Assume $50 CPA
        target_cpc = target_cpa * self.config.project_settings.assumed_conversion_rate
        
        # Use the lower of the two to be conservative
        return min(weighted_cpc, target_cpc)
    
    def _create_search_keywords(self, df: pd.DataFrame, ad_groups: Dict[str, List[str]]) -> List[KeywordRecord]:
        """Create final search keywords with ad group assignments."""
        
        keywords = []
        
        for _, row in df.iterrows():
            # Find which ad group this keyword belongs to
            ad_group = self._assign_ad_group(row['keyword'], ad_groups)
            
            # Update cluster to include ad group info
            updated_cluster = f"{ad_group}_{row['cluster']}"
            
            kw_record = KeywordRecord(
                keyword=row['keyword'],
                normalized=row['normalized'],
                intent=row['intent'],
                cluster=updated_cluster,
                match_type=row['match_type'],
                competition=row['competition'],
                volume=row['volume'],
                sources=row['sources'],
                gkp_avg_monthly_searches=row['gkp_avg_monthly_searches'],
                gkp_top_of_page_bid_low=row['gkp_top_of_page_bid_low'],
                gkp_top_of_page_bid_high=row['gkp_top_of_page_bid_high']
            )
            keywords.append(kw_record)
        
        return keywords
    
    def _assign_ad_group(self, keyword: str, ad_groups: Dict[str, List[str]]) -> str:
        """Assign keyword to the most appropriate ad group."""
        
        for ad_group_name, ad_group_keywords in ad_groups.items():
            if keyword in ad_group_keywords:
                return ad_group_name
        
        # If not found in any ad group, assign to "Other"
        return "Other"
