"""SSE streaming chat endpoint – maintains the same contract as the Go backend."""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Annotated, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from pydantic import BaseModel

from app.agent.agent import create_agent
from app.agent.content import get_content_loader
from app.agent.guardrails import GuardrailError, validate_input
from app.config import Settings, get_settings
from app.dependencies import get_current_user
from app.services.auth_service import AuthUser

log = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

# Shared in-memory session store (one per process – fine for single-instance deploy)
_session_service = InMemorySessionService()
APP_NAME = "jai_web_agent"


# ── Request / response models ─────────────────────────────────────────────────


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    sessionId: Optional[str] = None


# ── SSE helpers ───────────────────────────────────────────────────────────────


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _stream_agent(
    request: ChatRequest,
    settings: Settings,
    user: Optional[AuthUser],
) -> AsyncGenerator[str, None]:
    """Core streaming generator – yields SSE text chunks."""

    # ── 1. Validate input ────────────────────────────────────────────────────
    last_user_msg = next(
        (m.content for m in reversed(request.messages) if m.role == "user"), None
    )
    if not last_user_msg:
        yield _sse({"type": "error", "role": "assistant", "content": "No user message found."})
        return

    try:
        validate_input(last_user_msg)
    except GuardrailError as exc:
        log.warning("Input guardrail triggered: %s", exc)
        yield _sse({
            "type": "guardrail",
            "role": "assistant",
            "content": (
                "This assistant handles questions about Jai and simple actions it's "
                "authorized to perform (share his background, propose or book time, or "
                "provide contact options). What should it help with?"
            ),
        })
        return

    # ── 2. Session management ────────────────────────────────────────────────
    is_owner = user is not None and user.is_owner
    user_id = user.email if user else "anonymous"
    session_id = request.sessionId or str(uuid.uuid4())

    try:
        session = await _session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
    except Exception:
        session = None

    if session is None:
        session = await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    # ── 3. Build agent (inject access_token into tool closures if owner) ────
    content_loader = get_content_loader(settings.content_dir)
    agent = create_agent(
        content_loader=content_loader,
        is_owner=is_owner,
        chat_model=settings.chat_model,
    )

    # If owner, bind access_token as a partial for workspace tools
    if is_owner and user and user.access_token:
        _patch_workspace_tools(agent, user.access_token)

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=_session_service,
    )

    # ── 4. Build the message for ADK ─────────────────────────────────────────
    new_message = Content(role="user", parts=[Part.from_text(text=last_user_msg)])

    # ── 5. Send initial SSE connected event ──────────────────────────────────
    yield _sse({"type": "connected"})

    # ── 6. Stream events from ADK runner ────────────────────────────────────
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
        ):
            if not event.content or not event.content.parts:
                continue

            for part in event.content.parts:
                if part.text:
                    yield _sse({
                        "type": "text",
                        "role": "assistant",
                        "content": part.text,
                    })
                elif part.function_call:
                    yield _sse({
                        "type": "tool_call",
                        "role": "assistant",
                        "tool": {
                            "name": part.function_call.name,
                            "parameters": dict(part.function_call.args or {}),
                        },
                    })
    except asyncio.CancelledError:
        log.info("SSE stream cancelled by client (session=%s)", session_id)
    except Exception as exc:
        log.exception("Error during agent streaming: %s", exc)
        yield _sse({"type": "error", "role": "assistant", "content": "An error occurred."})


def _patch_workspace_tools(agent: object, access_token: str) -> None:
    """Inject the OAuth2 access_token into all workspace tool default args."""
    import functools

    workspace_tool_names = {
        "list_calendar_events", "create_calendar_event", "update_calendar_event",
        "delete_calendar_event", "list_emails", "get_email", "search_emails", "send_email",
    }

    if not hasattr(agent, "tools"):
        return

    patched = []
    for tool in agent.tools:
        fn = getattr(tool, "func", None) or tool
        name = getattr(fn, "__name__", "") or getattr(tool, "name", "")
        if name in workspace_tool_names:
            patched_fn = functools.partial(fn, _access_token=access_token)
            patched_fn.__name__ = fn.__name__
            patched_fn.__doc__ = fn.__doc__
            patched.append(patched_fn)
        else:
            patched.append(tool)
    agent.tools = patched


# ── Route ─────────────────────────────────────────────────────────────────────


@router.post("/chat", summary="SSE streaming chat")
async def chat(
    request: Request,
    body: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[Optional[AuthUser], Depends(get_current_user)],
) -> StreamingResponse:
    """Stream a chat response using Server-Sent Events.

    Maintains backward-compatible SSE format: `data: {JSON}\\n\\n`
    """
    return StreamingResponse(
        _stream_agent(body, settings, user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )
