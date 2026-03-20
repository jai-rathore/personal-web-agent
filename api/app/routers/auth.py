"""Google OAuth2 authentication router."""
from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import Settings, get_settings
from app.dependencies import get_current_user
from app.services.auth_service import AuthService, AuthUser

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _make_auth_service(settings: Settings) -> AuthService:
    return AuthService(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
        owner_emails=settings.owner_email_set,
        jwt_secret=settings.jwt_secret,
        jwt_algorithm=settings.jwt_algorithm,
        jwt_expire_minutes=settings.jwt_expire_minutes,
    )


@router.get("/google", summary="Initiate Google OAuth2 login")
async def login_google(settings: Annotated[Settings, Depends(get_settings)]) -> RedirectResponse:
    """Redirect the user to Google's OAuth2 consent screen."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth2 is not configured on this server.",
        )
    auth_service = _make_auth_service(settings)
    url, _ = auth_service.get_authorization_url()
    return RedirectResponse(url=url)


@router.get("/google/callback", summary="Google OAuth2 callback")
async def google_callback(
    code: str,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedirectResponse:
    """Handle Google OAuth2 callback, set session cookie, and redirect to frontend."""
    auth_service = _make_auth_service(settings)

    try:
        user = await auth_service.exchange_code(code)
    except Exception as exc:
        log.error("OAuth2 code exchange failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code.",
        )

    token = auth_service.create_session_token(user)

    # Redirect back to the frontend origin (use first in the list)
    frontend_origin = settings.allowed_origins_list[0].rstrip("/")
    redirect = RedirectResponse(url=f"{frontend_origin}/")

    redirect.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    log.info("Session cookie set for %s (owner=%s)", user.email, user.is_owner)
    return redirect


@router.get("/me", summary="Get current authenticated user")
async def get_me(
    user: Annotated[Optional[AuthUser], Depends(get_current_user)],
) -> JSONResponse:
    """Return the currently authenticated user, or null if not logged in."""
    if user is None:
        return JSONResponse(content={"authenticated": False, "user": None})
    return JSONResponse(
        content={
            "authenticated": True,
            "user": {
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "is_owner": user.is_owner,
            },
        }
    )


@router.post("/logout", summary="Log out and clear session cookie")
async def logout(response: Response) -> JSONResponse:
    """Clear the session cookie."""
    response.delete_cookie(key="session_token")
    return JSONResponse(content={"status": "logged_out"})
