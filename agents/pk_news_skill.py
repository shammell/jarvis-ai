SKILL_NAME = "pk_news"
SKILL_DESC = "Latest Pakistan news from Dawn and Geo"
SKILL_TRIGGERS = ["pakistan news", "pk news", "dawn news",
                  "geo news", "aaj ki khabar", "latest news",
                  "khabar", "news today pakistan",
                  "kya ho raha", "whats happening pakistan"]
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "jarvis"

import httpx
import re

async def run(task: str, context: str = "") -> str:
    """Get Pakistan news from Dawn.com RSS."""
    feeds = [
        ("https://www.dawn.com/feed/home", "Dawn"),
        ("https://arynews.tv/feed/", "ARY"),
    ]

    all_items = []
    for feed_url, source in feeds:
        try:
            async with httpx.AsyncClient(
                timeout=8, follow_redirects=True
            ) as client:
                r = await client.get(
                    feed_url,
                    headers={"User-Agent": "JARVIS/3.0"}
                )
                if r.status_code != 200:
                    continue

            items = re.findall(
                r'<item>(.*?)</item>', r.text, re.DOTALL
            )
            for item in items[:5]:
                title_m = re.search(
                    r'<title[^>]*>(.*?)</title>',
                    item, re.DOTALL
                )
                title = re.sub(
                    r'<[^>]+>|<!\[CDATA\[|\]\]>',
                    '', title_m.group(1) if title_m else ""
                ).strip()
                if title:
                    all_items.append(f"[{source}] {title}")

        except Exception as e:
            all_items.append(f"[{source}] Feed error: {e}")

    if not all_items:
        return "❌ News fetch failed — check internet connection"

    news_lines = "\n".join(
        f"• {item}" for item in all_items[:8]
    )
    return (
        f"📰 *Pakistan Latest News*\n\n"
        f"{news_lines}\n\n"
        f"_Source: Dawn, ARY | Live RSS_"
    )