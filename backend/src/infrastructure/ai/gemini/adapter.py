"""Gemini AI adapter — implements AIProviderPort using Google Generative AI."""

from __future__ import annotations

import json
import logging

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.src.core.config.settings import get_settings
from backend.src.core.exceptions import AIProviderError, AIRateLimitError
from backend.src.domain.ports.ai_provider import AIProviderPort, AIResult

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


class GeminiAdapter:
    """Concrete AI adapter that calls Google Gemini 1.5 Flash."""

    def __init__(self) -> None:
        self._settings = get_settings()
        genai.configure(api_key=self._settings.gemini_api_key)
        self._model = genai.GenerativeModel(self._settings.gemini_model)

    @retry(
        retry=retry_if_exception_type(AIProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def analyze(self, title: str, body: str) -> AIResult:
        """Call Gemini with a structured JSON prompt and parse the result."""
        prompt = _ANALYSIS_PROMPT_TEMPLATE.format(
            title=title,
            body=body[:4000],  # stay well within token limits
        )
        try:
            response = await self._model.generate_content_async(prompt)
            raw = response.text.strip()
        except ResourceExhausted as exc:
            logger.warning("Gemini rate limit exceeded: %s", exc)
            raise AIRateLimitError("gemini") from exc
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise AIProviderError("gemini", cause=exc) from exc

        return _parse_ai_result(raw)

    async def is_available(self) -> bool:
        """Return True if Gemini API key is configured and the model responds."""
        if not self._settings.gemini_api_key:
            return False
        try:
            response = await self._model.generate_content_async("ping")
            return bool(response.text)
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Shared JSON parser (used by both adapters)
# ---------------------------------------------------------------------------

def _parse_ai_result(raw: str) -> AIResult:
    """Parse raw JSON text from the LLM into an AIResult dataclass."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Attempt to extract JSON block if the model wrapped it in prose
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(raw[start:end])
            except json.JSONDecodeError:
                raise AIProviderError("gemini", cause=exc) from exc
        else:
            raise AIProviderError("gemini", cause=exc) from exc

    entities: dict[str, list[str]] = {
        "people": data.get("entities", {}).get("people", []),
        "orgs": data.get("entities", {}).get("orgs", []),
        "places": data.get("entities", {}).get("places", []),
    }

    return AIResult(
        summary=str(data.get("summary", "")),
        sentiment=int(data.get("sentiment", 0)),
        sentiment_score=float(data.get("sentiment_score", 0.0)),
        category=data.get("category") or None,
        entities=entities,
    )


# Expose the parser so the Ollama adapter can reuse it
__all__ = ["GeminiAdapter", "_parse_ai_result"]


# Type assertion — verify adapter satisfies the Protocol at import time
def _check_protocol() -> None:
    assert isinstance(GeminiAdapter(), AIProviderPort)  # noqa: S101


# Make the Protocol check opt-in (don't run it at module load — no API key yet)
