"""AI provider port — abstract interface for AI analysis services."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class AIResult:
    """Structured result returned by any AI provider."""

    summary: str
    sentiment: int  # -1 (negative) | 0 (neutral) | 1 (positive)
    sentiment_score: float  # confidence 0.0–1.0
    category: str | None = None
    entities: dict[str, list[str]] = field(default_factory=dict)
    # e.g. {"people": ["Elon Musk"], "orgs": ["Tesla"], "places": ["Berlin"]}


@runtime_checkable
class AIProviderPort(Protocol):
    """Protocol that every AI backend adapter must satisfy."""

    async def analyze(self, title: str, body: str) -> AIResult:
        """Analyse a single article and return structured AI output."""
        ...

    async def is_available(self) -> bool:
        """Return True if the provider is reachable and ready."""
        ...
