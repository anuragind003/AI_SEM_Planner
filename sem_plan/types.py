from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Literal

# Backward-compat shim: re-export from core.types for direct imports
from .core.types import (
    AdBudgets,
    ProjectSettings,
    Config,
    RawKeyword,
    KeywordRecord,
    CampaignOutputs,
)


