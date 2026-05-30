"""Calendly API service — checks availability across all connected calendars.

Calendly aggregates Google Calendar + Outlook + others, so availability
reflects the true picture across work and personal calendars.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

log = logging.getLogger(__name__)

BASE_URL = "https://api.calendly.com"


class CalendlyService:
    """Thin wrapper around Calendly API v2."""

    def __init__(self, api_key: str, event_type_uri: str = "") -> None:
        self._api_key = api_key
        self._event_type_uri = event_type_uri
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_user(self) -> dict[str, Any]:
        """Get the current Calendly user info."""
        resp = httpx.get(f"{BASE_URL}/users/me", headers=self._headers)
        resp.raise_for_status()
        return resp.json().get("resource", {})

    def get_event_types(self, user_uri: str = "") -> list[dict[str, Any]]:
        """List event types for the user."""
        if not user_uri:
            user_uri = self.get_user().get("uri", "")
        resp = httpx.get(
            f"{BASE_URL}/event_types",
            headers=self._headers,
            params={"user": user_uri, "active": "true"},
        )
        resp.raise_for_status()
        return resp.json().get("collection", [])

    def get_available_times(
        self,
        start_time: str,
        end_time: str,
        event_type_uri: str = "",
    ) -> list[dict[str, str]]:
        """Get available time slots for a date range.

        Args:
            start_time: ISO 8601 start (any timezone — will be converted to UTC)
            end_time: ISO 8601 end (any timezone — will be converted to UTC)
            event_type_uri: Calendly event type URI (uses default if not provided)

        Returns:
            List of available slots with start_time and status.
        """
        uri = event_type_uri or self._event_type_uri
        if not uri:
            raise ValueError("No event_type_uri configured. Set CALENDLY_EVENT_TYPE_URI in .env")

        # Calendly API requires UTC timestamps
        start_dt = datetime.fromisoformat(start_time).astimezone(timezone.utc)
        end_dt = datetime.fromisoformat(end_time).astimezone(timezone.utc)

        resp = httpx.get(
            f"{BASE_URL}/event_type_available_times",
            headers=self._headers,
            params={
                "event_type": uri,
                "start_time": start_dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
                "end_time": end_dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
            },
        )
        resp.raise_for_status()
        collection = resp.json().get("collection", [])

        return [
            {
                "start_time": slot["start_time"],
                "status": slot.get("status", "available"),
            }
            for slot in collection
            if slot.get("status") == "available"
        ]
