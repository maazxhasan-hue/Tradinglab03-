"""Daily read-only company review; only explicit direct-client projects rank in the queue."""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEADS_FILE = ROOT / "data" / "leads.json"
OUT_FILE = ROOT / "data" / "opportunities" / "daily-company-review.md"
TERMINAL_STATUSES = {"lost", "do_not_contact", "paid_verified"}


def _score(lead: dict) -> int:
    try:
        return int(lead.get("opportunity_score", 0) or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def _is_active(lead: dict) -> bool:
    return str(lead.get("status", "new")).strip().lower() not in TERMINAL_STATUSES


def _is_direct_client_project(lead: dict) -> bool:
    return lead.get("opportunity_type") == "client_project" and lead.get("client_fit") is True and _is_active(lead)


def main() -> int:
    lines = [
        "# TradingLab03 — Daily Company Review", "",
        f"- Generated (UTC): {datetime.now(timezone.utc).isoformat()}",
        "- Scope: read-only summary of tracked leads and automation files.",
        "- Listings are unverified opportunities, not confirmed clients, contracts, or revenue.",
        "- Only explicitly classified active direct-client projects appear in the priority queue.", "",
        "## Automation configuration",
    ]
    for rel in [
        ".github/workflows/hourly-opportunity-scout.yml",
        ".github/workflows/company-health-check.yml",
        ".github/workflows/daily-company-operations.yml",
        ".github/workflows/agent-worker.yml",
    ]:
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

    valid = [x for x in leads if isinstance(x, dict)]
    statuses = Counter(str(x.get("status", "unknown")) for x in valid)
    direct = [x for x in valid if _is_direct_client_project(x)]
    excluded = [x for x in valid if not _is_direct_client_project(x)]
    direct.sort(key=lambda x: (
        {"high": 0, "review": 1, "medium": 1, "low": 2}.get(str(x.get("opportunity_priority", "")).lower(), 3),
        -_score(x), str(x.get("created_at", "")),
    ))

    lines += ["", "## Snapshot", "", f"- Total tracked records: {len(leads)}",
              f"- Direct client-project candidates (explicit buyer intent): {len(direct)}",
              f"- Historical, unclassified, non-client, or closed records kept out of the priority queue: {len(excluded)}"]
    lines += [f"- Status {key}: {value}" for key, value in sorted(statuses.items())]
    lines += ["", "## Highest-priority direct client-project queue", ""]
    if not direct:
        lines.append("No active records currently meet the strict direct-client classification. Review fresh scout results; do not relabel old or employment listings without evidence.")
    for lead in direct[:15]:
        title = str(lead.get("business_name", "Untitled listing")).replace("\n", " ")[:160]
        url = str(lead.get("source_url", "")).strip()
        lines.append(f"- **{title}** — priority {lead.get('opportunity_priority', 'unranked')}, score {lead.get('opportunity_score', 'n/a')}, status {lead.get('status', 'unknown')}")
        if url.startswith("https://"):
            lines.append(f"  - Source: {url}")
        lines.append(f"  - Next step: {str(lead.get('next_action', 'Verify listing and suitability before acting.'))[:300]}")

    lines += ["", "## Historical / unclassified records not promoted as client leads", "",
              "These records are retained for auditability. Missing buyer-intent evidence, an employment classification, or a closed status means they are not presented as direct client prospects."]
    for lead in excluded[:10]:
        title = str(lead.get("business_name", "Untitled listing")).replace("\n", " ")[:160]
        url = str(lead.get("source_url", "")).strip()
        lines.append(f"- **{title}** — type: {lead.get('opportunity_type', 'unclassified')}; source: {lead.get('source_name', 'unknown source')}; status: {lead.get('status', 'unknown')}; reason: not explicitly classified as an active direct client project")
        if url.startswith("https://"):
            lines.append(f"  - Source: {url}")

    lines += ["", "## Required human checks before pursuing a lead",
              "- Open the original listing and confirm it is still active and accepts applications from your location.",
              "- Confirm buyer intent, language, country eligibility, platform rules/fees, scope, deadline, and payment terms.",
              "- Check the scope against actual skills and available time; do not claim unverified portfolio work.",
              "- Keep proposal and outreach drafts in review until explicitly approved.",
              "- Count revenue only after payment is independently confirmed and refunds are accounted for.",
              "", "## Not automatically performed",
              "- No bids, cold messages, social posts, contracts, purchases, deployments, or payments are made.",
              "- This report does not prove external accounts, AI credentials, notifications, or client delivery are operational.",
              "- Trading bot, Angel One, and MCX settings are out of scope and are not accessed or modified.", ""]
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_FILE.relative_to(ROOT)} with {len(leads)} tracked records and {len(direct)} direct client-project candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
