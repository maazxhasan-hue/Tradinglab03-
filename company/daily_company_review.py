"""Build a daily, read-only company operations summary from the tracked lead store.

This report is advisory: listings are not verified clients, and no external
messages, bids, purchases, deployments, or payments are performed.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEADS_FILE = ROOT / "data" / "leads.json"
OUT_FILE = ROOT / "data" / "opportunities" / "daily-company-review.md"


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# TradingLab03 — Daily Company Review",
        "",
        f"- Generated (UTC): {now}",
        "- Scope: read-only summary of the repository's tracked lead file and automation files.",
        "- Important: listings are unverified opportunities, not confirmed clients or revenue.",
        "",
        "## Automation configuration",
    ]
    workflow_paths = [
        ".github/workflows/hourly-opportunity-scout.yml",
        ".github/workflows/company-health-check.yml",
        ".github/workflows/daily-company-operations.yml",
        ".github/workflows/agent-worker.yml",
    ]
    for rel in workflow_paths:
        lines.append(f"- [{'x' if (ROOT / rel).is_file() else ' '}] {rel}")

    if not LEADS_FILE.exists():
        lines += ["", "## Lead tracker", "", "No data/leads.json file is present in this checkout."]
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(OUT_FILE)
        return 0

    try:
        store = json.loads(LEADS_FILE.read_text(encoding="utf-8"))
        leads = store.get("leads", []) if isinstance(store, dict) else []
        if not isinstance(leads, list):
            raise ValueError("Expected a 'leads' array")
    except Exception as exc:
        lines += ["", "## Lead tracker", "", f"ERROR: Could not read lead tracker: {exc}"]
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(OUT_FILE)
        return 1

    statuses = Counter(str(x.get("status", "unknown")) for x in leads if isinstance(x, dict))
    lines += ["", "## Snapshot", "", f"- Total tracked records: {len(leads)}"]
    lines += [f"- Status {key}: {value}" for key, value in sorted(statuses.items())]
    lines += ["", "## Highest-priority review queue", ""]
    valid = [x for x in leads if isinstance(x, dict)]

    def score_for_sort(lead: dict) -> int:
        # Malformed public-feed data must not crash the daily report.
        try:
            return int(lead.get("opportunity_score", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            return 0

    valid.sort(key=lambda x: (
        {"high": 0, "medium": 1, "low": 2}.get(str(x.get("opportunity_priority", "")).lower(), 3),
        -score_for_sort(x),
        str(x.get("created_at", "")),
    ))
    for lead in valid[:15]:
        title = str(lead.get("business_name", "Untitled listing")).replace("\n", " ")[:160]
        url = str(lead.get("source_url", "")).strip()
        status = str(lead.get("status", "unknown"))
        priority = str(lead.get("opportunity_priority", "unranked"))
        score = lead.get("opportunity_score", "n/a")
        lines.append(f"- **{title}** — priority {priority}, score {score}, status {status}")
        if url.startswith("https://"):
            lines.append(f"  - Source: {url}")
        lines.append(f"  - Next step: {str(lead.get('next_action', 'Verify listing and suitability before acting.'))[:300]}")
    lines += [
        "",
        "## Required human checks before pursuing a lead",
        "- Open the original listing and confirm it is still active and accepts applications from your location.",
        "- Distinguish direct client projects from employment listings, and confirm payment terms and platform rules.",
        "- Check the scope against actual skills and available time; do not claim unverified portfolio work.",
        "- Keep proposal and outreach drafts in review until explicitly approved.",
        "- Count revenue only after payment is independently confirmed and refunds are accounted for.",
        "",
        "## Not automatically performed",
        "- No bids, cold messages, social posts, contracts, purchases, deployments, or payments are made.",
        "- This script does not prove GitHub schedules, the public site, third-party accounts, AI credentials, or notifications are operational.",
        "- Trading bot, Angel One, and MCX settings are out of scope and are not accessed or modified.",
        "",
    ]
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_FILE.relative_to(ROOT)} with {len(leads)} tracked records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
