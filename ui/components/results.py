from __future__ import annotations

from typing import Dict, List
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

from sem_plan.core.types import CampaignOutputs, KeywordRecord


def _estimate_cpc_range(competition: str | None, baseline_cpc: float) -> tuple[float, float]:
    """Estimate CPC range based on competition level."""
    low_mult, high_mult = (0.8, 1.1)
    if competition == "medium":
        low_mult, high_mult = (1.1, 1.6)
    elif competition == "high":
        low_mult, high_mult = (1.6, 2.2)
    low = round(baseline_cpc * low_mult, 2)
    high = round(baseline_cpc * high_mult, 2)
    return low, high


def _create_search_dataframe(records: List[KeywordRecord], baseline_cpc: float) -> pd.DataFrame:
    """Create comprehensive search keywords dataframe."""
    data = []
    for r in records:
        # Get CPC values
        cpc_low = r.gkp_top_of_page_bid_low if r.gkp_top_of_page_bid_low is not None else _estimate_cpc_range(r.competition, baseline_cpc)[0]
        cpc_high = r.gkp_top_of_page_bid_high if r.gkp_top_of_page_bid_high is not None else _estimate_cpc_range(r.competition, baseline_cpc)[1]
        
        # Get search volume - ensure it's an integer
        search_volume = r.gkp_avg_monthly_searches if getattr(r, "gkp_avg_monthly_searches", None) is not None else r.volume
        # Convert to int, handling None and string values
        if search_volume is not None:
            try:
                search_volume = int(search_volume)
            except (ValueError, TypeError):
                search_volume = 0
        else:
            search_volume = 0
        
        data.append({
            "Ad Group": r.cluster,
            "Keyword": r.keyword,
            "Match Type": r.match_type,
            "Intent": r.intent,
            "Competition": r.competition or "medium",
            "Avg Monthly Searches": search_volume,
            "CPC Low ($)": cpc_low,
            "CPC High ($)": cpc_high,
            "CPC Range": f"${cpc_low:.2f} - ${cpc_high:.2f}",
            "Sources": ", ".join(r.sources) if r.sources else "Unknown",
            "Estimated Monthly Cost": search_volume * cpc_low if search_volume and cpc_low else 0,
            "ROI Potential": _calculate_roi_potential(search_volume, cpc_low, r.intent)
        })
    
    df = pd.DataFrame(data)
    return df.sort_values(["Ad Group", "Avg Monthly Searches"], ascending=[True, False]) if not df.empty else df


def _calculate_roi_potential(volume: int, cpc: float, intent: str) -> str:
    """Calculate ROI potential based on volume, CPC, and intent."""
    if volume == 0 or cpc == 0:
        return "Unknown"
    
    # Base score on volume and CPC efficiency
    volume_score = min(volume / 1000, 5)  # Cap at 5
    cpc_efficiency = max(1 - (cpc / 5), 0)  # Lower CPC is better
    
    # Intent multiplier
    intent_multiplier = {
        "transactional": 1.5,
        "commercial": 1.2,
        "informational": 0.8,
        "navigational": 0.6
    }.get(intent, 1.0)
    
    total_score = (volume_score + cpc_efficiency) * intent_multiplier
    
    if total_score >= 4:
        return "🔥 High"
    elif total_score >= 2:
        return "⚡ Medium"
    else:
        return "📊 Low"


def render_comprehensive_results(outputs: CampaignOutputs) -> None:
    """Render comprehensive results with detailed analysis."""
    
    # Overview metrics
    st.subheader("📊 Campaign Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Keywords", len(outputs.search_keywords))
    with col2:
        st.metric("PMax Themes", len(outputs.pmax_themes))
    with col3:
        st.metric("Shopping Target CPC", f"${outputs.shopping_target_cpc:.2f}")
    with col4:
        # Calculate total volume with proper type handling
        total_volume = 0
        for kw in outputs.search_keywords:
            volume = kw.gkp_avg_monthly_searches or kw.volume or 0
            if volume is not None:
                try:
                    total_volume += int(volume)
                except (ValueError, TypeError):
                    continue
        st.metric("Total Search Volume", f"{total_volume:,}")
    
    # Search Campaign Details
    st.subheader("🔍 Search Campaign: Detailed Keyword Analysis")
    
    baseline_cpc = outputs.shopping_target_cpc if outputs.shopping_target_cpc > 0 else 1.0
    search_df = _create_search_dataframe(outputs.search_keywords, baseline_cpc)
    
    if not search_df.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            ad_groups = ["All"] + sorted(search_df["Ad Group"].unique().tolist())
            selected_ad_group = st.selectbox("Filter by Ad Group", ad_groups)
        
        with col2:
            intents = ["All"] + sorted(search_df["Intent"].unique().tolist())
            selected_intent = st.selectbox("Filter by Intent", intents)
        
        with col3:
            competitions = ["All"] + sorted(search_df["Competition"].unique().tolist())
            selected_competition = st.selectbox("Filter by Competition", competitions)
        
        # Apply filters
        filtered_df = search_df.copy()
        if selected_ad_group != "All":
            filtered_df = filtered_df[filtered_df["Ad Group"] == selected_ad_group]
        if selected_intent != "All":
            filtered_df = filtered_df[filtered_df["Intent"] == selected_intent]
        if selected_competition != "All":
            filtered_df = filtered_df[filtered_df["Competition"] == selected_competition]
        
        # Display filtered results
        st.dataframe(
            filtered_df[["Ad Group", "Keyword", "Match Type", "Intent", "Competition", 
                        "Avg Monthly Searches", "CPC Range", "ROI Potential"]],
            use_container_width=True,
            height=400
        )
        
        # Detailed view in expandable section
        with st.expander("📋 Detailed Keyword Data", expanded=False):
            st.dataframe(filtered_df, use_container_width=True)
        
        # Analytics
        _render_search_analytics(filtered_df)
    
    # PMax Themes
    st.subheader("🎯 Performance Max: Campaign Themes")
    if outputs.pmax_themes:
        # Display themes in cards
        cols = st.columns(3)
        for idx, theme in enumerate(outputs.pmax_themes):
            with cols[idx % 3]:
                st.info(f"**{theme}**")
        
        # Theme analysis
        with st.expander("📊 PMax Theme Analysis", expanded=False):
            theme_categories = [_categorize_pmax_theme(theme) for theme in outputs.pmax_themes]
            theme_df = pd.DataFrame({
                "Theme": outputs.pmax_themes,
                "Category": theme_categories
            })
            st.dataframe(theme_df, use_container_width=True)
    else:
        st.info("No PMax themes derived from the keyword analysis.")
    
    # Shopping Campaign
    st.subheader("🛒 Shopping Campaign: CPC Strategy")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Target CPC", f"${outputs.shopping_target_cpc:.2f}")
        st.caption("Based on budget and conversion rate")
    
    with col2:
        # Calculate shopping metrics
        total_budget = 0
        for kw in outputs.search_keywords:
            volume = kw.gkp_avg_monthly_searches
            if volume is not None:
                try:
                    volume = int(volume)
                    cpc = kw.gkp_top_of_page_bid_low or 1.0
                    total_budget += volume * cpc
                except (ValueError, TypeError):
                    continue
        st.metric("Estimated Monthly Spend", f"${total_budget:.0f}")
    
    # Shopping recommendations
    with st.expander("💡 Shopping Campaign Recommendations", expanded=False):
        st.write("**Recommended Strategy:**")
        st.write("• Start with the suggested target CPC")
        st.write("• Monitor performance for first 2 weeks")
        st.write("• Adjust bids based on conversion data")
        st.write("• Focus on high-converting product categories")


def _render_search_analytics(df: pd.DataFrame) -> None:
    """Render search campaign analytics."""
    st.subheader("📈 Search Campaign Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ad Group Distribution
        if not df.empty:
            ad_group_counts = df["Ad Group"].value_counts()
            fig = px.pie(
                values=ad_group_counts.values,
                names=ad_group_counts.index,
                title="Keywords by Ad Group"
            )
            st.plotly_chart(fig, use_container_width=True, key="ad_group_pie")
    
    with col2:
        # Intent Distribution
        if not df.empty:
            intent_counts = df["Intent"].value_counts()
            fig = px.bar(
                x=intent_counts.index,
                y=intent_counts.values,
                title="Keywords by Intent",
                labels={"x": "Intent", "y": "Count"}
            )
            st.plotly_chart(fig, use_container_width=True, key="intent_bar")
    
    # Competition Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        if not df.empty:
            competition_counts = df["Competition"].value_counts()
            fig = px.pie(
                values=competition_counts.values,
                names=competition_counts.index,
                title="Keywords by Competition Level"
            )
            st.plotly_chart(fig, use_container_width=True, key="competition_pie")
    
    with col2:
        # Volume vs CPC Scatter
        if not df.empty and "Avg Monthly Searches" in df.columns and "CPC Low ($)" in df.columns:
            fig = px.scatter(
                df,
                x="Avg Monthly Searches",
                y="CPC Low ($)",
                color="Intent",
                size="Avg Monthly Searches",
                hover_data=["Keyword", "Ad Group"],
                title="Search Volume vs CPC"
            )
            st.plotly_chart(fig, use_container_width=True, key="volume_cpc_scatter")


def _categorize_pmax_theme(theme: str) -> str:
    """Categorize PMax theme based on content."""
    theme_lower = theme.lower()
    
    if any(word in theme_lower for word in ["product", "service", "solution"]):
        return "Product Category"
    elif any(word in theme_lower for word in ["use", "case", "scenario", "workflow"]):
        return "Use Case"
    elif any(word in theme_lower for word in ["professional", "business", "enterprise", "team"]):
        return "Demographic"
    elif any(word in theme_lower for word in ["seasonal", "event", "time", "period"]):
        return "Seasonal/Event"
    else:
        return "General"


def render_results(outputs: CampaignOutputs) -> None:
    """Legacy function for backward compatibility."""
    render_comprehensive_results(outputs)


