import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Intervals.icu MCP Proxy")

ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID", "")
API_KEY = os.getenv("INTERVALS_API_KEY", "")  # from Intervals settings (Developer Settings)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
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

if __name__ == "__main__":
    # Streamable HTTP endpoint at /mcp
    mcp.run(transport="http", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), path="/mcp")
