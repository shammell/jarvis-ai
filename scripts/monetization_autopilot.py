#!/usr/bin/env python3
"""
Monetization autopilot for JARVIS.

Reads repository audit outputs and generates a practical revenue plan.

Input:
- analysis/FULL_REPO_AUDIT_REPORT.json

Outputs:
- analysis/MONETIZATION_AUTOPILOT_PLAN.json
- analysis/MONETIZATION_AUTOPILOT_PLAN.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass
class Offer:
    name: str
    customer: str
    value_prop: str
    launch_readiness: int
    build_effort_days: int
    pricing: str
    channel: str
    first_month_target: str


def load_audit(root: Path) -> Dict:
    audit_path = root / "analysis" / "FULL_REPO_AUDIT_REPORT.json"
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing audit report: {audit_path}")
    return json.loads(audit_path.read_text(encoding="utf-8"))


def capability_ready(audit: Dict, key: str) -> bool:
    cap = audit.get("capabilities", {}).get(key, {})
    return cap.get("status") == "implemented" and cap.get("readiness") == "launch_candidate"


def make_offers(audit: Dict) -> List[Offer]:
    whatsapp_ready = capability_ready(audit, "whatsapp_bridge")
    api_ready = capability_ready(audit, "api_message_processing")
    memory_ready = capability_ready(audit, "memory_hybrid")
    reasoning_ready = capability_ready(audit, "system2_reasoning")

    offers: List[Offer] = []

    if whatsapp_ready and api_ready:
        offers.append(
            Offer(
                name="WhatsApp AI Assistant for Local Businesses",
                customer="Shops, clinics, agencies, freelancers",
                value_prop="Automate lead replies, FAQs, booking, and follow-up in WhatsApp",
                launch_readiness=9,
                build_effort_days=3,
                pricing="$99-$299/month per business",
                channel="Direct outreach + referrals + demo video",
                first_month_target="5 paying clients ($500-$1,500 MRR)",
            )
        )

    if api_ready and memory_ready:
        offers.append(
            Offer(
                name="Private Knowledge Copilot (RAG)",
                customer="Small teams with docs/SOPs/support history",
                value_prop="Team Q&A over internal data with memory and faster support answers",
                launch_readiness=8,
                build_effort_days=5,
                pricing="$199 setup + $49-$199/user/month",
                channel="LinkedIn founder outreach + niche communities",
                first_month_target="2 teams (>$1,000 revenue)",
            )
        )

    if api_ready and reasoning_ready:
        offers.append(
            Offer(
                name="AI Workflow API for Developers",
                customer="Developers and small SaaS teams",
                value_prop="Reasoning + memory + tool orchestration API endpoint",
                launch_readiness=7,
                build_effort_days=7,
                pricing="Free tier + usage-based paid plans",
                channel="Product Hunt + X + GitHub demos",
                first_month_target="100 signups, 10 paid",
            )
        )

    if not offers:
        offers.append(
            Offer(
                name="Custom AI Automation Consulting",
                customer="Any SMB with repetitive workflows",
                value_prop="Manual-to-AI workflow automation using your current stack",
                launch_readiness=6,
                build_effort_days=2,
                pricing="$500-$2,000/project",
                channel="Freelance marketplaces + direct network",
                first_month_target="2 projects",
            )
        )

    return offers


def top_offer(offers: List[Offer]) -> Offer:
    return sorted(
        offers,
        key=lambda o: (o.launch_readiness, -o.build_effort_days),
        reverse=True,
    )[0]


def generate_execution_plan(best: Offer) -> Dict:
    return {
        "72_hour_sprint": [
            "Deploy production stack on one VPS (API + gRPC + WhatsApp + Redis)",
            "Create one niche demo (e.g., clinic booking assistant)",
            "Record 90-second demo video and publish landing page",
            "Send 50 targeted outreach messages to ideal customers",
            "Offer first 3 clients discounted onboarding for quick testimonials",
        ],
        "week_1": [
            "Onboard first 1-2 clients manually",
            "Track response quality, latency, and conversion",
            "Add simple client dashboard and weekly performance report",
            "Collect case study metrics (leads handled, response speed, bookings)",
        ],
        "week_2_to_4": [
            "Standardize onboarding checklist and templates",
            "Raise price for new clients after first proof",
            "Launch referral incentive for existing clients",
            "Ship upsell: knowledge base add-on and analytics",
        ],
        "kpis": {
            "north_star": "Monthly recurring revenue",
            "week_1": "1 paying client",
            "week_2": "3 paying clients",
            "day_30": "5-10 paying clients",
        },
        "best_offer": asdict(best),
    }


def to_markdown(offers: List[Offer], plan: Dict) -> str:
    lines: List[str] = []
    lines.append("# Monetization Autopilot Plan")
    lines.append("")
    lines.append("## Best Immediate Offer")
    best = plan["best_offer"]
    lines.append(f"- Offer: {best['name']}")
    lines.append(f"- Customer: {best['customer']}")
    lines.append(f"- Value: {best['value_prop']}")
    lines.append(f"- Pricing: {best['pricing']}")
    lines.append(f"- Channel: {best['channel']}")
    lines.append(f"- First month target: {best['first_month_target']}")
    lines.append("")

    lines.append("## Offer Stack")
    for offer in offers:
        lines.append(f"- {offer.name} | readiness={offer.launch_readiness}/10 | effort={offer.build_effort_days} days | pricing={offer.pricing}")
    lines.append("")

    lines.append("## 72-Hour Sprint")
    for step in plan["72_hour_sprint"]:
        lines.append(f"- {step}")
    lines.append("")

    lines.append("## Week 1")
    for step in plan["week_1"]:
        lines.append(f"- {step}")
    lines.append("")

    lines.append("## Week 2-4")
    for step in plan["week_2_to_4"]:
        lines.append(f"- {step}")
    lines.append("")

    lines.append("## KPI Targets")
    for k, v in plan["kpis"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    root = Path(".").resolve()
    audit = load_audit(root)
    offers = make_offers(audit)
    best = top_offer(offers)
    plan = generate_execution_plan(best)

    out_dir = root / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "MONETIZATION_AUTOPILOT_PLAN.json"
    md_path = out_dir / "MONETIZATION_AUTOPILOT_PLAN.md"

    payload = {
        "offers": [asdict(o) for o in offers],
        "execution_plan": plan,
    }

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(offers, plan), encoding="utf-8")

    print(f"[OK] Wrote {json_path}")
    print(f"[OK] Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
