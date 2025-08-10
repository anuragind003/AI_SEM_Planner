from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import yaml
from dataclasses import asdict
from typing import List, Optional

import pandas as pd
import streamlit as st

# Ensure project root is on path when running `streamlit run ui/app.py`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sem_plan.pipeline import run_pipeline  # noqa: E402
from sem_plan.core.types import CampaignOutputs, KeywordRecord  # noqa: E402
from components.form import render_input_form, render_config_upload  # noqa: E402
from components.results import render_comprehensive_results  # noqa: E402
from components.dashboard import render_dashboard  # noqa: E402
from components.downloads import render_download_section  # noqa: E402


st.set_page_config(
    page_title="AI SEM Strategy Generator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _write_temp_config_yaml(data: dict) -> str:
    """Write configuration to temporary YAML file."""
    tmpdir = tempfile.mkdtemp(prefix="sem_plan_")
    path = os.path.join(tmpdir, "config.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    return path


def _load_config_from_yaml(yaml_content: str) -> dict:
    """Load configuration from YAML content."""
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        st.error(f"Invalid YAML format: {e}")
        return None


def _validate_config(config: dict) -> bool:
    """Validate configuration data."""
    required_fields = ['brand_url', 'competitor_urls', 'service_locations', 'ad_budgets']
    for field in required_fields:
        if field not in config:
            st.error(f"Missing required field: {field}")
            return False
    
    if not config['brand_url']:
        st.error("Brand URL is required")
        return False
    
    if not config['competitor_urls']:
        st.error("At least one competitor URL is required")
        return False
    
    if not config['service_locations']:
        st.error("At least one service location is required")
        return False
    
    return True


def _create_config_dict(form_data: tuple) -> dict:
    """Create configuration dictionary from form data."""
    (
        brand_url,
        competitor_urls,
        service_locations,
        budgets,
        project_settings,
        max_serp_queries,
        extra_seeds,
        llm_context,
        use_api_metrics,
    ) = form_data
    
    return {
        "brand_url": brand_url,
        "competitor_urls": competitor_urls,
        "service_locations": service_locations,
        "ad_budgets": {
            "search_ads_budget": budgets["search_ads_budget"],
            "shopping_ads_budget": budgets["shopping_ads_budget"],
            "pmax_ads_budget": budgets["pmax_ads_budget"],
        },
        "project_settings": {
            "assumed_conversion_rate": project_settings["assumed_conversion_rate"],
            "min_search_volume_threshold": project_settings["min_search_volume_threshold"],
        },
    }


def main() -> None:
    # Header
    st.title("📈 AI-Powered SEM Strategy Generator")
    st.caption("Advanced keyword discovery and campaign optimization with multi-source data collection")
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'config_data' not in st.session_state:
        st.session_state.config_data = None
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    input_method = st.sidebar.radio(
        "Input Method",
        ["📝 Form Input", "📁 Config File Upload"],
        help="Choose how to provide your configuration"
    )
    
    # Main content area
    if input_method == "📝 Form Input":
        st.header("📝 Configuration Form")
        form_data = render_input_form()
        
        if st.button("🚀 Generate SEM Strategy", type="primary", use_container_width=True):
            config_dict = _create_config_dict(form_data)
            st.session_state.config_data = config_dict
            
            if _validate_config(config_dict):
                _run_pipeline_and_display_results(config_dict, form_data)
    
    else:  # Config File Upload
        st.header("📁 Configuration File Upload")
        config_dict = render_config_upload()
        
        if config_dict and st.button("🚀 Generate SEM Strategy", type="primary", use_container_width=True):
            st.session_state.config_data = config_dict
            
            if _validate_config(config_dict):
                # Use default values for additional parameters
                default_form_data = (
                    config_dict.get('brand_url', ''),
                    config_dict.get('competitor_urls', []),
                    config_dict.get('service_locations', []),
                    {
                        'search_ads_budget': config_dict.get('ad_budgets', {}).get('search_ads_budget', 5000),
                        'shopping_ads_budget': config_dict.get('ad_budgets', {}).get('shopping_ads_budget', 3000),
                        'pmax_ads_budget': config_dict.get('ad_budgets', {}).get('pmax_ads_budget', 7000),
                    },
                    {
                        'assumed_conversion_rate': config_dict.get('project_settings', {}).get('assumed_conversion_rate', 0.02),
                        'min_search_volume_threshold': config_dict.get('project_settings', {}).get('min_search_volume_threshold', 500),
                    },
                    10,  # max_serp_queries
                    [],  # extra_seeds
                    "",  # llm_context
                    False,  # use_api_metrics
                )
                _run_pipeline_and_display_results(config_dict, default_form_data)
    
    # Display results if available
    if st.session_state.results:
        st.header("📊 Results Dashboard")
        render_dashboard(st.session_state.results, st.session_state.config_data)
        
        st.header("📋 Detailed Results")
        render_comprehensive_results(st.session_state.results)
        
        st.header("💾 Download Results")
        render_download_section(st.session_state.results)


def _run_pipeline_and_display_results(config_dict: dict, form_data: tuple) -> None:
    """Run the pipeline and display results."""
    # Extract additional parameters from form data
    max_serp_queries = form_data[5] if len(form_data) > 5 else 10
    extra_seeds = form_data[6] if len(form_data) > 6 else []
    llm_context = form_data[7] if len(form_data) > 7 else ""
    
    # Create temporary config file
    cfg_path = _write_temp_config_yaml(config_dict)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 Initializing pipeline...")
        progress_bar.progress(10)
        
        status_text.text("🔍 Collecting keywords from multiple sources...")
        progress_bar.progress(30)
        
        status_text.text("📊 Processing and evaluating keywords...")
        progress_bar.progress(60)
        
        status_text.text("🎯 Creating campaign outputs...")
        progress_bar.progress(80)
        
        # Run pipeline
        outputs = run_pipeline(
            config_path=cfg_path,
            outputs_dir=tempfile.mkdtemp(prefix="sem_outputs_"),
            max_serp_queries=max_serp_queries,
            extra_seeds=extra_seeds if extra_seeds else None,
            llm_context=llm_context if llm_context else None,
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        # Store results in session state
        st.session_state.results = outputs
        
        st.success("🎉 SEM Strategy generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        st.exception(e)
    finally:
        progress_bar.empty()
        status_text.empty()


if __name__ == "__main__":
    main()


