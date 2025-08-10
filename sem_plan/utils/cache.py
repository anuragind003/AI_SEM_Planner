from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


def _default_cache_path() -> str:
    base = os.path.join(os.getcwd(), ".cache")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "metrics.json")


def load_cache(path: Optional[str] = None) -> Dict[str, Any]:
    cache_path = path or _default_cache_path()
    if not os.path.exists(cache_path):
        return {}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(data: Dict[str, Any], path: Optional[str] = None) -> None:
    cache_path = path or _default_cache_path()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


