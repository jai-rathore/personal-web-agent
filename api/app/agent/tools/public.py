"""Public tools – available to all users, no authentication required."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from app.agent.content import ContentLoader
    from app.services.calendar_service import CalendarService
    from app.services.calendly_service import CalendlyService

log = logging.getLogger(__name__)

_PT = ZoneInfo("America/Los_Angeles")


# ── Static tools ────────────────────────────────────────────────────────────


def get_contact_info(info_type: str = "all") -> dict:
    """Return Jai's public contact information.

    Args:
        info_type: One of 'email', 'linkedin', 'twitter', 'all'.

    Returns:
        A dict containing the requested contact details.
    """
    contacts = {
        "email": "jaiadityarathore@gmail.com",
        "linkedin": "https://www.linkedin.com/in/jrathore",
        "twitter": "https://x.com/Jai_A_Rathore",
        "website": "https://www.jairathore.com",
    }

    if info_type == "all":
        return {"status": "success", "contacts": contacts}

    if info_type in contacts:
        return {"status": "success", "contacts": {info_type: contacts[info_type]}}

    return {
        "status": "error",
        "message": f"Unknown info_type '{info_type}'. Use: email, linkedin, twitter, or all.",
    }


def make_lookup_knowledge_tool(content_loader: "ContentLoader"):
    """Return a lookup_knowledge function closed over the given ContentLoader."""

    def lookup_knowledge(topic: str) -> dict:
        """Search Jai's knowledge base for detailed information on a specific topic or project.

        Use this tool when a visitor or Jai asks about a specific project, experience, or
        topic that requires more depth than what is available in the base context.
        Examples: 'Tell me more about FluxBot', 'How was this website built?',
        'What is the personal web agent?'

        Args:
            topic: The topic or project to look up (e.g. 'FluxBot', 'personal web agent').

        Returns:
            A dict with the matching content, or a message indicating nothing was found.
        """
        packs = content_loader.search_packs(topic)
        if not packs:
            return {
                "status": "not_found",
                "message": f"No detailed content found for '{topic}'. Answer based on your existing context.",
            }

        results = []
        for pack in packs:
            results.append({
                "id": pack.id,
                "category": pack.category,
                "content": pack.content,
            })

        return {"status": "success", "results": results}

    return lookup_knowledge


# ── Calendar tools ──────────────────────────────────────────────────────────


def make_calendar_tools(
    cal: "CalendarService",
    calendly: "CalendlyService | None" = None,
):
    """Return public calendar tools.

    Availability is checked via Calendly (aggregates Outlook + Google Calendar).
    Booking is done via Google Calendar API (creates event + sends invite).
    Falls back to Google Calendar freebusy if Calendly is not configured.
    """

    def check_availability(date: str) -> dict:
        """Check Jai's availability for a given date.

        Returns available time slots, accounting for both his work (Outlook)
        and personal (Google) calendars. Use this when a visitor wants to
        schedule a meeting with Jai.

        Args:
            date: The date to check in YYYY-MM-DD format (e.g. '2026-06-02').

        Returns:
            A dict with available time slots for the requested date.
        """
        try:
            day = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"status": "error", "message": f"Invalid date format '{date}'. Use YYYY-MM-DD."}

        day_start = day.replace(hour=0, minute=0, second=0, tzinfo=_PT)
        day_end = day.replace(hour=23, minute=59, second=59, tzinfo=_PT)

        now = datetime.now(_PT)
        if day_end <= now:
            return {"status": "error", "message": "That date is in the past."}

        # ── Calendly path (preferred — aggregates all calendars) ────────
        if calendly:
            try:
                available = calendly.get_available_times(
                    start_time=day_start.isoformat(),
                    end_time=day_end.isoformat(),
                )
                slots = []
                for slot in available:
                    raw = slot["start_time"].replace("Z", "+00:00")
                    st = datetime.fromisoformat(raw).astimezone(_PT)
                    et = st + timedelta(minutes=30)
                    slots.append({
                        "start": st.strftime("%-I:%M %p"),
                        "end": et.strftime("%-I:%M %p"),
                        "start_iso": st.isoformat(),
                        "end_iso": et.isoformat(),
                    })

                if not slots:
                    return {
                        "status": "success",
                        "date": date,
                        "available_slots": [],
                        "message": f"No available slots on {date}.",
                    }

                return {
                    "status": "success",
                    "date": date,
                    "timezone": "America/Los_Angeles (Pacific Time)",
                    "available_slots": slots,
                }
            except Exception as exc:
                log.exception("Calendly availability check failed: %s", exc)
                # Fall through to Google Calendar fallback

        # ── Google Calendar fallback ────────────────────────────────────
        fb_start = day.replace(hour=9, minute=0, second=0, tzinfo=_PT)
        fb_end = day.replace(hour=17, minute=0, second=0, tzinfo=_PT)

        try:
            busy = cal.freebusy(
                time_min=fb_start.isoformat(),
                time_max=fb_end.isoformat(),
            )
        except Exception as exc:
            log.exception("Calendar freebusy failed: %s", exc)
            return {"status": "error", "message": "Could not check calendar. Please try again."}

        slots: list[dict[str, str]] = []
        cursor = fb_start
        if cursor < now:
            cursor = now.replace(second=0, microsecond=0)
            if cursor.minute < 30:
                cursor = cursor.replace(minute=30)
            else:
                cursor = (cursor + timedelta(hours=1)).replace(minute=0)

        busy_parsed = [
            (datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
            for b in busy
        ]

        while cursor + timedelta(minutes=30) <= fb_end:
            slot_end = cursor + timedelta(minutes=30)
            is_free = all(
                slot_end <= b_start or cursor >= b_end
                for b_start, b_end in busy_parsed
            )
            if is_free:
                slots.append({
                    "start": cursor.strftime("%-I:%M %p"),
                    "end": slot_end.strftime("%-I:%M %p"),
                    "start_iso": cursor.isoformat(),
                    "end_iso": slot_end.isoformat(),
                })
            cursor = slot_end

        if not slots:
            return {
                "status": "success",
                "date": date,
                "available_slots": [],
                "message": f"No available 30-minute slots on {date}.",
            }

        return {
            "status": "success",
            "date": date,
            "timezone": "America/Los_Angeles (Pacific Time)",
            "available_slots": slots,
        }

    def schedule_meeting(
        title: str,
        start_time: str,
        attendee_name: str,
        attendee_email: str,
        duration_minutes: int = 30,
    ) -> dict:
        """Schedule a meeting on Jai's calendar.

        IMPORTANT: Before calling this, you MUST:
        1. Use check_availability to find an open slot
        2. Confirm the exact time with the visitor
        3. Get the visitor's name and email

        Args:
            title: Meeting title (e.g. 'Chat with Alice about project').
            start_time: Start time in ISO 8601 format from check_availability results.
            attendee_name: Name of the person scheduling the meeting.
            attendee_email: Email of the person scheduling the meeting.
            duration_minutes: Meeting duration in minutes (default 30).

        Returns:
            A dict with the created event details, or an error.
        """
        try:
            start_dt = datetime.fromisoformat(start_time)
        except ValueError:
            return {"status": "error", "message": f"Invalid start_time format: {start_time}"}

        end_dt = start_dt + timedelta(minutes=duration_minutes)

        try:
            event = cal.create_event(
                summary=title,
                start=start_dt.isoformat(),
                end=end_dt.isoformat(),
                description=f"Meeting with {attendee_name} ({attendee_email})\nBooked via Jai's web agent.",
                attendee_email=attendee_email,
            )
        except Exception as exc:
            log.exception("Calendar create_event failed: %s", exc)
            return {"status": "error", "message": "Failed to create the meeting. Please try again."}

        return {
            "status": "success",
            "event_id": event["id"],
            "summary": event["summary"],
            "start": event["start"],
            "end": event["end"],
            "html_link": event.get("htmlLink", ""),
            "message": (
                f"Meeting '{event['summary']}' created! "
                f"A calendar invite has been sent to {attendee_email}."
            ),
        }

    return [check_availability, schedule_meeting]
