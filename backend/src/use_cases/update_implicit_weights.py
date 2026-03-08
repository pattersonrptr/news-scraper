"""Use case: update a user's implicit interest weights from their read history."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from backend.src.domain.repositories import ArticleRepository, UserProfileRepository

logger = logging.getLogger(__name__)

_WEIGHT_INCREMENT = 0.05   # bump each read category by this amount
_WEIGHT_MAX = 1.0
_WEIGHT_DECAY = 0.995      # daily multiplicative decay for all weights


class UpdateImplicitWeightsUseCase:
    """Learn implicit interest weights from the articles a user has read.

    Algorithm (per daily run):
    1. Fetch all articles marked ``is_read=True`` in the last 24h.
    2. Count category frequencies among those articles.
    3. For each category, increment its weight by ``_WEIGHT_INCREMENT``
       (capped at ``_WEIGHT_MAX``).
    4. Apply a small multiplicative decay to all existing weights so
       old interests fade gradually.
    5. Persist the updated weights via ``UserProfileRepository``.
    """

    def __init__(
        self,
        article_repo: ArticleRepository,
        profile_repo: UserProfileRepository,
        hours: int = 24,
    ) -> None:
        self._articles = article_repo
        self._profiles = profile_repo
        self._hours = hours

    async def execute(self) -> dict[str, int]:
        """Run one weight-update cycle.

        Returns
        -------
        dict with keys:
          - articles_read: number of articles considered
          - categories_updated: number of distinct categories boosted
        """
        profile = await self._profiles.get_default()
        if profile is None:
            logger.warning("update_implicit_weights: no profile found")
            return {"articles_read": 0, "categories_updated": 0}

        # Fetch articles read in the look-back window
        recent = await self._articles.list_recent(hours=self._hours, limit=500)
        read_articles = [a for a in recent if a.is_read and a.category]

        if not read_articles:
            logger.debug("update_implicit_weights: no recently-read articles")
            return {"articles_read": 0, "categories_updated": 0}

        category_counts: Counter[str] = Counter(
            a.category.lower() for a in read_articles if a.category
        )

        # Apply decay then increment
        weights: dict[str, float] = {
            k: v * _WEIGHT_DECAY for k, v in profile.implicit_weights.items()
        }
        for category, _count in category_counts.items():
            current = weights.get(category, 0.0)
            weights[category] = min(current + _WEIGHT_INCREMENT, _WEIGHT_MAX)

        await self._profiles.update_implicit_weights(
            user_id=profile.id, weights=weights
        )
        logger.info(
            "implicit_weights_updated: articles_read=%d categories=%d",
            len(read_articles),
            len(category_counts),
        )
        return {
            "articles_read": len(read_articles),
            "categories_updated": len(category_counts),
        }
