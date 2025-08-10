from __future__ import annotations

from typing import Iterable, Optional

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from .agents.config_agent import load_and_validate_config
from .agents.keyword_agent import gather_keywords, enrich_keywords_with_heuristic_metrics
from .agents.filter_agent import consolidate_and_filter
from .agents.structure_agent import structure_keywords
from .agents.strategy_agent import assemble_outputs, write_outputs_txt_csv
from .core.types import CampaignOutputs


class PipelineState(BaseModel):
    config_path: str
    outputs_dir: str
    max_serp_queries: int = 10
    extra_seeds: Optional[list[str]] = None
    llm_context: Optional[str] = None

    # intermediate products
    raw_keywords: list = Field(default_factory=list)
    filtered_keywords: list = Field(default_factory=list)
    structured_records: list = Field(default_factory=list)
    outputs: Optional[CampaignOutputs] = None


def node_load_config(state: PipelineState) -> PipelineState:
    load_and_validate_config(state.config_path)  # validation side-effect
    return state


def node_gather(state: PipelineState) -> PipelineState:
    cfg = load_and_validate_config(state.config_path)
    state.raw_keywords = gather_keywords(
        cfg, extra_seeds=state.extra_seeds, max_serp_queries=state.max_serp_queries
    )
    # Heuristic metrics enrichment when GKP API is not used
    state.raw_keywords = enrich_keywords_with_heuristic_metrics(state.raw_keywords)
    return state


def node_filter(state: PipelineState) -> PipelineState:
    cfg = load_and_validate_config(state.config_path)
    state.filtered_keywords = consolidate_and_filter(
        state.raw_keywords, min_volume=cfg.project_settings.min_search_volume_threshold, llm_context=state.llm_context
    )
    return state


def node_structure(state: PipelineState) -> PipelineState:
    # Build brand and competitor tokens and locations for clustering
    cfg = load_and_validate_config(state.config_path)
    from urllib.parse import urlparse

    def extract_tokens(url: str) -> list[str]:
        try:
            host = urlparse(url).hostname or ""
            host = host.lower()
            parts = [p for p in host.split(".") if p not in {"www", "com", "net", "org", "io", "ai", "co"}]
            return parts
        except Exception:
            return []

    brand_terms = extract_tokens(cfg.brand_url)
    competitor_terms = []
    for u in cfg.competitor_urls:
        competitor_terms.extend(extract_tokens(u))

    locations = cfg.service_locations

    state.structured_records = structure_keywords(
        state.filtered_keywords,
        llm_context=state.llm_context,
        brand_terms=brand_terms,
        competitor_terms=competitor_terms,
        locations=locations,
    )
    return state


def node_strategy(state: PipelineState) -> PipelineState:
    cfg = load_and_validate_config(state.config_path)
    state.outputs = assemble_outputs(cfg, state.structured_records)
    write_outputs_txt_csv(state.outputs_dir, state.outputs)
    return state


def build_graph() -> StateGraph:
    g = StateGraph(PipelineState)
    g.add_node("validate_config", node_load_config)
    g.add_node("gather", node_gather)
    g.add_node("filter", node_filter)
    g.add_node("structure", node_structure)
    g.add_node("strategy", node_strategy)

    g.set_entry_point("validate_config")
    g.add_edge("validate_config", "gather")
    g.add_edge("gather", "filter")
    g.add_edge("filter", "structure")
    g.add_edge("structure", "strategy")
    g.add_edge("strategy", END)
    return g


