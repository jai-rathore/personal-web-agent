"""Google Workspace tools – owner-only, backed by the gws CLI.

The `gws` CLI (github.com/googleworkspace/cli) must be installed and
authenticated before these tools are invoked. Each tool wraps a subprocess
call and returns structured JSON back to the ADK agent.

Auth note: the gws CLI uses its own stored OAuth2 credentials (set up via
`gws auth setup`). The access_token from the user's session is passed via the
GWS_ACCESS_TOKEN env var so gws can act on behalf of the authenticated user.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil

log = logging.getLogger(__name__)

_GWS_AVAILABLE = shutil.which("gws") is not None


# ── Internal helper ──────────────────────────────────────────────────────────


async def _run_gws(args: list[str], access_token: str = "") -> dict:
    """Execute a gws CLI command and return parsed JSON output."""
    if not _GWS_AVAILABLE:
        return {
            "status": "error",
            "message": "gws CLI not installed. Run: npm install -g @googleworkspace/cli",
        }

    env = {**os.environ}
    if access_token:
        env["GWS_ACCESS_TOKEN"] = access_token

    try:
        proc = await asyncio.create_subprocess_exec(
            "gws",
            *args,
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode != 0:
            error_text = stderr.decode().strip()
            log.error("gws CLI error (rc=%d): %s", proc.returncode, error_text)
            return {"status": "error", "message": error_text or "gws command failed"}

        raw = stdout.decode().strip()
        if not raw:
            return {"status": "success", "data": None}

        return {"status": "success", "data": json.loads(raw)}

    except asyncio.TimeoutError:
        return {"status": "error", "message": "gws command timed out after 30s"}
    except json.JSONDecodeError as exc:
        log.error("Failed to parse gws output: %s", exc)
        return {"status": "error", "message": "Invalid JSON response from gws"}
    except Exception as exc:
        log.exception("Unexpected error running gws: %s", exc)
        return {"status": "error", "message": str(exc)}


# ── Calendar tools ───────────────────────────────────────────────────────────


async def list_calendar_events(
    date: str = "",
    max_results: int = 10,
    calendar_id: str = "primary",
    _access_token: str = "",
) -> dict:
    """List upcoming Google Calendar events.

    Args:
        date: ISO date string to filter events (e.g. '2026-03-20'). Leave empty for today onward.
        max_results: Maximum number of events to return (default 10).
        calendar_id: Calendar ID to query (default 'primary').
        _access_token: OAuth2 access token (injected by the agent runner, do not pass manually).

    Returns:
        A dict with a list of calendar events.
    """
    params: dict = {"calendarId": calendar_id, "maxResults": max_results}
    if date:
        params["timeMin"] = f"{date}T00:00:00Z"
        params["timeMax"] = f"{date}T23:59:59Z"

    return await _run_gws(
        ["calendar", "events", "list", "--params", json.dumps(params)],
        access_token=_access_token,
    )


async def create_calendar_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    attendee_email: str = "",
    calendar_id: str = "primary",
    _access_token: str = "",
) -> dict:
    """Create a new Google Calendar event.

    Args:
        summary: Event title.
        start: Start datetime in ISO format (e.g. '2026-03-20T10:00:00-07:00').
        end: End datetime in ISO format.
        description: Optional event description.
        attendee_email: Optional attendee email address to invite.
        calendar_id: Calendar ID (default 'primary').
        _access_token: OAuth2 access token (injected).

    Returns:
        A dict with the created event details.
    """
    body: dict = {
        "summary": summary,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    if description:
        body["description"] = description
    if attendee_email:
        body["attendees"] = [{"email": attendee_email}]

    return await _run_gws(
        [
            "calendar",
            "events",
            "insert",
            "--params",
            json.dumps({"calendarId": calendar_id}),
            "--body",
            json.dumps(body),
        ],
        access_token=_access_token,
    )


async def update_calendar_event(
    event_id: str,
    summary: str = "",
    start: str = "",
    end: str = "",
    description: str = "",
    calendar_id: str = "primary",
    _access_token: str = "",
) -> dict:
    """Update an existing Google Calendar event.

    Args:
        event_id: The event ID to update.
        summary: New event title (optional).
        start: New start datetime in ISO format (optional).
        end: New end datetime in ISO format (optional).
        description: New description (optional).
        calendar_id: Calendar ID (default 'primary').
        _access_token: OAuth2 access token (injected).

    Returns:
        A dict with the updated event details.
    """
    body: dict = {}
    if summary:
        body["summary"] = summary
    if start:
        body["start"] = {"dateTime": start}
    if end:
        body["end"] = {"dateTime": end}
    if description:
        body["description"] = description

    return await _run_gws(
        [
            "calendar",
            "events",
            "patch",
            "--params",
            json.dumps({"calendarId": calendar_id, "eventId": event_id}),
            "--body",
            json.dumps(body),
        ],
        access_token=_access_token,
    )


async def delete_calendar_event(
    event_id: str,
    calendar_id: str = "primary",
    _access_token: str = "",
) -> dict:
    """Delete a Google Calendar event.

    Args:
        event_id: The event ID to delete.
        calendar_id: Calendar ID (default 'primary').
        _access_token: OAuth2 access token (injected).

    Returns:
        A dict confirming deletion.
    """
    result = await _run_gws(
        [
            "calendar",
            "events",
            "delete",
            "--params",
            json.dumps({"calendarId": calendar_id, "eventId": event_id}),
        ],
        access_token=_access_token,
    )
    if result.get("status") == "success":
        result["message"] = f"Event {event_id} deleted successfully."
    return result


# ── Gmail tools ──────────────────────────────────────────────────────────────


async def list_emails(
    query: str = "",
    max_results: int = 10,
    label_ids: str = "INBOX",
    _access_token: str = "",
) -> dict:
    """List emails from Gmail, optionally filtered by query.

    Args:
        query: Gmail search query (e.g. 'from:boss@example.com is:unread').
        max_results: Maximum number of messages to return (default 10).
        label_ids: Comma-separated label IDs to filter by (default 'INBOX').
        _access_token: OAuth2 access token (injected).

    Returns:
        A dict with a list of email message summaries.
    """
    params: dict = {"maxResults": max_results}
    if query:
        params["q"] = query
    if label_ids:
        params["labelIds"] = label_ids.split(",")

    return await _run_gws(
        ["gmail", "users", "messages", "list", "--params", json.dumps(params)],
        access_token=_access_token,
    )


async def get_email(
    message_id: str,
    format: str = "full",
    _access_token: str = "",
) -> dict:
    """Get the full content of a specific email.

    Args:
        message_id: The Gmail message ID.
        format: Response format – 'full', 'metadata', or 'minimal' (default 'full').
        _access_token: OAuth2 access token (injected).

    Returns:
        A dict with the email content.
    """
    return await _run_gws(
        [
            "gmail",
            "users",
            "messages",
            "get",
            "--params",
            json.dumps({"userId": "me", "id": message_id, "format": format}),
        ],
        access_token=_access_token,
    )


async def search_emails(
    query: str,
    max_results: int = 10,
    _access_token: str = "",
) -> dict:
    """Search Gmail using a search query.

    Args:
        query: Gmail search query (e.g. 'subject:meeting from:recruiter').
        max_results: Maximum number of results to return (default 10).
        _access_token: OAuth2 access token (injected).

    Returns:
        A dict with matching email message summaries.
    """
    return await _run_gws(
        [
            "gmail",
            "users",
            "messages",
            "list",
            "--params",
            json.dumps({"q": query, "maxResults": max_results, "userId": "me"}),
        ],
        access_token=_access_token,
    )


async def send_email(
    to: str,
    subject: str,
    body: str,
    _access_token: str = "",
) -> dict:
    """Send an email via Gmail.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.
        _access_token: OAuth2 access token (injected).

    Returns:
        A dict confirming the sent message.
    """
    import base64
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    return await _run_gws(
        [
            "gmail",
            "users",
            "messages",
            "send",
            "--params",
            json.dumps({"userId": "me"}),
            "--body",
            json.dumps({"raw": raw}),
        ],
        access_token=_access_token,
    )
