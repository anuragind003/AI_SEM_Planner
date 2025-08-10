from __future__ import annotations

from typing import Iterable, Optional

from .core.types import CampaignOutputs
from .graph import build_graph, PipelineState


def run_pipeline(
    *,
    config_path: str,
    outputs_dir: str,
    max_serp_queries: int = 10,
    extra_seeds: Optional[Iterable[str]] = None,
    llm_context: Optional[str] = None,
) -> CampaignOutputs:
    graph = build_graph().compile()
    state = PipelineState(
        config_path=config_path,
        outputs_dir=outputs_dir,
        max_serp_queries=max_serp_queries,
        extra_seeds=list(extra_seeds) if extra_seeds else None,
        llm_context=llm_context,
    )
    final_state = graph.invoke(state)
    # LangGraph may return a dict-like state; support both
    if isinstance(final_state, dict):
        outputs = final_state.get("outputs")
    else:
        outputs = getattr(final_state, "outputs", None)

    # Ensure a CampaignOutputs-like object is returned
    if outputs is None:
        # Provide an empty shell to keep downstream UI stable
        from .core.types import KeywordRecord, CampaignOutputs as CO

        outputs = CO(search_keywords=[], pmax_themes=[], shopping_target_cpc=0.0)
    return outputs  


