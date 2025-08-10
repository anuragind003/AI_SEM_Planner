from __future__ import annotations

import re
from typing import Iterable, List, Optional
from urllib.parse import urlparse

from ..core.types import RawKeyword, Config, KeywordRecord, CampaignOutputs
from ..utils.cache import load_cache, save_cache

# Import the new specialized modules
from .keyword_collectors.website_scraper import WebsiteScraper
from .keyword_collectors.search_suggestions import SearchSuggestionsCollector
from .keyword_collectors.public_tools import PublicToolsCollector
from .keyword_processors.text_cleaner import TextCleaner
from .keyword_processors.candidate_generator import CandidateGenerator
from .keyword_processors.relevance_filter import RelevanceFilter
from .keyword_processors.expansion_engine import ExpansionEngine
from .keyword_processors.scoring_engine import ScoringEngine
from .keyword_processors.consolidation_engine import ConsolidationEngine
from .keyword_processors.advanced_evaluation_engine import AdvancedEvaluationEngine
from .keyword_processors.ad_group_segmentation_engine import AdGroupSegmentationEngine
from .keyword_processors.deliverables_generator import DeliverablesGenerator


def gather_keywords(cfg: Config, *, extra_seeds: Iterable[str] | None = None, max_serp_queries: int = 10) -> List[RawKeyword]:
    """Main function to collect keywords using the new multi-source approach."""
    raw_keywords: List[RawKeyword] = []
    
    # 1. Website scraping (Brand + Competitors)
    print("🔍 Scraping websites...")
    with WebsiteScraper(cfg) as scraper:
        raw_keywords.extend(scraper.scrape_all_websites())
    
    # 2. Search-based keyword suggestions
    print("🔍 Collecting search-based suggestions...")
    search_collector = SearchSuggestionsCollector(cfg)
    raw_keywords.extend(search_collector.collect_suggestions(extra_seeds, max_serp_queries))
    
    # 3. Public keyword tools
    print("🔍 Using public keyword tools...")
    tools_collector = PublicToolsCollector(cfg)
    raw_keywords.extend(tools_collector.collect_from_tools())
    
    # 4. Text cleaning and structuring
    print("🧹 Cleaning and structuring text...")
    cleaner = TextCleaner()
    raw_keywords = cleaner.clean_and_structure(raw_keywords)
    
    # 5. Candidate keyword generation
    print("🔧 Generating candidate keywords...")
    generator = CandidateGenerator()
    raw_keywords.extend(generator.generate_candidates(raw_keywords))
    
    # 6. Relevance filtering
    print("🎯 Filtering for relevance...")
    filter_engine = RelevanceFilter(cfg)
    raw_keywords = filter_engine.filter_keywords(raw_keywords)
    
    # 7. Expansion without paid APIs
    print("📈 Expanding keywords...")
    expansion_engine = ExpansionEngine(cfg)
    raw_keywords.extend(expansion_engine.expand_keywords(raw_keywords))
    
    # 8. Scoring and prioritization
    print("📊 Scoring and prioritizing...")
    scoring_engine = ScoringEngine(cfg)
    raw_keywords = scoring_engine.score_and_prioritize(raw_keywords)
    
    return raw_keywords


def create_advanced_campaign_outputs(cfg: Config, *, extra_seeds: Iterable[str] | None = None, max_serp_queries: int = 10) -> CampaignOutputs:
    """Advanced function that implements the robust Step 3 & Step 4 approach."""
    
    # Steps 1-8: Collect raw keywords (same as before)
    raw_keywords = gather_keywords(cfg, extra_seeds=extra_seeds, max_serp_queries=max_serp_queries)
    
    # Step 3: Keyword Consolidation & Filtering
    print("🔄 Consolidating and filtering keywords...")
    consolidation_engine = ConsolidationEngine(cfg)
    consolidated_keywords = consolidation_engine.consolidate_keywords(raw_keywords)
    
    # Step 4: Advanced Evaluation & Scoring
    print("📊 Applying advanced evaluation criteria...")
    evaluation_engine = AdvancedEvaluationEngine(cfg)
    evaluated_keywords = evaluation_engine.evaluate_and_score(consolidated_keywords)
    
    # Step 5: Ad Group Segmentation & Campaign Outputs
    print("🎯 Creating ad groups and campaign themes...")
    segmentation_engine = AdGroupSegmentationEngine(cfg)
    campaign_outputs = segmentation_engine.create_campaign_outputs(evaluated_keywords)
    
    return campaign_outputs


def create_complete_deliverables(cfg: Config, *, extra_seeds: Iterable[str] | None = None, max_serp_queries: int = 10, output_dir: str = "outputs") -> Dict[str, str]:
    """Create complete deliverables including all files and reports."""
    
    # Get campaign outputs
    campaign_outputs = create_advanced_campaign_outputs(cfg, extra_seeds=extra_seeds, max_serp_queries=max_serp_queries)
    
    # Generate deliverables
    print("📄 Generating deliverables...")
    deliverables_generator = DeliverablesGenerator(cfg)
    deliverables = deliverables_generator.generate_deliverables(campaign_outputs, output_dir)
    
    return deliverables


def enrich_keywords_with_heuristic_metrics(keywords: List[RawKeyword]) -> List[RawKeyword]:
    """Legacy function - metrics are now calculated during collection."""
    return keywords  # Already enriched in the new approach


# Legacy helper functions for backward compatibility
def _extract_terms_from_url(url: str) -> List[str]:
    """Extract meaningful terms from URL."""
    try:
        parsed = urlparse(url)
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


