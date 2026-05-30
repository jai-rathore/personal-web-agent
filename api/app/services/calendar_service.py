"""Google Calendar API service — replaces the gws CLI dependency."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

log = logging.getLogger(__name__)

TOKEN_URI = "https://oauth2.googleapis.com/token"


class CalendarService:
    """Thin wrapper around the Google Calendar v3 API."""

    def __init__(self, credentials: Credentials) -> None:
        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    @classmethod
    def from_refresh_token(
        cls,
        refresh_token: str,
        client_id: str,
        client_secret: str,
    ) -> "CalendarService":
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri=TOKEN_URI,
        )
        return cls(creds)

    @classmethod
    def from_access_token(cls, access_token: str) -> "CalendarService":
        creds = Credentials(token=access_token)
        return cls(creds)

    # ── Queries ──────────────────────────────────────────────────────────────

    def list_events(
        self,
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int = 10,
        calendar_id: str = "primary",
    ) -> list[dict[str, Any]]:
        """Return upcoming events between time_min and time_max."""
        now = datetime.utcnow().isoformat() + "Z"
        result = (
            self._service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min or now,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return [
            {
                "id": ev.get("id"),
                "summary": ev.get("summary", "(no title)"),
                "start": ev["start"].get("dateTime", ev["start"].get("date")),
                "end": ev["end"].get("dateTime", ev["end"].get("date")),
                "attendees": [
                    a.get("email") for a in ev.get("attendees", [])
                ],
            }
            for ev in result.get("items", [])
        ]

    def freebusy(
        self,
        time_min: str,
        time_max: str,
        calendar_id: str = "primary",
    ) -> list[dict[str, str]]:
        """Return busy intervals within the given window."""
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": calendar_id}],
        }
        result = self._service.freebusy().query(body=body).execute()
        calendars = result.get("calendars", {})
        busy = calendars.get(calendar_id, {}).get("busy", [])
        return [{"start": b["start"], "end": b["end"]} for b in busy]

    # ── Mutations ────────────────────────────────────────────────────────────

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        description: str = "",
        attendee_email: str = "",
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Create a calendar event and return its details."""
        body: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
        }
        if description:
            body["description"] = description
        if attendee_email:
            body["attendees"] = [{"email": attendee_email}]
            body["conferenceData"] = None  # don't auto-create a meet link

        event = (
            self._service.events()
            .insert(calendarId=calendar_id, body=body, sendUpdates="all")
            .execute()
        )
        return {
            "id": event["id"],
            "summary": event.get("summary"),
            "start": event["start"].get("dateTime"),
            "end": event["end"].get("dateTime"),
            "htmlLink": event.get("htmlLink", ""),
        }

    def update_event(
        self,
        event_id: str,
        summary: str = "",
        start: str = "",
        end: str = "",
        description: str = "",
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Patch an existing event."""
        body: dict[str, Any] = {}
        if summary:
            body["summary"] = summary
        if start:
            body["start"] = {"dateTime": start}
        if end:
            body["end"] = {"dateTime": end}
        if description:
            body["description"] = description

        event = (
            self._service.events()
            .patch(calendarId=calendar_id, eventId=event_id, body=body, sendUpdates="all")
            .execute()
        )
        return {
            "id": event["id"],
            "summary": event.get("summary"),
            "start": event["start"].get("dateTime"),
            "end": event["end"].get("dateTime"),
        }

    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> None:
        """Delete an event."""
        self._service.events().delete(
            calendarId=calendar_id, eventId=event_id, sendUpdates="all"
        ).execute()
