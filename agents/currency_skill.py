SKILL_NAME = "currency"
SKILL_DESC = "Currency conversion including PKR rates"
SKILL_TRIGGERS = ["currency", "convert", "usd to pkr",
                  "dollar rate", "exchange rate",
                  "kitna dollar", "rupee rate",
                  "pkr", "dollar kya hai",
                  "euro rate", "pound rate"]
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "jarvis"

import httpx
import re

async def run(task: str, context: str = "") -> str:
    """Get live exchange rates — free, no API key."""
    try:
        # Parse amount and currencies
        amount = 1.0
        from_curr = "USD"
        to_curr = "PKR"

        # Extract patterns: "100 usd to pkr", "dollar rate", etc.
        amount_m = re.search(r'(\d+(?:\.\d+)?)', task)
        if amount_m:
            amount = float(amount_m.group(1))

        # Common currency mentions
        curr_map = {
            "dollar": "USD", "usd": "USD", "$": "USD",
            "euro": "EUR", "eur": "EUR", "€": "EUR",
            "pound": "GBP", "gbp": "GBP", "£": "GBP",
            "rupee": "PKR", "pkr": "PKR", "rs": "PKR",
            "riyal": "SAR", "sar": "SAR",
            "dirham": "AED", "aed": "AED",
            "yen": "JPY", "yuan": "CNY",
        }

        task_lower = task.lower()
        currencies_found = []
        for word, code in curr_map.items():
            if word in task_lower and code not in currencies_found:
                currencies_found.append(code)

        if len(currencies_found) >= 2:
            from_curr, to_curr = (
                currencies_found[0], currencies_found[1]
            )
        elif len(currencies_found) == 1:
            if "to" in task_lower or "mein" in task_lower:
                to_curr = currencies_found[0]
            else:
                from_curr = currencies_found[0]

        # Free API: exchangerate-api.com (no key for basic)
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                f"https://open.er-api.com/v6/latest/{from_curr}"
            )
            data = r.json()

        if data.get("result") != "success":
            return "❌ Exchange rate API unavailable"

        rates = data.get("rates", {})
        rate = rates.get(to_curr, 0)

        if not rate:
            return (
                f"❌ Currency '{to_curr}' not found.\n"
                f"Available: USD, EUR, GBP, PKR, SAR, AED, JPY"
            )

        converted = amount * rate

        # Also show PKR rates for context
        pkr_rate = rates.get("PKR", 0)
        sar_rate = rates.get("SAR", 0)
        aed_rate = rates.get("AED", 0)

        result = (
            f"💱 *Currency Conversion*\n\n"
            f"{amount:,.0f} {from_curr} = "
            f"*{converted:,.2f} {to_curr}*\n\n"
            f"📊 *{from_curr} Rates:*\n"
        )
        if from_curr != "PKR":
            result += f"• 1 {from_curr} = PKR {pkr_rate:,.2f}\n"
        if from_curr != "SAR" and from_curr != "PKR":
            result += f"• 1 {from_curr} = SAR {sar_rate:.4f}\n"
        if from_curr != "AED" and from_curr != "PKR":
            result += f"• 1 {from_curr} = AED {aed_rate:.4f}\n"

        result += f"\n_Live rates from open.er-api.com_"
        return result

    except Exception as e:
        return f"❌ Currency error: {e}"