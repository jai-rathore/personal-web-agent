"""Google OAuth2 authentication service."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import jwt

log = logging.getLogger(__name__)


@dataclass
class AuthUser:
    email: str
    name: str
    picture: str
    is_owner: bool
    access_token: str = ""


class AuthService:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        owner_emails: set[str],
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expire_minutes: int = 60 * 24 * 7,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._owner_emails = owner_emails
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._jwt_expire_minutes = jwt_expire_minutes

    def get_authorization_url(self) -> tuple[str, str]:
        """Return (authorization_url, state) for redirecting the user to Google."""
        from authlib.integrations.httpx_client import AsyncOAuth2Client

        client = AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=self._redirect_uri,
        )
        url, state = client.create_authorization_url(
            "https://accounts.google.com/o/oauth2/v2/auth",
            scope=[
                "openid",
                "email",
                "profile",
                # Workspace scopes – needed for gws CLI delegation
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/gmail.modify",
            ],
            access_type="offline",
            prompt="consent",
        )
        return url, state

    async def exchange_code(self, code: str) -> AuthUser:
        """Exchange an authorization code for tokens and return an AuthUser."""
        import httpx

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()

            # Fetch user info
            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()

        email = userinfo.get("email", "").lower()
        is_owner = email in self._owner_emails
        log.info("OAuth2 login: email=%s is_owner=%s", email, is_owner)

        return AuthUser(
            email=email,
            name=userinfo.get("name", ""),
            picture=userinfo.get("picture", ""),
            is_owner=is_owner,
            access_token=tokens.get("access_token", ""),
        )

    def create_session_token(self, user: AuthUser) -> str:
        """Issue a signed JWT session token."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._jwt_expire_minutes)
        payload = {
            "sub": user.email,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "is_owner": user.is_owner,
            "access_token": user.access_token,
            "exp": expire,
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)
