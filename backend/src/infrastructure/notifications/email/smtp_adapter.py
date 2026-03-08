"""SMTP email adapter — sends HTML email using aiosmtplib + Jinja2."""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.src.core.config.settings import get_settings

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


class SMTPEmailAdapter:
    """Send HTML emails via SMTP using aiosmtplib."""

    def __init__(self) -> None:
        self._settings = get_settings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def send_alert_email(
        self,
        to: str,
        keyword: str,
        articles: list,  # list[Article] — avoid circular import
        generated_at: str,
    ) -> None:
        """Render the alert template and send it."""
        html = _jinja_env.get_template("alerts_email.html").render(
            keyword=keyword,
            articles=articles,
            generated_at=generated_at,
        )
        subject = f"News Alert: {keyword}"
        await self._send(to=to, subject=subject, html=html)

    async def send_digest_email(
        self,
        to: str,
        context: dict,
    ) -> None:
        """Render the digest template and send it."""
        html = _jinja_env.get_template("digest_email.html").render(**context)
        subject = f"Your Daily Digest — {context.get('date_label', '')}"
        await self._send(to=to, subject=subject, html=html)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _send(self, to: str, subject: str, html: str) -> None:
        s = self._settings

        if not s.smtp_host or not s.alert_email:
            logger.warning(
                "SMTP not configured — skipping email to %s (subject: %s)", to, subject
            )
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = s.smtp_user or s.alert_email
        message["To"] = to
        message.attach(MIMEText(html, "html"))

        try:
            await aiosmtplib.send(
                message,
                hostname=s.smtp_host,
                port=s.smtp_port,
                username=s.smtp_user or None,
                password=s.smtp_password or None,
                use_tls=s.smtp_use_tls,
            )
            logger.info("Email sent to %s — %s", to, subject)
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to, exc)
            raise
