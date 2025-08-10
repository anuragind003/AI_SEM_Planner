from __future__ import annotations

import os
from typing import List, Dict, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI


def _get_model(model_name: str = "gemini-1.5-flash") -> ChatGoogleGenerativeAI | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=0)


def filter_keywords_with_llm(candidates: List[str], *, context: Optional[str] = None) -> List[str]:
    model = _get_model()
    if model is None:
        # Fallback: return as-is (heuristics are applied elsewhere)
        return candidates

    prompt = PromptTemplate.from_template(
        """
You are a marketing analyst. Use the following business context to decide relevance.
Context:
{context}

From the list below, return ONLY the keywords relevant to the business's offerings and audience.
Output: one keyword per line, no bullets, no numbering.

{keywords}
        """
    )

    chain = prompt | model | StrOutputParser()
    text = chain.invoke({"keywords": "\n".join(candidates), "context": context or ""})
    kept = [line.strip() for line in text.splitlines() if line.strip()]
    return kept


def cluster_keywords_with_llm(candidates: List[str], *, context: Optional[str] = None) -> Dict[str, List[str]]:
    model = _get_model()
    if model is None:
        return {}

    prompt = PromptTemplate.from_template(
        """
Cluster the following keywords into concise, semantically tight ad groups.
Use this business context to inform grouping (brand, competitors, locations, and offerings):
{context}

Prefer groups like Brand Terms, Competitor: X, Category: Y, Use Case: Z, Location-based Queries, Long-Tail Informational Queries.
Return JSON ONLY as a mapping from group name to list of keywords.

{keywords}
        """
    )

    chain = prompt | model | StrOutputParser()
    text = chain.invoke({"keywords": "\n".join(candidates), "context": context or ""})
    import json

    start = text.find("{")
    end = text.rfind("}")
    block = text[start : end + 1] if start != -1 and end != -1 else "{}"
    try:
        data = json.loads(block)
        out: Dict[str, List[str]] = {}
        for k, v in data.items():
            if isinstance(v, list):
                out[str(k)] = [str(x) for x in v]
        return out
    except Exception:
        return {}


