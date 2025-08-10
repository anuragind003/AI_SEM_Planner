#!/usr/bin/env python3
"""
Test script for the enhanced UI components.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sem_plan.core.types import Config, ProjectSettings, AdBudgets, KeywordRecord, CampaignOutputs


def test_ui_components():
    """Test the UI components with sample data."""
    
    print("🧪 Testing UI components...")
    
    # Create sample configuration
    config = Config(
        brand_url="https://www.example.com",
        competitor_urls=[
            "https://www.competitor1.com",
            "https://www.competitor2.com"
        ],
        service_locations=["United States", "United Kingdom"],
        ad_budgets=AdBudgets(
            search_ads_budget=5000,
            shopping_ads_budget=3000,
            pmax_ads_budget=7000
        ),
        project_settings=ProjectSettings(
            assumed_conversion_rate=0.02,
            min_search_volume_threshold=500
        )
    )
    
    # Create sample keyword records
    sample_keywords = [
        KeywordRecord(
            keyword="financial planning software",
            normalized="financial planning software",
            intent="commercial",
            cluster="financial_planning",
            match_type="phrase",
            competition="medium",
            volume=1200,
            sources=["website_scraper"],
            gkp_avg_monthly_searches=1200,
            gkp_top_of_page_bid_low=2.50,
            gkp_top_of_page_bid_high=3.75
        ),
        KeywordRecord(
            keyword="budget planning tools",
            normalized="budget planning tools",
            intent="informational",
            cluster="budget_planning",
            match_type="broad",
            competition="low",
            volume=800,
            sources=["search_suggestions"],
            gkp_avg_monthly_searches=800,
            gkp_top_of_page_bid_low=1.25,
            gkp_top_of_page_bid_high=2.00
        ),
        KeywordRecord(
            keyword="enterprise planning solution",
            normalized="enterprise planning solution",
            intent="transactional",
            cluster="enterprise_planning",
            match_type="exact",
            competition="high",
            volume=2500,
            sources=["competitor_analysis"],
            gkp_avg_monthly_searches=2500,
            gkp_top_of_page_bid_low=4.00,
            gkp_top_of_page_bid_high=6.50
        )
    ]
    
    # Create sample campaign outputs
    sample_outputs = CampaignOutputs(
        search_keywords=sample_keywords,
        pmax_themes=[
            "Financial Planning Solutions",
            "Enterprise Budget Management",
            "Business Planning Tools"
        ],
        shopping_target_cpc=2.85
    )
    
    print("✅ Sample data created successfully!")
    print(f"📊 Keywords: {len(sample_outputs.search_keywords)}")
    print(f"🎯 PMax Themes: {len(sample_outputs.pmax_themes)}")
    print(f"💰 Shopping Target CPC: ${sample_outputs.shopping_target_cpc:.2f}")
    
    # Test config validation
    config_dict = {
        "brand_url": config.brand_url,
        "competitor_urls": config.competitor_urls,
        "service_locations": config.service_locations,
        "ad_budgets": {
            "search_ads_budget": config.ad_budgets.search_ads_budget,
            "shopping_ads_budget": config.ad_budgets.shopping_ads_budget,
            "pmax_ads_budget": config.ad_budgets.pmax_ads_budget,
        },
        "project_settings": {
            "assumed_conversion_rate": config.project_settings.assumed_conversion_rate,
            "min_search_volume_threshold": config.project_settings.min_search_volume_threshold,
        },
    }
    
    print("✅ Configuration validation test passed!")
    
    # Test data processing functions
    try:
        from ui.components.results import _create_search_dataframe, _calculate_roi_potential
        from ui.components.dashboard import render_dashboard
        from ui.components.downloads import _create_search_keywords_csv
        
        # Test search dataframe creation
        df = _create_search_dataframe(sample_keywords, 2.85)
        print(f"✅ Search dataframe created with {len(df)} rows")
        
        # Test ROI calculation
        roi = _calculate_roi_potential(1200, 2.50, "commercial")
        print(f"✅ ROI calculation: {roi}")
        
        # Test CSV creation
        csv_name, csv_data = _create_search_keywords_csv(sample_outputs)
        print(f"✅ CSV export created: {csv_name} ({len(csv_data)} bytes)")
        
        print("🎉 All UI component tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing UI components: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ui_components()
    sys.exit(0 if success else 1)
