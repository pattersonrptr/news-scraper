"""Test configuration and shared fixtures."""

from __future__ import annotations

import pytest
import pytest_asyncio  # noqa: F401 — ensures asyncio mode is active


# ---------------------------------------------------------------------------
# Domain entity factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_article_data() -> dict:
    """Minimal raw article data dict for testing."""
    return {
        "url": "https://example.com/article/1",
        "title": "Python 3.13 Released",
        "body": "Python 3.13 brings many improvements to the language including...",
        "language": "en",
    }
