from __future__ import annotations

import pandas as pd
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from ...core.types import KeywordRecord, Config, CampaignOutputs


class DeliverablesGenerator:
    """Generates final deliverables in the specified format."""
    
    def __init__(self, config: Config):
        self.config = config
        
    def generate_deliverables(self, campaign_outputs: CampaignOutputs, output_dir: str = "outputs") -> Dict[str, str]:
        """Generate all deliverables and save to files."""
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        deliverables = {}
        
        # 1. Keyword List Grouped by Ad Groups (Search Campaign)
        search_deliverable = self._generate_search_campaign_deliverable(campaign_outputs.search_keywords)
        search_file = output_path / "search_campaign_keywords.csv"
        search_deliverable.to_csv(search_file, index=False)
        deliverables['search_campaign'] = str(search_file)
        
        # 2. Search Themes for Performance Max Campaign
        pmax_deliverable = self._generate_pmax_themes_deliverable(campaign_outputs.pmax_themes)
        pmax_file = output_path / "pmax_themes.json"
        with open(pmax_file, 'w') as f:
            json.dump(pmax_deliverable, f, indent=2)
        deliverables['pmax_themes'] = str(pmax_file)
        
        # 3. Suggested CPC Bids for Manual Shopping Campaign
        shopping_deliverable = self._generate_shopping_campaign_deliverable(
            campaign_outputs.search_keywords, 
            campaign_outputs.shopping_target_cpc
        )
        shopping_file = output_path / "shopping_campaign_cpc.csv"
        shopping_deliverable.to_csv(shopping_file, index=False)
        deliverables['shopping_campaign'] = str(shopping_file)
        
        # 4. Summary Report
        summary_deliverable = self._generate_summary_report(campaign_outputs)
        summary_file = output_path / "campaign_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary_deliverable, f, indent=2)
        deliverables['summary'] = str(summary_file)
        
        return deliverables
    
    def _generate_search_campaign_deliverable(self, keywords: List[KeywordRecord]) -> pd.DataFrame:
        """Generate keyword list grouped by ad groups for search campaign."""
        
        data = []
        for kw in keywords:
            # Extract ad group from cluster
            ad_group = kw.cluster.split('_')[0] if '_' in kw.cluster else 'Other'
            
            # Calculate suggested CPC range
            suggested_cpc_low = kw.gkp_top_of_page_bid_low or 1.0
            suggested_cpc_high = kw.gkp_top_of_page_bid_high or 2.0
            
            # Determine match type recommendation
            match_type = self._recommend_match_type(kw)
            
            row = {
                'Ad Group': ad_group,
                'Keyword': kw.keyword,
                'Match Type': match_type,
                'Search Volume': kw.gkp_avg_monthly_searches or 0,
                'Competition': kw.competition or 'medium',
                'Suggested CPC Low': suggested_cpc_low,
                'Suggested CPC High': suggested_cpc_high,
                'Intent': kw.intent,
                'Sources': ', '.join(kw.sources),
                'Notes': self._generate_keyword_notes(kw)
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Sort by ad group and search volume
        df = df.sort_values(['Ad Group', 'Search Volume'], ascending=[True, False])
        
        return df
    
    def _recommend_match_type(self, kw: KeywordRecord) -> str:
        """Recommend match type based on keyword characteristics."""
        volume = kw.gkp_avg_monthly_searches or 0
        intent = kw.intent
        competition = kw.competition or 'medium'
        
        if intent == "transactional" and volume >= 1000 and competition != 'high':
            return "Exact"
        elif intent == "commercial" and volume >= 500:
            return "Phrase"
        else:
            return "Broad"
    
    def _generate_keyword_notes(self, kw: KeywordRecord) -> str:
        """Generate notes for keyword."""
        notes = []
        
        if kw.gkp_avg_monthly_searches and kw.gkp_avg_monthly_searches >= 1000:
            notes.append("High volume")
        
        if kw.competition == 'low':
            notes.append("Low competition opportunity")
        
        if 'goldmine' in kw.cluster.lower():
            notes.append("Goldmine opportunity")
        
        if kw.intent == "transactional":
            notes.append("High conversion potential")
        
        return '; '.join(notes) if notes else "Standard keyword"
    
    def _generate_pmax_themes_deliverable(self, pmax_themes: List[str]) -> Dict:
        """Generate PMax themes deliverable."""
        
        # Categorize themes
        categorized_themes = {
            'Product Categories': [],
            'Intent-Based': [],
            'Demographic': [],
            'Seasonal/Event': [],
            'Use-Case Based': []
        }
        
        for theme in pmax_themes:
            theme_lower = theme.lower()
            
            if any(x in theme_lower for x in ['product', 'service', 'tool', 'software', 'app']):
                categorized_themes['Product Categories'].append(theme)
            elif any(x in theme_lower for x in ['transactional', 'commercial', 'informational']):
                categorized_themes['Intent-Based'].append(theme)
            elif any(x in theme_lower for x in ['professional', 'business', 'personal', 'family']):
                categorized_themes['Demographic'].append(theme)
            elif any(x in theme_lower for x in ['seasonal', 'event', 'holiday', 'back to school']):
                categorized_themes['Seasonal/Event'].append(theme)
            else:
                categorized_themes['Use-Case Based'].append(theme)
        
        return {
            'total_themes': len(pmax_themes),
            'categorized_themes': categorized_themes,
            'all_themes': pmax_themes,
            'recommendations': {
                'primary_themes': pmax_themes[:5],
                'secondary_themes': pmax_themes[5:10] if len(pmax_themes) > 5 else [],
                'testing_themes': pmax_themes[10:15] if len(pmax_themes) > 10 else []
            }
        }
    
    def _generate_shopping_campaign_deliverable(self, keywords: List[KeywordRecord], target_cpc: float) -> pd.DataFrame:
        """Generate shopping campaign CPC recommendations."""
        
        # Filter for transactional keywords
        transactional_keywords = [kw for kw in keywords if kw.intent == "transactional"]
        
        data = []
        for kw in transactional_keywords:
            # Calculate target CPC based on ROI
            target_cpc_for_keyword = self.target_cpa * self.config.project_settings.assumed_conversion_rate
            
            # Compare with actual bids
            actual_low = kw.gkp_top_of_page_bid_low or 1.0
            actual_high = kw.gkp_top_of_page_bid_high or 2.0
            
            # Determine bid strategy
            if target_cpc_for_keyword < actual_low:
                bid_strategy = "Increase budget or exclude"
                recommended_cpc = actual_low * 1.1  # 10% above low bid
            elif target_cpc_for_keyword > actual_high:
                bid_strategy = "Can win with lower spend"
                recommended_cpc = actual_high * 0.9  # 10% below high bid
            else:
                bid_strategy = "Competitive within budget"
                recommended_cpc = target_cpc_for_keyword
            
            row = {
                'Product Keyword': kw.keyword,
                'Search Volume': kw.gkp_avg_monthly_searches or 0,
                'Competition': kw.competition or 'medium',
                'Actual Bid Low': actual_low,
                'Actual Bid High': actual_high,
                'Target CPC': round(target_cpc_for_keyword, 2),
                'Recommended CPC': round(recommended_cpc, 2),
                'Bid Strategy': bid_strategy,
                'ROI Potential': self._calculate_roi_potential(target_cpc_for_keyword, actual_low)
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Only sort if DataFrame is not empty
        if not df.empty:
            df = df.sort_values('ROI Potential', ascending=False)
        
        return df
    
    def _calculate_roi_potential(self, target_cpc: float, actual_low: float) -> str:
        """Calculate ROI potential."""
        if target_cpc < actual_low:
            return "Low - Need higher budget"
        elif target_cpc > actual_low * 1.5:
            return "High - Good margin"
        else:
            return "Medium - Competitive"
    
    def _generate_summary_report(self, campaign_outputs: CampaignOutputs) -> Dict:
        """Generate comprehensive summary report."""
        
        # Analyze search keywords
        search_keywords = campaign_outputs.search_keywords
        
        # Group by ad group
        ad_group_stats = {}
        for kw in search_keywords:
            ad_group = kw.cluster.split('_')[0] if '_' in kw.cluster else 'Other'
            if ad_group not in ad_group_stats:
                ad_group_stats[ad_group] = {
                    'count': 0,
                    'total_volume': 0,
                    'avg_cpc_low': 0,
                    'avg_cpc_high': 0,
                    'intents': {'transactional': 0, 'commercial': 0, 'informational': 0}
                }
            
            ad_group_stats[ad_group]['count'] += 1
            ad_group_stats[ad_group]['total_volume'] += kw.gkp_avg_monthly_searches or 0
            ad_group_stats[ad_group]['avg_cpc_low'] += kw.gkp_top_of_page_bid_low or 0
            ad_group_stats[ad_group]['avg_cpc_high'] += kw.gkp_top_of_page_bid_high or 0
            ad_group_stats[ad_group]['intents'][kw.intent] += 1
        
        # Calculate averages
        for ad_group in ad_group_stats:
            count = ad_group_stats[ad_group]['count']
            if count > 0:
                ad_group_stats[ad_group]['avg_cpc_low'] /= count
                ad_group_stats[ad_group]['avg_cpc_high'] /= count
        
        # Overall statistics
        total_keywords = len(search_keywords)
        total_volume = sum(kw.gkp_avg_monthly_searches or 0 for kw in search_keywords)
        avg_cpc_low = sum(kw.gkp_top_of_page_bid_low or 0 for kw in search_keywords) / total_keywords if total_keywords > 0 else 0
        avg_cpc_high = sum(kw.gkp_top_of_page_bid_high or 0 for kw in search_keywords) / total_keywords if total_keywords > 0 else 0
        
        return {
            'campaign_overview': {
                'total_search_keywords': total_keywords,
                'total_search_volume': total_volume,
                'average_cpc_low': round(avg_cpc_low, 2),
                'average_cpc_high': round(avg_cpc_high, 2),
                'pmax_themes_count': len(campaign_outputs.pmax_themes),
                'shopping_target_cpc': round(campaign_outputs.shopping_target_cpc, 2)
            },
            'ad_group_breakdown': ad_group_stats,
            'budget_recommendations': {
                'search_ads_budget': self.config.ad_budgets.search_ads_budget,
                'shopping_ads_budget': self.config.ad_budgets.shopping_ads_budget,
                'pmax_ads_budget': self.config.ad_budgets.pmax_ads_budget,
                'estimated_monthly_spend': round(total_volume * avg_cpc_low * 0.1, 2),  # Assume 10% click-through rate
                'recommended_budget_allocation': {
                    'search_ads': '60%',
                    'shopping_ads': '25%',
                    'pmax_ads': '15%'
                }
            },
            'performance_insights': {
                'high_volume_keywords': len([kw for kw in search_keywords if (kw.gkp_avg_monthly_searches or 0) >= 1000]),
                'low_competition_opportunities': len([kw for kw in search_keywords if kw.competition == 'low']),
                'transactional_keywords': len([kw for kw in search_keywords if kw.intent == 'transactional']),
                'goldmine_opportunities': len([kw for kw in search_keywords if 'goldmine' in kw.cluster.lower()])
            }
        }
    
    @property
    def target_cpa(self) -> float:
        """Calculate target CPA."""
        total_budget = (
            self.config.ad_budgets.search_ads_budget +
            self.config.ad_budgets.shopping_ads_budget +
            self.config.ad_budgets.pmax_ads_budget
        )
        return total_budget * 0.1  # Assume 10% of budget for target CPA
