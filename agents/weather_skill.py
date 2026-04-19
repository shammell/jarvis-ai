SKILL_NAME = "weather"
SKILL_DESC = "Get current weather for any city"
SKILL_TRIGGERS = ["weather", "mausam", "garmi", "sardi",
                  "barish", "temperature", "aaj ka mausam",
                  "how hot", "how cold"]
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "jarvis"

import httpx
import re

async def run(task: str, context: str = "") -> str:
    """Get weather via wttr.in (always free, no API key)."""
    try:
        # Extract city from task
        patterns = [
            r"(?:weather|mausam)\s+(?:in|of|mein)\s+([\w\s]+?)(?:\?|$|\.|,)",
            r"([\w]+(?:\s+[\w]+)?)\s+(?:weather|mausam)",
        ]
        city = "Karachi"  # Default for Pakistan users
        for pat in patterns:
            m = re.search(pat, task, re.I)
            if m:
                city = m.group(1).strip()
                break

        # wttr.in: free, no API key, always works
        async with httpx.AsyncClient(timeout=8) as client:
            # Format 3: one-line compact
            r = await client.get(
                f"https://wttr.in/{city}?format=3",
                headers={"User-Agent": "JARVIS/3.0"}
            )
            one_line = r.text.strip()

            # Format j1: JSON for details
            r2 = await client.get(
                f"https://wttr.in/{city}?format=j1",
                headers={"User-Agent": "JARVIS/3.0"}
            )

        if r.status_code == 200:
            import json
            try:
                data = r2.json()
                current = data["current_condition"][0]
                feels = current.get("FeelsLikeC", "?")
                humidity = current.get("humidity", "?")
                wind = current.get("windspeedKmph", "?")
                desc = current.get("weatherDesc", [{}])[0].get("value", "")

                return (
                    f"🌤️ *{city} Weather*\n\n"
                    f"{one_line}\n"
                    f"Feels like: {feels}°C\n"
                    f"Humidity: {humidity}%\n"
                    f"Wind: {wind} km/h\n"
                    f"_{desc}_"
                )
            except Exception:
                return f"🌤️ {one_line}"

        return f"❌ Weather not found for '{city}'"

    except Exception as e:
        return f"❌ Weather error: {e}"