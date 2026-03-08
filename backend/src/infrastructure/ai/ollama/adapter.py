"""Ollama AI adapter — implements AIProviderPort using a local Ollama server."""

from __future__ import annotations

import json
import logging

import httpx
import ollama

from backend.src.core.config.settings import get_settings
from backend.src.core.exceptions import AIProviderError
from backend.src.domain.ports.ai_provider import AIProviderPort, AIResult
from backend.src.infrastructure.ai.gemini.adapter import _parse_ai_result

logger = logging.getLogger(__name__)

_ANALYSIS_PROMPT_TEMPLATE = """\
Analyze the following news article and return a JSON object with exactly these keys:

- "summary": a concise 2-3 sentence summary in English
- "sentiment": integer — -1 (negative), 0 (neutral), or 1 (positive)
- "sentiment_score": float between 0.0 and 1.0 indicating confidence
- "category": one of [politics, technology, business, sports, health, science, entertainment, world, other] or null
- "entities": object with keys "people", "orgs", "places" — each is a list of strings (empty list if none)

Return ONLY valid JSON, no markdown, no code fences.

Title: {title}

Body:
{body}
"""


class OllamaAdapter:
    """Concrete AI adapter that calls a locally-running Ollama server."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = ollama.AsyncClient(host=self._settings.ollama_base_url)

    async def analyze(self, title: str, body: str) -> AIResult:
        """Call Ollama chat endpoint and parse the structured JSON response."""
        prompt = _ANALYSIS_PROMPT_TEMPLATE.format(
            title=title,
            body=body[:4000],
        )
        try:
            response = await self._client.chat(
                model=self._settings.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
            raw: str = response.message.content.strip()  # type: ignore[union-attr]
        except Exception as exc:
            logger.error("Ollama API error: %s", exc)
            raise AIProviderError("ollama", cause=exc) from exc

        try:
            return _parse_ai_result(raw)
        except AIProviderError:
            # Re-raise with correct provider label
            raise AIProviderError("ollama") from None

    async def is_available(self) -> bool:
        """Return True if the Ollama server responds on /api/tags."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._settings.ollama_base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


__all__ = ["OllamaAdapter"]
