from __future__ import annotations

import yaml
from typing import Dict, List, Tuple, Optional

import streamlit as st


def _accent() -> None:
    """Apply custom styling to the UI."""
    st.markdown(
        """
        <style>
        :root {
            --brand-1: #0f172a; /* slate-900 */
            --brand-2: #1e293b; /* slate-800 */
            --accent: #22c55e;  /* emerald-500 */
        }
        .stButton>button {
            background: var(--accent) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.6rem 1rem !important;
            border: none !important;
        }
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea textarea {
            border-radius: 8px !important;
        }
        .metric-card {
            background-color: #f8fafc;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid var(--accent);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_config_upload() -> Optional[Dict]:
    """Render config file upload section."""
    st.subheader("📁 Upload Configuration File")
    
    uploaded_file = st.file_uploader(
        "Choose a YAML configuration file",
        type=['yaml', 'yml'],
        help="Upload your config.yaml file"
    )
    
    if uploaded_file is not None:
        try:
            yaml_content = uploaded_file.read().decode('utf-8')
            config = yaml.safe_load(yaml_content)
            
            if config:
                st.success("✅ Configuration file loaded successfully!")
                
                # Display preview
                with st.expander("📋 Configuration Preview", expanded=True):
                    st.json(config)
                
                return config
            else:
                st.error("❌ Invalid configuration file")
                return None
                
        except yaml.YAMLError as e:
            st.error(f"❌ Error parsing YAML file: {e}")
            return None
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            return None
    
    # Show example config
    with st.expander("📝 Example Configuration", expanded=False):
        example_config = {
            "brand_url": "https://www.example.com",
            "competitor_urls": [
                "https://www.competitor1.com",
                "https://www.competitor2.com"
            ],
            "service_locations": [
                "United States",
                "United Kingdom"
            ],
            "ad_budgets": {
                "search_ads_budget": 5000,
                "shopping_ads_budget": 3000,
                "pmax_ads_budget": 7000
            },
            "project_settings": {
                "assumed_conversion_rate": 0.02,
                "min_search_volume_threshold": 500
            }
        }
        st.code(yaml.dump(example_config, default_flow_style=False), language='yaml')
    
    return None


def render_input_form() -> Tuple:
    """Render the main input form with enhanced organization."""
    _accent()

    # Main form container
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎯 Brand & Competitor Information")
            
            # Brand URL
            brand_url = st.text_input(
                "Brand Website URL",
                value="https://www.cubehq.ai",
                help="Enter your main brand website URL"
            )
            
            # Competitor URLs
            st.write("**Competitor URLs**")
            competitors_text = st.text_area(
                "Enter competitor URLs (one per line)",
                value="https://www.anaplan.com/\nhttps://www.pigment.com/\nhttps://www.workday.com/en-us/products/planning.html",
                height=120,
                help="List your main competitors' websites"
            )
            competitor_urls = [x.strip() for x in competitors_text.splitlines() if x.strip()]
            
            # Service Locations
            st.write("**Service Locations**")
            locations_text = st.text_area(
                "Enter target locations (one per line)",
                value="United States\nUnited Kingdom\nCanada",
                height=120,
                help="List the geographic locations you want to target"
            )
            service_locations = [x.strip() for x in locations_text.splitlines() if x.strip()]
        
        with col2:
            st.subheader("💰 Budget Configuration")
            
            # Budget inputs
            search_budget = st.number_input(
                "Search Ads Budget ($)",
                min_value=0,
                value=5000,
                step=500,
                help="Monthly budget for Search campaigns"
            )
            
            shopping_budget = st.number_input(
                "Shopping Ads Budget ($)",
                min_value=0,
                value=3000,
                step=500,
                help="Monthly budget for Shopping campaigns"
            )
            
            pmax_budget = st.number_input(
                "PMax Ads Budget ($)",
                min_value=0,
                value=7000,
                step=500,
                help="Monthly budget for Performance Max campaigns"
            )
            
            # Budget summary
            total_budget = search_budget + shopping_budget + pmax_budget
            st.metric("Total Monthly Budget", f"${total_budget:,}")
    
    # Project Settings
    st.subheader("⚙️ Project Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        conv_rate = st.number_input(
            "Assumed Conversion Rate",
            min_value=0.001,
            max_value=1.0,
            value=0.02,
            step=0.005,
            format="%.3f",
            help="Expected conversion rate (e.g., 0.02 = 2%)"
        )
    
    with col2:
        min_volume = st.number_input(
            "Min Monthly Searches",
            min_value=0,
            value=500,
            step=50,
            help="Minimum search volume threshold for keywords"
        )
    
    with col3:
        max_serp_queries = st.slider(
            "Max SERP Seeds",
            min_value=1,
            max_value=20,
            value=5,
            help="Maximum number of seed keywords to expand via SERP analysis"
        )
    
    # Advanced Settings
    with st.expander("🔧 Advanced Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            extra_seeds_text = st.text_area(
                "Extra Seed Keywords",
                value="",
                height=80,
                help="Additional seed keywords (comma separated)"
            )
            extra_seeds = [s.strip() for s in extra_seeds_text.split(",") if s.strip()]
            
            llm_context = st.text_area(
                "LLM Context",
                value="B2B FP&A planning software for finance teams",
                height=80,
                help="Business context to guide AI analysis"
            )
        
        with col2:
            use_api_metrics = st.checkbox(
                "Use Google Keyword Planner",
                value=False,
                help="Currently disabled; heuristic metrics will be used"
            )
            
            st.info("💡 **Tip**: The system uses multiple free sources for keyword discovery and doesn't require Google Ads API access.")
    
    # Validation and summary
    if st.button("📋 Validate Configuration", type="secondary"):
        _validate_form_inputs(brand_url, competitor_urls, service_locations, total_budget)
    
    budgets = {
        "search_ads_budget": float(search_budget),
        "shopping_ads_budget": float(shopping_budget),
        "pmax_ads_budget": float(pmax_budget),
    }
    project_settings = {
        "assumed_conversion_rate": float(conv_rate),
        "min_search_volume_threshold": int(min_volume),
    }

    return (
        brand_url,
        competitor_urls,
        service_locations,
        budgets,
        project_settings,
        int(max_serp_queries),
        extra_seeds,
        llm_context,
        use_api_metrics,
    )


def _validate_form_inputs(brand_url: str, competitor_urls: List[str], service_locations: List[str], total_budget: float) -> None:
    """Validate form inputs and show feedback."""
    errors = []
    warnings = []
    
    # Validate brand URL
    if not brand_url:
        errors.append("Brand URL is required")
    elif not brand_url.startswith(('http://', 'https://')):
        errors.append("Brand URL must start with http:// or https://")
    
    # Validate competitors
    if not competitor_urls:
        errors.append("At least one competitor URL is required")
    elif len(competitor_urls) < 2:
        warnings.append("Consider adding more competitors for better keyword discovery")
    
    # Validate locations
    if not service_locations:
        errors.append("At least one service location is required")
    
    # Validate budget
    if total_budget == 0:
        errors.append("Total budget must be greater than 0")
    elif total_budget < 1000:
        warnings.append("Consider increasing budget for better keyword coverage")
    
    # Display results
    if errors:
        st.error("❌ **Validation Errors:**")
        for error in errors:
            st.error(f"• {error}")
    
    if warnings:
        st.warning("⚠️ **Warnings:**")
        for warning in warnings:
            st.warning(f"• {warning}")
    
    if not errors and not warnings:
        st.success("✅ **Configuration is valid!**")
    elif not errors:
        st.success("✅ **Configuration is valid with warnings**")


