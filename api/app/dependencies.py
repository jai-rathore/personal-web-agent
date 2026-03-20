"""FastAPI dependency injection helpers."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt

from app.config import Settings, get_settings
from app.services.auth_service import AuthUser


def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    session_token: Annotated[Optional[str], Cookie()] = None,
) -> Optional[AuthUser]:
    """Return the authenticated user from JWT session cookie, or None."""
    if not session_token:
        return None
    try:
        payload = jwt.decode(
            session_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return AuthUser(
            email=payload["email"],
            name=payload.get("name", ""),
            picture=payload.get("picture", ""),
            is_owner=payload.get("is_owner", False),
            access_token=payload.get("access_token", ""),
        )
    except JWTError:
        return None


def require_owner(
    user: Annotated[Optional[AuthUser], Depends(get_current_user)],
) -> AuthUser:
    """Raise 401 if the caller is not the authenticated owner."""
    if user is None or not user.is_owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Owner authentication required",
        )
    return user
