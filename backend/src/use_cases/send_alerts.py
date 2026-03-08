"""Use case: scan recent articles for keyword matches and send alert emails."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from backend.src.domain.entities.alert import Alert, NotificationChannel
from backend.src.domain.repositories import AlertRepository, ArticleRepository, UserProfileRepository
from backend.src.domain.services.alert_service import match_articles
from backend.src.infrastructure.notifications.email.smtp_adapter import SMTPEmailAdapter

logger = logging.getLogger(__name__)

_RATE_LIMIT_HOURS = 1  # max 1 alert per keyword per hour


class SendAlertsUseCase:
    """Scan recent articles for keyword matches and send rate-limited email alerts.

    Rate-limiting strategy: before firing, query the alert log for the
    same keyword within the last ``_RATE_LIMIT_HOURS`` hour(s). If an
    alert was already sent, skip it.
    """

    def __init__(
        self,
        article_repo: ArticleRepository,
        alert_repo: AlertRepository,
        profile_repo: UserProfileRepository,
        email_adapter: SMTPEmailAdapter,
        lookback_hours: int = 1,
    ) -> None:
        self._articles = article_repo
        self._alerts = alert_repo
        self._profiles = profile_repo
        self._email = email_adapter
        self._lookback_hours = lookback_hours

    async def execute(self) -> dict[str, int]:
        """Run one alert-check cycle.

        Returns
        -------
        dict with keys:
          - matched: total (keyword, article) pairs found
          - sent: alerts actually sent (after rate-limit filtering)
          - skipped: pairs skipped due to rate-limit
        """
        profile = await self._profiles.get_default()
        if not profile or not profile.alert_keywords:
            logger.debug("No alert keywords configured — skipping")
            return {"matched": 0, "sent": 0, "skipped": 0}

        recipient = profile.notification_email or profile.email
        if not recipient:
            logger.warning("No recipient email on profile — skipping alerts")
            return {"matched": 0, "sent": 0, "skipped": 0}

        # Fetch articles from the last lookback window
        recent_articles = await self._articles.list_recent(
            hours=self._lookback_hours, limit=200
        )
        matches = match_articles(profile.alert_keywords, recent_articles)

        matched = len(matches)
        sent = 0
        skipped = 0
        now = datetime.now(timezone.utc)
        rate_limit_cutoff = now - timedelta(hours=_RATE_LIMIT_HOURS)

        # Group by keyword so we send one email per keyword (with all articles)
        keyword_articles: dict[str, list] = {}
        for keyword, article in matches:
            keyword_articles.setdefault(keyword, []).append(article)

        for keyword, articles in keyword_articles.items():
            # Rate-limit check
            recent_alerts = await self._alerts.list_recent_by_keyword(
                keyword=keyword,
                user_id=profile.id,
                since=rate_limit_cutoff,
            )
            if recent_alerts:
                logger.debug(
                    "Rate-limit: skipping alert for keyword '%s' (already sent %d time(s) in last %dh)",
                    keyword,
                    len(recent_alerts),
                    _RATE_LIMIT_HOURS,
                )
                skipped += len(articles)
                continue

            # Send one email for all matching articles under this keyword
            try:
                await self._email.send_alert_email(
                    to=recipient,
                    keyword=keyword,
                    articles=articles,
                    generated_at=now.strftime("%Y-%m-%d %H:%M UTC"),
                )
            except Exception as exc:
                logger.error("Failed to send alert email for keyword '%s': %s", keyword, exc)
                skipped += len(articles)
                continue

            # Log the fired alert (first matching article as reference)
            alert = Alert(
                user_id=profile.id,
                article_id=articles[0].id,
                trigger_keyword=keyword,
                channel=NotificationChannel.EMAIL,
                sent_at=now,
            )
            await self._alerts.save(alert)
            sent += len(articles)
            logger.info("Alert sent for keyword '%s' — %d article(s)", keyword, len(articles))

        return {"matched": matched, "sent": sent, "skipped": skipped}
