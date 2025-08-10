from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Optional

from sem_plan.core.types import CampaignOutputs


def render_dashboard(outputs: CampaignOutputs, config_data: Optional[Dict] = None) -> None:
    """Render the main dashboard with key metrics and insights."""
    
    # Key Performance Indicators
    st.subheader("🎯 Key Performance Indicators")
    
    # Calculate metrics
    total_keywords = len(outputs.search_keywords)
    
    # Calculate total volume with proper type handling
    total_volume = 0
    for kw in outputs.search_keywords:
        volume = kw.gkp_avg_monthly_searches or kw.volume or 0
        if volume is not None:
            try:
                total_volume += int(volume)
            except (ValueError, TypeError):
                continue
    
    avg_cpc = outputs.shopping_target_cpc
    
    # Budget allocation
    if config_data and 'ad_budgets' in config_data:
        search_budget = config_data['ad_budgets'].get('search_ads_budget', 0)
        shopping_budget = config_data['ad_budgets'].get('shopping_ads_budget', 0)
        pmax_budget = config_data['ad_budgets'].get('pmax_ads_budget', 0)
        total_budget = search_budget + shopping_budget + pmax_budget
    else:
        total_budget = 15000  # Default
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Keywords",
            f"{total_keywords:,}",
            help="Number of keywords discovered and analyzed"
        )
    
    with col2:
        st.metric(
            "Total Search Volume",
            f"{total_volume:,}",
            help="Combined monthly search volume across all keywords"
        )
    
    with col3:
        st.metric(
            "Avg Target CPC",
            f"${avg_cpc:.2f}",
            help="Average cost-per-click target for campaigns"
        )
    
    with col4:
        st.metric(
            "Total Budget",
            f"${total_budget:,}",
            help="Monthly advertising budget across all campaigns"
        )
    
    # Campaign Distribution
    st.subheader("📊 Campaign Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Budget Distribution
        if config_data and 'ad_budgets' in config_data:
            budget_data = {
                'Search Ads': search_budget,
                'Shopping Ads': shopping_budget,
                'PMax Ads': pmax_budget
            }
            
            fig = px.pie(
                values=list(budget_data.values()),
                names=list(budget_data.keys()),
                title="Budget Distribution by Campaign Type"
            )
            st.plotly_chart(fig, use_container_width=True, key="budget_distribution_pie")
    
    with col2:
        # Keyword Distribution by Intent
        if outputs.search_keywords:
            intent_counts = {}
            for kw in outputs.search_keywords:
                intent = kw.intent
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            if intent_counts:
                fig = px.bar(
                    x=list(intent_counts.keys()),
                    y=list(intent_counts.values()),
                    title="Keywords by Intent",
                    labels={"x": "Intent", "y": "Count"}
                )
                st.plotly_chart(fig, use_container_width=True, key="dashboard_intent_bar")
    
    # Top Performing Keywords
    st.subheader("🏆 Top Performing Keywords")
    
    if outputs.search_keywords:
        # Sort by search volume
        def get_volume(kw):
            volume = kw.gkp_avg_monthly_searches or kw.volume or 0
            if volume is not None:
                try:
                    return int(volume)
                except (ValueError, TypeError):
                    return 0
            return 0
        
        sorted_keywords = sorted(
            outputs.search_keywords,
            key=get_volume,
            reverse=True
        )
        
        # Create top keywords dataframe
        top_keywords_data = []
        for i, kw in enumerate(sorted_keywords[:10]):
            # Ensure volume is an integer
            volume = kw.gkp_avg_monthly_searches or kw.volume or 0
            if volume is not None:
                try:
                    volume = int(volume)
                except (ValueError, TypeError):
                    volume = 0
            else:
                volume = 0
            
            cpc_low = kw.gkp_top_of_page_bid_low or 1.0
            top_keywords_data.append({
                "Rank": i + 1,
                "Keyword": kw.keyword,
                "Ad Group": kw.cluster,
                "Search Volume": volume,
                "CPC": f"${cpc_low:.2f}",
                "Intent": kw.intent,
                "Competition": kw.competition or "medium"
            })
        
        top_df = pd.DataFrame(top_keywords_data)
        st.dataframe(top_df, use_container_width=True)
    
    # Strategic Insights
    st.subheader("💡 Strategic Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**🎯 Campaign Recommendations**")
        
        if outputs.search_keywords:
            # Analyze keyword distribution
            high_volume_keywords = []
            for kw in outputs.search_keywords:
                volume = kw.gkp_avg_monthly_searches or kw.volume or 0
                if volume is not None:
                    try:
                        volume = int(volume)
                        if volume > 1000:
                            high_volume_keywords.append(kw)
                    except (ValueError, TypeError):
                        continue
            low_competition_keywords = [kw for kw in outputs.search_keywords 
                                      if kw.competition == "low"]
            
            st.write(f"• **{len(high_volume_keywords)}** high-volume keywords (>1K searches)")
            st.write(f"• **{len(low_competition_keywords)}** low-competition opportunities")
            st.write(f"• **{len(outputs.pmax_themes)}** PMax themes identified")
            
            if high_volume_keywords:
                st.write("• Focus on high-volume keywords for immediate impact")
            if low_competition_keywords:
                st.write("• Target low-competition keywords for cost efficiency")
    
    with col2:
        st.info("**💰 Budget Optimization**")
        
        if config_data and 'project_settings' in config_data:
            conv_rate = config_data['project_settings'].get('assumed_conversion_rate', 0.02)
            target_cpa = total_budget / (total_volume * conv_rate) if total_volume > 0 else 0
            
            st.write(f"• Target CPA: **${target_cpa:.2f}**")
            st.write(f"• Conversion Rate: **{conv_rate:.1%}**")
            st.write(f"• Expected Conversions: **{total_volume * conv_rate:.0f}**")
            
            if avg_cpc > target_cpa:
                st.warning("⚠️ Average CPC exceeds target CPA - consider bid optimization")
            else:
                st.success("✅ CPC targets align with CPA goals")
    
    # Performance Summary
    with st.expander("📈 Performance Summary", expanded=False):
        if outputs.search_keywords:
            # Calculate performance metrics
            total_estimated_cost = 0
            for kw in outputs.search_keywords:
                volume = kw.gkp_avg_monthly_searches or 0
                if volume is not None:
                    try:
                        volume = int(volume)
                        cpc = kw.gkp_top_of_page_bid_low or 1.0
                        total_estimated_cost += volume * cpc
                    except (ValueError, TypeError):
                        continue
            
            avg_volume = total_volume / len(outputs.search_keywords) if outputs.search_keywords else 0
            
            summary_data = {
                "Metric": [
                    "Total Keywords",
                    "Average Search Volume",
                    "Total Monthly Volume",
                    "Average CPC",
                    "Estimated Monthly Cost",
                    "Budget Utilization"
                ],
                "Value": [
                    str(total_keywords),
                    str(f"{avg_volume:.0f}"),
                    str(f"{total_volume:,}"),
                    str(f"${avg_cpc:.2f}"),
                    str(f"${total_estimated_cost:.0f}"),
                    str(f"{(total_estimated_cost/total_budget)*100:.1f}%" if total_budget > 0 else "N/A")
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
