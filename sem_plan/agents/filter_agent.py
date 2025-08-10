from __future__ import annotations

import re
from typing import Iterable, List, Set, Optional

from ..core.types import RawKeyword
from ..llm import filter_keywords_with_llm


def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _llm_filter_junk(keywords: List[str], *, context: Optional[str] = None) -> Set[str]:
    try:
        kept = filter_keywords_with_llm(keywords, context=context)
        kept_set = {k.lower() for k in kept}
        if kept_set:
            return kept_set
    except Exception:
        pass
    return {k for k in keywords if re.search(r"[a-z]", k) and len(k) >= 3}


def consolidate_and_filter(
    raw: Iterable[RawKeyword], *, min_volume: int | None, llm_context: Optional[str] = None
) -> List[RawKeyword]:
    by_norm: dict[str, RawKeyword] = {}
    for rk in raw:
        norm = _normalize(rk.keyword)
        if not norm:
            continue
        if norm in by_norm:
            existing = by_norm[norm]
            if (rk.volume or 0) > (existing.volume or 0):
                existing.volume = rk.volume
            if rk.competition in {"low", "medium", "high"}:
                existing.competition = rk.competition
            continue
        by_norm[norm] = RawKeyword(
            keyword=norm,
            source=rk.source,
            seed=rk.seed,
            volume=rk.volume,
            competition=rk.competition,
            origin_url=rk.origin_url,
        )

    unique_keywords = list(by_norm.values())

    if min_volume is not None:
        # Prefer GKP-enriched AMS when available
        def ams(rk: RawKeyword) -> int:
            if rk.gkp_avg_monthly_searches is not None:
                return int(rk.gkp_avg_monthly_searches)
            return int(rk.volume or 0)

        unique_keywords = [rk for rk in unique_keywords if ams(rk) >= min_volume]

    keep_set = _llm_filter_junk([rk.keyword for rk in unique_keywords], context=llm_context)
    filtered = [rk for rk in unique_keywords if rk.keyword in keep_set]

    return filtered


