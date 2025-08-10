from __future__ import annotations

import yaml
from typing import Any, Dict

from ..core.types import Config, AdBudgets, ProjectSettings


class ConfigValidationError(Exception):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigValidationError(message)


def load_and_validate_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f) or {}

    brand_url = raw.get("brand_url")
    competitor_urls = raw.get("competitor_urls") or []
    service_locations = raw.get("service_locations") or []
    ad_budgets_raw = raw.get("ad_budgets") or {}
    project_settings_raw = raw.get("project_settings") or {}

    _require(isinstance(brand_url, str) and brand_url.startswith("http"),
             "brand_url must be a full URL (http/https)")
    _require(isinstance(competitor_urls, list) and all(isinstance(u, str) for u in competitor_urls),
             "competitor_urls must be a list of URLs")
    _require(isinstance(service_locations, list) and len(service_locations) > 0,
             "service_locations must be a non-empty list")

    ad_budgets = AdBudgets(
        search_ads_budget=float(ad_budgets_raw.get("search_ads_budget", 0)),
        shopping_ads_budget=float(ad_budgets_raw.get("shopping_ads_budget", 0)),
        pmax_ads_budget=float(ad_budgets_raw.get("pmax_ads_budget", 0)),
    )

    _require(ad_budgets.search_ads_budget >= 0 and ad_budgets.shopping_ads_budget >= 0 and ad_budgets.pmax_ads_budget >= 0,
             "ad budgets must be non-negative numbers")

    ps = ProjectSettings(
        assumed_conversion_rate=float(project_settings_raw.get("assumed_conversion_rate", 0.02)),
        min_search_volume_threshold=project_settings_raw.get("min_search_volume_threshold"),
    )

    cfg = Config(
        brand_url=brand_url,
        competitor_urls=competitor_urls,
        service_locations=service_locations,
        ad_budgets=ad_budgets,
        project_settings=ps,
    )
    return cfg


