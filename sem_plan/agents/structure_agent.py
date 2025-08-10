from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional

from ..core.types import KeywordRecord, RawKeyword
from ..llm import cluster_keywords_with_llm


INTENTS = ["informational", "navigational", "commercial", "transactional"]


def _infer_intent_heuristic(keyword: str) -> str:
    k = keyword.lower()
    if any(t in k for t in ["buy", "pricing", "price", "demo", "trial", "quote"]):
        return "transactional"
    if any(t in k for t in ["vs", "compare", "alternatives", "competitor"]):
        return "commercial"
    if any(t in k for t in ["what is", "how to", "guide", "tutorial"]):
        return "informational"
    if any(t in k for t in ["login", "signin", "homepage", "official"]):
        return "navigational"
    return "commercial"


def _suggest_match_type(keyword: str, intent: str) -> str:
    if intent == "transactional" or re.search(r"\b(buy|pricing|price|demo|trial|quote)\b", keyword.lower()):
        return "exact"
    if len(keyword.split()) >= 3:
        return "phrase"
    return "broad"


def _qualitative_competition(rk: RawKeyword) -> str | None:
    if rk.competition in {"low", "medium", "high"}:
        return rk.competition
    if rk.volume is not None:
        if rk.volume >= 5000:
            return "high"
        if rk.volume >= 1000:
            return "medium"
        return "low"
    return None


def _cluster_heuristic(keywords: List[str], *, brand_terms: Optional[List[str]] = None, competitor_terms: Optional[List[str]] = None, locations: Optional[List[str]] = None) -> Dict[str, List[str]]:
    clusters: Dict[str, List[str]] = defaultdict(list)
    for k in keywords:
        low = k.lower()
        # brand
        if brand_terms and any(bt in low for bt in brand_terms):
            clusters["Brand Terms"].append(k)
            continue
        # competitors
        if competitor_terms and any(ct in low for ct in competitor_terms):
            # Try to label by the matching competitor token
            matched = next((ct for ct in competitor_terms if ct in low), None)
            group = f"Competitor: {matched}" if matched else "Competitor Terms"
            clusters[group].append(k)
            continue
        # locations
        if locations and any(loc.lower() in low for loc in locations):
            clusters["Location-based Queries"].append(k)
            continue
        # heuristics for categories
        if any(t in low for t in ["buy", "pricing", "price", "demo", "trial", "quote", "near me", "best"]):
            clusters["Category: Transactional"].append(k)
        elif any(t in low for t in ["vs", "compare", "alternatives", "competitor"]):
            clusters["Category: Commercial"].append(k)
        elif any(t in low for t in ["what is", "how to", "guide", "tutorial", "benefits", "ideas"]):
            clusters["Long-Tail Informational Queries"].append(k)
        else:
            clusters["Category: General"].append(k)
    return clusters


def _cluster_with_llm(keywords: List[str], *, context: Optional[str] = None, brand_terms: Optional[List[str]] = None, competitor_terms: Optional[List[str]] = None, locations: Optional[List[str]] = None) -> Dict[str, List[str]]:
    try:
        clusters = cluster_keywords_with_llm(keywords, context=context)
        if clusters:
            return {g: [k.lower() for k in ks] for g, ks in clusters.items()}
    except Exception:
        pass
    return _cluster_heuristic(keywords, brand_terms=brand_terms, competitor_terms=competitor_terms, locations=locations)


def structure_keywords(filtered: List[RawKeyword], *, llm_context: Optional[str] = None, brand_terms: Optional[List[str]] = None, competitor_terms: Optional[List[str]] = None, locations: Optional[List[str]] = None) -> List[KeywordRecord]:
    intents: Dict[str, str] = {}
    comp_map: Dict[str, str | None] = {}
    volume_map: Dict[str, int | None] = {}
    for rk in filtered:
        intents[rk.keyword] = _infer_intent_heuristic(rk.keyword)
        comp_map[rk.keyword] = _qualitative_competition(rk)
        volume_map[rk.keyword] = rk.volume

    clusters = _cluster_with_llm([rk.keyword for rk in filtered], context=llm_context, brand_terms=brand_terms, competitor_terms=competitor_terms, locations=locations)

    records: List[KeywordRecord] = []
    for cluster_name, kws in clusters.items():
        for k in kws:
            if k not in intents:
                intents[k] = _infer_intent_heuristic(k)
            mt = _suggest_match_type(k, intents[k])
            # carry GKP CPC if available from the source RawKeyword
            gkp_low = None
            gkp_high = None
            # We look up in filtered list to find the original rk
            for rk in filtered:
                if rk.keyword == k:
                    # carry AMS and CPC if present
                    if hasattr(rk, "gkp_avg_monthly_searches"):
                        pass
                    gkp_low = rk.gkp_top_of_page_bid_low
                    gkp_high = rk.gkp_top_of_page_bid_high
                    gkp_ams = rk.gkp_avg_monthly_searches
                    break
            rec = KeywordRecord(
                keyword=k,
                normalized=k,
                intent=intents[k],
                cluster=cluster_name,
                match_type=mt,
                competition=comp_map.get(k),
                volume=volume_map.get(k),
                sources=[],
                gkp_avg_monthly_searches=gkp_ams if 'gkp_ams' in locals() else None,
                gkp_top_of_page_bid_low=gkp_low,
                gkp_top_of_page_bid_high=gkp_high,
            )
            records.append(rec)
    return records


