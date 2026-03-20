"""Feedback form endpoint."""
from __future__ import annotations

import logging
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.email_service import FeedbackPayload, SMTPEmailService

log = logging.getLogger(__name__)
router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    message: str
    name: Optional[str] = None
    email: Optional[str] = None
    page: Optional[str] = None


def _make_email_service(settings: Settings) -> SMTPEmailService:
    return SMTPEmailService(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        from_email=settings.smtp_from_email,
        feedback_email=settings.feedback_email,
    )


@router.post("/feedback", summary="Submit feedback")
async def submit_feedback(
    body: FeedbackRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    if not body.message or not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    if len(body.message) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message too long (max 5000 characters).",
        )

    if not settings.smtp_username or not settings.smtp_password:
        log.warning("SMTP not configured – feedback received but not emailed")
        return JSONResponse(
            content={
                "status": "received",
                "message": "Feedback received (email delivery not configured).",
                "id": str(uuid.uuid4()),
            }
        )

    svc = _make_email_service(settings)
    payload = FeedbackPayload(
        message=body.message.strip(),
        name=body.name or "",
        email=body.email or "",
        page=body.page or "",
    )

    try:
        await svc.send_feedback(payload)
    except Exception as exc:
        log.error("Failed to send feedback: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not deliver feedback. Please try again later.",
        )

    feedback_id = str(uuid.uuid4())
    return JSONResponse(
        content={
            "status": "sent",
            "message": "Thank you for your feedback!",
            "id": feedback_id,
        }
    )
