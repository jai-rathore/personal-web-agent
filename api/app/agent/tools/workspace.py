"""Google Workspace tools – owner-only, using direct Google API calls.

Calendar tools use the CalendarService. Gmail tools use the Gmail API
via google-api-python-client. All tools require the owner's OAuth2
access token, passed via closure from the agent factory.
"""
from __future__ import annotations

import base64
import logging
from email.mime.text import MIMEText
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.services.calendar_service import CalendarService

log = logging.getLogger(__name__)


# ── Calendar tools ───────────────────────────────────────────────────────────


def make_owner_calendar_tools(cal: CalendarService) -> list:
    """Return calendar CRUD tools for the owner, closed over a CalendarService."""

    def list_calendar_events(
        date: str = "",
        max_results: int = 10,
        calendar_id: str = "primary",
    ) -> dict:
        """List upcoming Google Calendar events.

        Args:
            date: ISO date string to filter events (e.g. '2026-03-20'). Leave empty for today onward.
            max_results: Maximum number of events to return (default 10).
            calendar_id: Calendar ID to query (default 'primary').
        """
        time_min = f"{date}T00:00:00Z" if date else None
        time_max = f"{date}T23:59:59Z" if date else None
        try:
            events = cal.list_events(
                time_min=time_min, time_max=time_max,
                max_results=max_results, calendar_id=calendar_id,
            )
            return {"status": "success", "events": events, "count": len(events)}
        except Exception as exc:
            log.exception("list_calendar_events failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    def create_calendar_event(
        summary: str,
        start: str,
        end: str,
        description: str = "",
        attendee_email: str = "",
        calendar_id: str = "primary",
    ) -> dict:
        """Create a new Google Calendar event.

        Args:
            summary: Event title.
            start: Start datetime in ISO format (e.g. '2026-03-20T10:00:00-07:00').
            end: End datetime in ISO format.
            description: Optional event description.
            attendee_email: Optional attendee email address to invite.
            calendar_id: Calendar ID (default 'primary').
        """
        try:
            event = cal.create_event(
                summary=summary, start=start, end=end,
                description=description, attendee_email=attendee_email,
                calendar_id=calendar_id,
            )
            return {"status": "success", "event": event}
        except Exception as exc:
            log.exception("create_calendar_event failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    def update_calendar_event(
        event_id: str,
        summary: str = "",
        start: str = "",
        end: str = "",
        description: str = "",
        calendar_id: str = "primary",
    ) -> dict:
        """Update an existing Google Calendar event.

        Args:
            event_id: The event ID to update.
            summary: New event title (optional).
            start: New start datetime in ISO format (optional).
            end: New end datetime in ISO format (optional).
            description: New description (optional).
            calendar_id: Calendar ID (default 'primary').
        """
        try:
            event = cal.update_event(
                event_id=event_id, summary=summary, start=start,
                end=end, description=description, calendar_id=calendar_id,
            )
            return {"status": "success", "event": event}
        except Exception as exc:
            log.exception("update_calendar_event failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    def delete_calendar_event(
        event_id: str,
        calendar_id: str = "primary",
    ) -> dict:
        """Delete a Google Calendar event.

        Args:
            event_id: The event ID to delete.
            calendar_id: Calendar ID (default 'primary').
        """
        try:
            cal.delete_event(event_id=event_id, calendar_id=calendar_id)
            return {"status": "success", "message": f"Event {event_id} deleted."}
        except Exception as exc:
            log.exception("delete_calendar_event failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    return [
        list_calendar_events,
        create_calendar_event,
        update_calendar_event,
        delete_calendar_event,
    ]


# ── Gmail tools ──────────────────────────────────────────────────────────────


def make_gmail_tools(access_token: str) -> list:
    """Return Gmail tools closed over an access token."""
    creds = Credentials(token=access_token)
    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)

    def list_emails(
        query: str = "",
        max_results: int = 10,
        label_ids: str = "INBOX",
    ) -> dict:
        """List emails from Gmail, optionally filtered by query.

        Args:
            query: Gmail search query (e.g. 'from:boss@example.com is:unread').
            max_results: Maximum number of messages to return (default 10).
            label_ids: Comma-separated label IDs to filter by (default 'INBOX').
        """
        try:
            results = gmail.users().messages().list(
                userId="me", q=query, maxResults=max_results,
                labelIds=label_ids.split(",") if label_ids else None,
            ).execute()
            messages = results.get("messages", [])

            # Fetch headers for each message
            summaries = []
            for msg in messages[:max_results]:
                detail = gmail.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()
                headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
                summaries.append({
                    "id": msg["id"],
                    "subject": headers.get("Subject", ""),
                    "from": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "snippet": detail.get("snippet", ""),
                })
            return {"status": "success", "messages": summaries, "count": len(summaries)}
        except Exception as exc:
            log.exception("list_emails failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    def get_email(
        message_id: str,
        format: str = "full",
    ) -> dict:
        """Get the full content of a specific email.

        Args:
            message_id: The Gmail message ID.
            format: Response format – 'full', 'metadata', or 'minimal' (default 'full').
        """
        try:
            msg = gmail.users().messages().get(
                userId="me", id=message_id, format=format,
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

            # Extract body text
            body = ""
            payload = msg.get("payload", {})
            if payload.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
            elif payload.get("parts"):
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                        break

            return {
                "status": "success",
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "body": body[:5000],  # Truncate very long emails
            }
        except Exception as exc:
            log.exception("get_email failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    def search_emails(
        query: str,
        max_results: int = 10,
    ) -> dict:
        """Search Gmail using a search query.

        Args:
            query: Gmail search query (e.g. 'subject:meeting from:recruiter').
            max_results: Maximum number of results to return (default 10).
        """
        return list_emails(query=query, max_results=max_results, label_ids="")

    def send_email(
        to: str,
        subject: str,
        body: str,
    ) -> dict:
        """Send an email via Gmail.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Plain-text email body.
        """
        try:
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            result = gmail.users().messages().send(
                userId="me", body={"raw": raw},
            ).execute()
            return {"status": "success", "message_id": result["id"]}
        except Exception as exc:
            log.exception("send_email failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    return [list_emails, get_email, search_emails, send_email]
