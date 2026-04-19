SKILL_NAME = "price"
SKILL_DESC = "Crypto and stock prices in real-time"
SKILL_TRIGGERS = ["bitcoin", "crypto", "btc", "eth",
                  "ethereum", "price", "stock price",
                  "kya rate", "kitna hai", "current price",
                  "market", "share price", "crypto rate"]
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "jarvis"

import httpx
import re

async def run(task: str, context: str = "") -> str:
    """Get crypto prices from CoinGecko (free, no key)."""
    try:
        # Map common names to CoinGecko IDs
        crypto_map = {
            "bitcoin": "bitcoin", "btc": "bitcoin",
            "ethereum": "ethereum", "eth": "ethereum",
            "usdt": "tether", "tether": "tether",
            "bnb": "binancecoin", "binance": "binancecoin",
            "sol": "solana", "solana": "solana",
            "xrp": "ripple", "ripple": "ripple",
            "usdc": "usd-coin",
            "doge": "dogecoin", "dogecoin": "dogecoin",
            "ada": "cardano", "cardano": "cardano",
        }

        task_lower = task.lower()
        coins_requested = []
        for name, coin_id in crypto_map.items():
            if name in task_lower and coin_id not in coins_requested:
                coins_requested.append(coin_id)

        if not coins_requested:
            # Default: show top 5
            coins_requested = [
                "bitcoin", "ethereum", "tether",
                "binancecoin", "solana"
            ]

        ids_str = ",".join(coins_requested[:5])

        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": ids_str,
                    "vs_currencies": "usd,pkr",
                    "include_24hr_change": "true",
                    "include_market_cap": "false",
                }
            )
            data = r.json()

        if not data:
            return "❌ Price data unavailable"

        lines = ["💰 *Crypto Prices*\n"]
        for coin_id, prices in data.items():
            usd = prices.get("usd", 0)
            pkr = prices.get("pkr", 0)
            change = prices.get("usd_24h_change", 0)
            arrow = "📈" if change >= 0 else "📉"
            name = coin_id.replace("-", " ").title()

            lines.append(
                f"{arrow} *{name}*\n"
                f"   ${usd:,.2f} | PKR {pkr:,.0f}\n"
                f"   24h: {change:+.2f}%"
            )

        lines.append("\n_Source: CoinGecko (live)_")
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Price error: {e}"