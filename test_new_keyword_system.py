#!/usr/bin/env python3
"""
Test script for the new multi-source keyword research system.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sem_plan.core.types import Config, ProjectSettings, AdBudgets
from sem_plan.agents.keyword_agent import gather_keywords, create_advanced_campaign_outputs, create_complete_deliverables


def test_new_keyword_system():
    """Test the new multi-source keyword research system."""
    
    # Create a test configuration
    config = Config(
        brand_url="https://www.myfitnesspal.com",
        competitor_urls=[
            "https://www.fitbit.com",
            "https://www.cronometer.com"
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
    
    print("🚀 Testing new multi-source keyword research system...")
    print(f"Brand URL: {config.brand_url}")
    print(f"Competitors: {config.competitor_urls}")
    print()
    
    try:
        # Test the advanced approach with robust Step 3 & Step 4
        print("🚀 Testing advanced keyword research system with robust evaluation...")
        campaign_outputs = create_advanced_campaign_outputs(
            config, 
            extra_seeds=["planning software", "financial planning"],
            max_serp_queries=3
        )
        
        print(f"✅ Successfully created campaign outputs!")
        print(f"📊 Search Keywords: {len(campaign_outputs.search_keywords)}")
        print(f"🎯 PMax Themes: {len(campaign_outputs.pmax_themes)}")
        print(f"💰 Shopping Target CPC: ${campaign_outputs.shopping_target_cpc:.2f}")
        print()
        
        # Show sample search keywords with ad groups
        print("📊 Sample search keywords by ad group:")
        ad_groups = {}
        for kw in campaign_outputs.search_keywords:
            ad_group = kw.cluster.split('_')[0] if '_' in kw.cluster else 'Other'
            if ad_group not in ad_groups:
                ad_groups[ad_group] = []
            ad_groups[ad_group].append(kw)
        
        for ad_group, keywords in list(ad_groups.items())[:5]:  # Show top 5 ad groups
            print(f"\n🎯 {ad_group} ({len(keywords)} keywords):")
            for i, kw in enumerate(keywords[:3]):  # Show top 3 keywords per group
                print(f"  {i+1}. {kw.keyword} ({kw.match_type}, Volume: {kw.gkp_avg_monthly_searches})")
        
        # Show PMax themes
        print(f"\n🎯 PMax Themes ({len(campaign_outputs.pmax_themes)}):")
        for i, theme in enumerate(campaign_outputs.pmax_themes[:5]):
            print(f"  {i+1}. {theme}")
        
        print()
        print("🎉 Advanced keyword system test completed successfully!")
        
        # Test deliverables generation
        print("\n📄 Testing deliverables generation...")
        deliverables = create_complete_deliverables(
            config, 
            extra_seeds=["planning software", "financial planning"],
            max_serp_queries=3,
            output_dir="test_outputs"
        )
        
        print("✅ Deliverables generated successfully!")
        print("📁 Generated files:")
        for deliverable_type, file_path in deliverables.items():
            print(f"  - {deliverable_type}: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing new keyword system: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_new_keyword_system()
    sys.exit(0 if success else 1)
