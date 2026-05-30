"""One-time setup: authorize Google Calendar access and save refresh token.

Run this once:
    cd api && .venv/bin/python setup_calendar.py

It will open your browser for Google OAuth consent. After you authorize,
the refresh token is saved and calendar tools work for all visitors forever.
"""
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

# Load config from .env
from app.config import get_settings

settings = get_settings()

CLIENT_ID = settings.google_client_id
CLIENT_SECRET = settings.google_client_secret
REDIRECT_URI = "http://localhost:9090/callback"
TOKEN_PATH = Path(__file__).parent / ".google_refresh_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]

AUTH_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
    f"&scope={'+'.join(SCOPES)}"
    f"&access_type=offline"
    f"&prompt=consent"
)


class CallbackHandler(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        CallbackHandler.code = query.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Done! You can close this tab.</h2>")

    def log_message(self, format, *args):
        pass  # silence logs


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env")
        return

    print("Opening browser for Google OAuth consent...")
    print(f"(If it doesn't open, visit: {AUTH_URL})\n")
    webbrowser.open(AUTH_URL)

    server = HTTPServer(("localhost", 9090), CallbackHandler)
    server.handle_request()  # wait for one callback

    code = CallbackHandler.code
    if not code:
        print("ERROR: No authorization code received.")
        return

    print("Exchanging code for tokens...")
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    tokens = resp.json()

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("ERROR: No refresh token returned. Try revoking app access at")
        print("https://myaccount.google.com/permissions and running again.")
        return

    TOKEN_PATH.write_text(json.dumps({"refresh_token": refresh_token}))
    print(f"\nRefresh token saved to {TOKEN_PATH}")
    print("Calendar tools are now active for all visitors!\n")
    print("For production, add this to your environment:")
    print(f"  GOOGLE_REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    main()
