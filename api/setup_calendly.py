"""Helper to find your Calendly event type URI.

1. Get your Personal Access Token from: https://calendly.com/integrations/api_webhooks
2. Set CALENDLY_API_KEY in your .env
3. Run: cd api && .venv/bin/python setup_calendly.py
"""
import sys
import httpx

BASE = "https://api.calendly.com"


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_calendly.py <your-calendly-api-key>")
        print("\nGet your key from: https://calendly.com/integrations/api_webhooks")
        return

    token = sys.argv[1]
    headers = {"Authorization": f"Bearer {token}"}

    print("Fetching your Calendly user...")
    resp = httpx.get(f"{BASE}/users/me", headers=headers)
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} — {resp.text}")
        return

    user = resp.json()["resource"]
    print(f"  User: {user['name']} ({user['email']})")
    user_uri = user["uri"]

    print("\nFetching your event types...")
    resp = httpx.get(f"{BASE}/event_types", headers=headers, params={"user": user_uri, "active": "true"})
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} — {resp.text}")
        return

    event_types = resp.json()["collection"]
    if not event_types:
        print("  No active event types found.")
        return

    print(f"\n  Found {len(event_types)} event type(s):\n")
    for i, et in enumerate(event_types, 1):
        print(f"  {i}. {et['name']} ({et['duration']} min)")
        print(f"     URI: {et['uri']}")
        print(f"     URL: {et['scheduling_url']}")
        print()

    if len(event_types) == 1:
        uri = event_types[0]["uri"]
    else:
        choice = input("  Pick a number (default 1): ").strip() or "1"
        uri = event_types[int(choice) - 1]["uri"]

    print("\nAdd these to your .env:\n")
    print(f"  CALENDLY_API_KEY={token}")
    print(f"  CALENDLY_EVENT_TYPE_URI={uri}")


if __name__ == "__main__":
    main()
