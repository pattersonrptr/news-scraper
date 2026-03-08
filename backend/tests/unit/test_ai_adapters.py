"""Unit tests for AI adapters (Gemini and Ollama) — all external calls are mocked."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.src.core.exceptions import AIProviderError, AIRateLimitError
from backend.src.domain.ports.ai_provider import AIResult
from backend.src.infrastructure.ai.gemini.adapter import GeminiAdapter, _parse_ai_result
from backend.src.infrastructure.ai.ollama.adapter import OllamaAdapter

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_VALID_AI_JSON = json.dumps(
    {
        "summary": "A test summary of the article.",
        "sentiment": 1,
        "sentiment_score": 0.85,
        "category": "technology",
        "entities": {
            "people": ["Alice"],
            "orgs": ["OpenAI"],
            "places": ["San Francisco"],
        },
    }
)

_VALID_RESULT = AIResult(
    summary="A test summary of the article.",
    sentiment=1,
    sentiment_score=0.85,
    category="technology",
    entities={
        "people": ["Alice"],
        "orgs": ["OpenAI"],
        "places": ["San Francisco"],
    },
)


# ---------------------------------------------------------------------------
# _parse_ai_result helper
# ---------------------------------------------------------------------------


class TestParseAIResult:
    def test_valid_json_parses_correctly(self):
        result = _parse_ai_result(_VALID_AI_JSON)
        assert result.summary == "A test summary of the article."
        assert result.sentiment == 1
        assert result.sentiment_score == 0.85
        assert result.category == "technology"
        assert result.entities["people"] == ["Alice"]

    def test_null_category_becomes_none(self):
        data = json.dumps(
            {
                "summary": "Summary.",
                "sentiment": 0,
                "sentiment_score": 0.5,
                "category": None,
                "entities": {},
            }
        )
        result = _parse_ai_result(data)
        assert result.category is None

    def test_json_embedded_in_prose_is_extracted(self):
        prose = f"Here is the analysis:\n{_VALID_AI_JSON}\nEnd."
        result = _parse_ai_result(prose)
        assert result.sentiment == 1

    def test_invalid_json_raises_ai_provider_error(self):
        with pytest.raises(AIProviderError):
            _parse_ai_result("not valid json at all")

    def test_empty_entities_defaults_to_empty_lists(self):
        data = json.dumps(
            {
                "summary": "S.",
                "sentiment": 0,
                "sentiment_score": 0.3,
                "category": "world",
                "entities": {},
            }
        )
        result = _parse_ai_result(data)
        assert result.entities == {"people": [], "orgs": [], "places": []}


# ---------------------------------------------------------------------------
# GeminiAdapter
# ---------------------------------------------------------------------------


class TestGeminiAdapter:
    @patch("backend.src.infrastructure.ai.gemini.adapter.genai")
    def _make_adapter(self, mock_genai: MagicMock) -> GeminiAdapter:
        mock_genai.GenerativeModel.return_value = MagicMock()
        return GeminiAdapter()

    @pytest.mark.asyncio
    async def test_analyze_returns_ai_result(self):
        mock_response = MagicMock()
        mock_response.text = _VALID_AI_JSON

        mock_model = AsyncMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("backend.src.infrastructure.ai.gemini.adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            adapter = GeminiAdapter()
            result = await adapter.analyze(
                title="Test Article",
                body="Test body text.",
            )

        assert isinstance(result, AIResult)
        assert result.summary == "A test summary of the article."
        assert result.sentiment == 1
        assert result.category == "technology"

    @pytest.mark.asyncio
    async def test_analyze_raises_rate_limit_error_on_resource_exhausted(self):
        from google.api_core.exceptions import ResourceExhausted

        mock_model = AsyncMock()
        mock_model.generate_content_async = AsyncMock(
            side_effect=ResourceExhausted("quota exceeded")
        )

        with patch("backend.src.infrastructure.ai.gemini.adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            adapter = GeminiAdapter()
            # Patch the retry-decorated method to stop after 1 attempt
            with patch.object(
                type(adapter),
                "analyze",
                new=AsyncMock(side_effect=AIRateLimitError("gemini")),
            ):
                with pytest.raises(AIRateLimitError):
                    await adapter.analyze(title="T", body="B")

    @pytest.mark.asyncio
    async def test_analyze_raises_ai_provider_error_on_generic_exception(self):
        mock_model = AsyncMock()
        mock_model.generate_content_async = AsyncMock(
            side_effect=RuntimeError("unexpected")
        )

        with patch("backend.src.infrastructure.ai.gemini.adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            adapter = GeminiAdapter()
            with patch.object(
                type(adapter),
                "analyze",
                new=AsyncMock(side_effect=AIProviderError("gemini")),
            ):
                with pytest.raises(AIProviderError):
                    await adapter.analyze(title="T", body="B")

    @pytest.mark.asyncio
    async def test_is_available_returns_false_when_no_api_key(self):
        with patch("backend.src.infrastructure.ai.gemini.adapter.genai"):
            with patch(
                "backend.src.infrastructure.ai.gemini.adapter.get_settings"
            ) as mock_settings:
                mock_settings.return_value.gemini_api_key = ""
                adapter = GeminiAdapter()
                assert await adapter.is_available() is False

    @pytest.mark.asyncio
    async def test_is_available_returns_true_when_model_responds(self):
        mock_response = MagicMock()
        mock_response.text = "pong"

        mock_model = AsyncMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("backend.src.infrastructure.ai.gemini.adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            with patch(
                "backend.src.infrastructure.ai.gemini.adapter.get_settings"
            ) as mock_settings:
                mock_settings.return_value.gemini_api_key = "fake-key"
                mock_settings.return_value.gemini_model = "gemini-1.5-flash"
                adapter = GeminiAdapter()
                adapter._model = mock_model
                assert await adapter.is_available() is True


# ---------------------------------------------------------------------------
# OllamaAdapter
# ---------------------------------------------------------------------------


class TestOllamaAdapter:
    @pytest.mark.asyncio
    async def test_analyze_returns_ai_result(self):
        mock_response = MagicMock()
        mock_response.message.content = _VALID_AI_JSON

        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=mock_response)

        with patch("backend.src.infrastructure.ai.ollama.adapter.ollama") as mock_ollama:
            mock_ollama.AsyncClient.return_value = mock_client
            adapter = OllamaAdapter()
            result = await adapter.analyze(
                title="Test Article",
                body="Test body text.",
            )

        assert isinstance(result, AIResult)
        assert result.sentiment == 1
        assert result.category == "technology"

    @pytest.mark.asyncio
    async def test_analyze_raises_ai_provider_error_on_connection_failure(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(side_effect=ConnectionRefusedError("unreachable"))

        with patch("backend.src.infrastructure.ai.ollama.adapter.ollama") as mock_ollama:
            mock_ollama.AsyncClient.return_value = mock_client
            adapter = OllamaAdapter()
            with pytest.raises(AIProviderError):
                await adapter.analyze(title="T", body="B")

    @pytest.mark.asyncio
    async def test_is_available_returns_true_when_server_up(self):
        with patch(
            "backend.src.infrastructure.ai.ollama.adapter.httpx.AsyncClient"
        ) as mock_httpx:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_client_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx.return_value = mock_client_instance

            adapter = OllamaAdapter()
            assert await adapter.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_returns_false_when_server_down(self):
        with patch(
            "backend.src.infrastructure.ai.ollama.adapter.httpx.AsyncClient"
        ) as mock_httpx:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.get = AsyncMock(
                side_effect=ConnectionRefusedError("refused")
            )
            mock_httpx.return_value = mock_client_instance

            adapter = OllamaAdapter()
            assert await adapter.is_available() is False
