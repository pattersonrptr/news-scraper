"""CollectFeedsUseCase — orchestrates RSS collection + dedup + persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.src.core.exceptions import DuplicateArticleError, SourceFetchError
from backend.src.core.logging import get_logger
from backend.src.domain.entities.article import Article
from backend.src.domain.repositories import ArticleRepository, SourceRepository
from backend.src.domain.services.deduplication import DeduplicationService
from backend.src.domain.value_objects import ArticleHash
from backend.src.infrastructure.collectors.rss.collector import RSSCollector, RawArticle

log = get_logger(__name__)


class CollectFeedsUseCase:
    """Fetch all active RSS sources and persist new (non-duplicate) articles.

    One instance per execution; dependencies are injected.
    """

    def __init__(
        self,
        source_repo: SourceRepository,
        article_repo: ArticleRepository,
        dedup_service: DeduplicationService,
        collector: RSSCollector | None = None,
    ) -> None:
        self._sources = source_repo
        self._articles = article_repo
        self._dedup = dedup_service
        self._collector = collector or RSSCollector()

    async def execute(self) -> dict[str, int]:
        """Run the collection for all active sources.

        Returns a summary dict: {source_name: articles_saved}.
        """
        sources = await self._sources.list_active()
        summary: dict[str, int] = {}

        for source in sources:
            saved = await self._collect_source(source)
            summary[source.name] = saved

        log.info("collect_feeds_done", summary=summary, total=sum(summary.values()))
        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _collect_source(self, source) -> int:  # type: ignore[no-untyped-def]
        """Collect one source. Returns the number of new articles saved."""
        feed_url = source.feed_url or source.url
        saved = 0

        try:
            raw_articles = await self._collector.collect(
                source_id=str(source.id),
                feed_url=feed_url,
                language=source.language,
            )
        except SourceFetchError as exc:
            log.error("source_fetch_failed", source=source.name, error=str(exc))
            await self._sources.increment_error_count(source.id, str(exc))
            return 0

        for raw in raw_articles:
            try:
                is_dup = await self._dedup.is_duplicate(raw.url, raw.title, raw.body)
                if is_dup:
                    continue
                article = self._raw_to_article(raw, source)
                await self._articles.save(article)
                saved += 1
            except DuplicateArticleError:
                continue
            except Exception as exc:  # noqa: BLE001
                log.warning("article_save_failed", url=raw.url, error=str(exc))

        await self._sources.update_last_fetched(source.id)
        log.info("source_collected", source=source.name, saved=saved)
        return saved

    @staticmethod
    def _raw_to_article(raw: RawArticle, source) -> Article:  # type: ignore[no-untyped-def]
        """Convert a RawArticle from the collector to a domain Article entity."""
        hashes = ArticleHash.from_article_data(url=raw.url, title=raw.title, body=raw.body)
        return Article(
            source_id=source.id,
            url=raw.url,
            url_hash=hashes.url_hash,
            content_hash=hashes.content_hash,
            title=raw.title,
            body=raw.body,
            author=raw.author,
            published_at=raw.published_at,
            collected_at=datetime.now(timezone.utc),
            language=raw.language or source.language,
            tags=raw.tags,
            image_url=raw.image_url,
            is_processed=False,
            is_read=False,
        )
