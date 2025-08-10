from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal


@dataclass
class AdBudgets:
    search_ads_budget: float
    shopping_ads_budget: float
    pmax_ads_budget: float


@dataclass
class ProjectSettings:
    assumed_conversion_rate: float = 0.02
    min_search_volume_threshold: Optional[int] = None


@dataclass
class Config:
    brand_url: str
    competitor_urls: List[str]
    service_locations: List[str]
    ad_budgets: AdBudgets
    project_settings: ProjectSettings = field(default_factory=ProjectSettings)


@dataclass
class GkpMetrics:
    avg_monthly_searches: Optional[int] = None
    top_of_page_bid_low: Optional[float] = None
    top_of_page_bid_high: Optional[float] = None
    competition: Optional[Literal["low", "medium", "high"]] = None


@dataclass
class GoogleAdsCredentials:
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    login_customer_id: str


@dataclass
class RawKeyword:
    keyword: str
    source: Literal[
        "brand_tool",
        "competitor_tool",
        "serp_related",
        "serp_paa",
        "seed_extra",
    ]
    seed: Optional[str] = None
    volume: Optional[int] = None
    competition: Optional[Literal["low", "medium", "high"]] = None
    origin_url: Optional[str] = None
    # Optional GKP enrichment
    gkp_avg_monthly_searches: Optional[int] = None
    gkp_top_of_page_bid_low: Optional[float] = None
    gkp_top_of_page_bid_high: Optional[float] = None
    gkp_competition: Optional[Literal["low", "medium", "high"]] = None


@dataclass
class KeywordRecord:
    keyword: str
    normalized: str
    intent: Literal["informational", "navigational", "commercial", "transactional"]
    cluster: str
    match_type: Literal["broad", "phrase", "exact"]
    competition: Optional[Literal["low", "medium", "high"]]
    volume: Optional[int]
    sources: List[str]
    # Optional GKP enrichment carried to outputs
    gkp_avg_monthly_searches: Optional[int] = None
    gkp_top_of_page_bid_low: Optional[float] = None
    gkp_top_of_page_bid_high: Optional[float] = None


@dataclass
class CampaignOutputs:
    search_keywords: List[KeywordRecord]
    pmax_themes: List[str]
    shopping_target_cpc: float


