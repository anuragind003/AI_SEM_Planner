from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import pandas as pd

from ..core.types import KeywordRecord, CampaignOutputs, Config


def _compute_shopping_target_cpc(cfg: Config) -> float:
    target_cpa = max(1.0, 0.10 * cfg.ad_budgets.shopping_ads_budget)
    conv_rate = max(0.0001, cfg.project_settings.assumed_conversion_rate)
    return round(target_cpa * conv_rate, 2)


def _derive_pmax_themes(records: List[KeywordRecord]) -> List[str]:
    themes: Dict[str, int] = defaultdict(int)
    for r in records:
        if r.cluster.lower().startswith("competitor"):
            continue
        if r.intent in {"commercial", "transactional"}:
            themes[r.cluster] += 1
    ranked = sorted(themes.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in ranked[:12]]


def assemble_outputs(cfg: Config, records: List[KeywordRecord]) -> CampaignOutputs:
    return CampaignOutputs(
        search_keywords=records,
        pmax_themes=_derive_pmax_themes(records),
        shopping_target_cpc=_compute_shopping_target_cpc(cfg),
    )


def _estimate_cpc_range(competition: str | None, baseline_cpc: float) -> tuple[float, float]:
    low_mult, high_mult = (0.8, 1.1)
    if competition == "medium":
        low_mult, high_mult = (1.1, 1.6)
    elif competition == "high":
        low_mult, high_mult = (1.6, 2.2)
    low = round(baseline_cpc * low_mult, 2)
    high = round(baseline_cpc * high_mult, 2)
    return low, high


def write_outputs_txt_csv(outputs_dir: str, out: CampaignOutputs) -> None:
    import os

    os.makedirs(outputs_dir, exist_ok=True)

    baseline_cpc = out.shopping_target_cpc if out.shopping_target_cpc > 0 else 1.0

    rows = [
        {
            "ad_group": r.cluster,
            "keyword": r.keyword,
            "match_type": r.match_type,
            "intent": r.intent,
            "competition": r.competition,
            "volume": r.volume,
            # Prefer GKP CPC if present; otherwise heuristic
            "cpc_low": (r.gkp_top_of_page_bid_low if r.gkp_top_of_page_bid_low is not None else _estimate_cpc_range(r.competition, baseline_cpc)[0]),
            "cpc_high": (r.gkp_top_of_page_bid_high if r.gkp_top_of_page_bid_high is not None else _estimate_cpc_range(r.competition, baseline_cpc)[1]),
        }
        for r in out.search_keywords
    ]
    df = pd.DataFrame(rows, columns=[
        "ad_group", "keyword", "match_type", "intent", "competition", "volume", "cpc_low", "cpc_high"
    ])
    if not df.empty:
        df.sort_values(["ad_group", "intent", "match_type", "keyword"], inplace=True)
    df.to_csv(os.path.join(outputs_dir, "search_keywords.csv"), index=False)

    pd.DataFrame({"pmax_theme": out.pmax_themes}).to_csv(
        os.path.join(outputs_dir, "pmax_themes.csv"), index=False
    )

    lines: List[str] = []
    lines.append("Search Campaign: Keyword Plan\n")
    by_group: Dict[str, List[KeywordRecord]] = defaultdict(list)
    for r in out.search_keywords:
        by_group[r.cluster].append(r)
    for group, items in sorted(by_group.items()):
        lines.append(f"Ad Group: {group}")
        for r in items:
            comp = r.competition or "-"
            vol = r.volume if r.volume is not None else "-"
            lines.append(f"  - {r.keyword} | {r.match_type} | intent={r.intent} | comp={comp} | vol={vol}")
        lines.append("")

    lines.append("Performance Max Campaign: Thematic Guidance\n")
    for theme in out.pmax_themes:
        lines.append(f"- {theme}")
    lines.append("")

    lines.append("Manual Shopping Campaign: Bidding Strategy\n")
    lines.append(f"Suggested starting Target CPC: ${out.shopping_target_cpc:.2f}")
    lines.append("Prioritize products aligning with the most transactional keywords.")
    lines.append("")
    lines.append("Notes on Methodology (no Keyword Planner):")
    lines.append("- Competition is parsed from free sources or inferred from volume.")
    lines.append("- Search CPC ranges are estimated by scaling a baseline (Shopping Target CPC) with competition multipliers: low ~0.8–1.1x, medium ~1.1–1.6x, high ~1.6–2.2x.")
    lines.append("- Validate against market CPCs before launch; adjust multipliers based on early performance.")

    with open(os.path.join(outputs_dir, "sem_plan.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


