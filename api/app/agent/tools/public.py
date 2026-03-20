"""Public tools – available to all users, no authentication required."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.content import ContentLoader


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
