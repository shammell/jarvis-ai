SKILL_NAME = "prayer"
SKILL_DESC = "Islamic prayer times for any Pakistan city"
SKILL_TRIGGERS = ["prayer", "namaz", "azan", "fajr",
                  "zuhr", "asr", "maghrib", "isha",
                  "namaz time", "prayer time",
                  "aaj ki namaz", "salah"]
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "jarvis"

import httpx
import re
from datetime import datetime

async def run(task: str, context: str = "") -> str:
    """Get prayer times via Aladhan API (free, no key)."""
    try:
        # Extract city
        city = "Karachi"
        country = "Pakistan"
        city_patterns = [
            r"(?:in|mein|for)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
            r"([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:namaz|prayer)",
        ]
        for pat in city_patterns:
            m = re.search(pat, task, re.I)
            if m:
                potential = m.group(1).strip()
                if potential.lower() not in [
                    "namaz", "prayer", "time", "today",
                    "aaj", "mein", "for", "in"
                ]:
                    city = potential
                    break

        today = datetime.now()
        url = "http://api.aladhan.com/v1/timingsByCity"
        params = {
            "city": city,
            "country": country,
            "method": 1,  # University of Islamic Sciences, Karachi
            "date": today.strftime("%d-%m-%Y"),
        }

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            data = r.json()

        if data.get("code") != 200:
            return f"❌ Prayer times not found for {city}"

        timings = data["data"]["timings"]
        date_info = data["data"]["date"]["readable"]

        prayers = [
            ("🌅 Fajr",    timings.get("Fajr", "?")),
            ("☀️ Sunrise", timings.get("Sunrise", "?")),
            ("🌞 Zuhr",    timings.get("Dhuhr", "?")),
            ("🌤️ Asr",     timings.get("Asr", "?")),
            ("🌆 Maghrib", timings.get("Maghrib", "?")),
            ("🌙 Isha",    timings.get("Isha", "?")),
        ]

        lines = [
            f"🕌 *{city} Prayer Times*",
            f"_{date_info}_\n",
        ]
        for name, time_str in prayers:
            lines.append(f"{name}: *{time_str}*")

        lines.append(f"\n_Method: Karachi (UISK)_")
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Prayer times error: {e}"