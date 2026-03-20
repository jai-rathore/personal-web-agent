"""Public tools – available to all users, no authentication required."""
from __future__ import annotations


def schedule_calendly_meeting(meeting_type: str, requestor_name: str = "") -> dict:
    """Provide Jai's Calendly link for scheduling a 30-minute meeting.

    Args:
        meeting_type: Type of meeting requested (e.g. 'general', 'consultation').
        requestor_name: Name of the person requesting the meeting.

    Returns:
        A dict with the Calendly URL and scheduling instructions.
    """
    return {
        "status": "success",
        "calendly_url": "https://calendly.com/jairathore/30min",
        "message": (
            f"You can schedule a 30-minute {meeting_type} meeting with Jai using his "
            "Calendly link: https://calendly.com/jairathore/30min\n\n"
            "This lets you pick a time that works for both of you. "
            "All meetings are in Pacific Time."
        ),
        "requestor_name": requestor_name,
    }


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
