"""SMTP email service for the feedback form."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)


@dataclass
class FeedbackPayload:
    message: str
    name: str = ""
    email: str = ""
    page: str = ""


class SMTPEmailService:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        feedback_email: str,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._feedback_email = feedback_email

    async def send_feedback(self, payload: FeedbackPayload) -> None:
        """Send a feedback email asynchronously."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "New Feedback – Personal Web Agent"
        msg["From"] = self._from_email
        msg["To"] = self._feedback_email

        name_line = f"From: {payload.name} ({payload.email})" if payload.name else ""
        page_line = f"Page: {payload.page}" if payload.page else ""
        separator = "\n" if (name_line or page_line) else ""

        plain = (
            f"{name_line}\n{page_line}{separator}{payload.message}".strip()
        )
        html = f"<pre style='font-family:sans-serif'>{plain}</pre>"

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                start_tls=True,
            )
            log.info("Feedback email sent to %s", self._feedback_email)
        except Exception as exc:
            log.error("Failed to send feedback email: %s", exc)
            raise
