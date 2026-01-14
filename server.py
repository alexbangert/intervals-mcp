import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Intervals.icu MCP Proxy")

ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID", "")
API_KEY = os.getenv(
    "INTERVALS_API_KEY", ""
)  # from Intervals settings (Developer Settings)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
BASE_URL = "https://intervals.icu"


def berlin_today() -> datetime:
    return datetime.now(ZoneInfo("Europe/Berlin"))


@mcp.tool
async def get_last4w_events() -> dict:
    """
    Fetch Intervals.icu calendar events for the last 4 weeks.
    """
    if not API_KEY:
        return {"error": "Missing INTERVALS_API_KEY env var"}

    newest = berlin_today().date()
    oldest = newest - timedelta(days=28)

    url = f"{BASE_URL}/api/v1/athlete/{ATHLETE_ID}/events"
    params = {"oldest": oldest.isoformat(), "newest": newest.isoformat()}

    # Intervals.icu API: Basic Auth (username 'API_KEY', password = your API key)
    # Source: Intervals.icu forum API guide.
    auth = ("API_KEY", API_KEY)  # :contentReference[oaicite:2]{index=2}

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params, auth=auth)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}

    return {
        "request": {"url": url, "params": params, "status": r.status_code},
        "data": data,
    }


@mcp.tool
async def get_events(oldest: str, newest: str) -> dict:
    """
    Fetch Intervals.icu events between oldest and newest (YYYY-MM-DD).
    """
    if not API_KEY:
        return {"error": "Missing INTERVALS_API_KEY env var"}

    if not DATE_RE.match(oldest) or not DATE_RE.match(newest):
        return {"error": "Dates must be in YYYY-MM-DD format"}

    url = f"{BASE_URL}/api/v1/athlete/{ATHLETE_ID}/events"
    params = {"oldest": oldest, "newest": newest}
    auth = ("API_KEY", API_KEY)

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params, auth=auth)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}

    return {"status": r.status_code, "request": {"params": params}, "data": data}


@mcp.tool
async def create_event(
    category: str,
    start_date_local: str,
    type: str,
    name: str,
    description: str = "",
) -> dict:
    """
    Create a planned workout event in Intervals.icu calendar.
    Example category: WORKOUT
    Example type: Ride / Run / Swim
    start_date_local: YYYY-MM-DDTHH:MM:SS (local)
    discription: optional, must be multi-line
        Example description:
            - 15m Z2

            3x
            - 10m Z4
            - 5m Z1

            - 10m Z1
    """

    if not API_KEY:
        return {"error": "Missing INTERVALS_API_KEY env var"}

    if not DATETIME_RE.match(start_date_local):
        return {"error": "start_date_local must be YYYY-MM-DDTHH:MM:SS"}

    payload = {
        "category": category,
        "start_date_local": start_date_local,
        "type": type,
        "name": name,
        "description": description,
    }

    url = f"{BASE_URL}/api/v1/athlete/{ATHLETE_ID}/events"

    # Personal API key: Basic Auth (username 'API_KEY', password = API key)
    auth = ("API_KEY", API_KEY)

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(url, auth=auth, json=payload)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}

    return {
        "status": r.status_code,
        "request": {"url": url, "payload": payload},
        "data": data,
    }


@mcp.tool
async def get_wellness_records(oldest: str, newest: str) -> dict:
    """
    Fetch Intervals.icu wellness records for the athlete between oldest and newest (YYYY-MM-DD).
    """
    if not API_KEY:
        return {"error": "Missing INTERVALS_API_KEY env var"}

    if not DATE_RE.match(oldest) or not DATE_RE.match(newest):
        return {"error": "Dates must be in YYYY-MM-DD format"}

    url = f"{BASE_URL}/api/v1/athlete/{ATHLETE_ID}/wellness"
    params = {"oldest": oldest, "newest": newest}
    auth = ("API_KEY", API_KEY)

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params, auth=auth)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}

    return {"status": r.status_code, "request": {"params": params}, "data": data}


@mcp.tool
async def get_activity(activity_id: str) -> dict:
    """
    Fetch Intervals.icu activity by ID.
    """

    if not API_KEY:
        return {"error": "Missing INTERVALS_API_KEY env var"}

    url = f"{BASE_URL}/api/v1/activity/{activity_id}"
    auth = ("API_KEY", API_KEY)

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, auth=auth)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}

    return {"status": r.status_code, "data": data}


@mcp.tool
async def get_activity_comments(activity_id: str) -> dict:
    """
    Fetch Intervals.icu Comments for a given Activity ID

    Args:
        activity_id (str): The Activity ID to fetch comments for
    """

    if not API_KEY:
        return {"error": "Missing INTERVALS_API_KEY env var"}

    url = f"{BASE_URL}/api/v1/activity/{activity_id}/messages"
    auth = ("API_KEY", API_KEY)

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, auth=auth)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}

    return {"status": r.status_code, "data": data}


if __name__ == "__main__":
    # Streamable HTTP endpoint at /mcp
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        path="/mcp",
    )
