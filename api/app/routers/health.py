"""Health check and privacy endpoints."""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.agent.content import get_content_loader
from app.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Health check")
async def healthz(
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    content_loader = get_content_loader(settings.content_dir)
    return JSONResponse(
        content={
            "status": "ok",
            "environment": settings.environment,
            "build_sha": settings.build_sha,
            "content_checksums": content_loader.checksums,
        }
    )


@router.get("/privacy", summary="Privacy notice")
async def privacy() -> JSONResponse:
    return JSONResponse(
        content={
            "title": "Privacy Notice",
            "last_updated": "2026-03-19",
            "summary": (
                "This site does not store conversation history. "
                "Chat messages are processed transiently by Google Gemini. "
                "Feedback submissions are emailed and not stored in any database. "
                "No cookies are set unless you choose to sign in with Google, "
                "in which case a session cookie is used solely to maintain your login state."
            ),
            "contact": "jaiadityarathore@gmail.com",
        }
    )
