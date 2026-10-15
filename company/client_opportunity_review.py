"""Prepare local proposal drafts for saved client-project leads; never send them."""
from __future__ import annotations
import json
from pathlib import Path
from company.client_pipeline import build_pack_from_lead

ROOT = Path(__file__).resolve().parents[1]
LEADS_FILE = ROOT / "data" / "leads.json"
OUT_DIR = ROOT / "data" / "client_packs" / "daily_review"


def main() -> int:
    store = json.loads(LEADS_FILE.read_text(encoding="utf-8"))
    leads = store.get("leads", []) if isinstance(store, dict) else []
    if not isinstance(leads, list):
        raise ValueError("Lead store must contain a leads list")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    eligible = [
        lead for lead in leads
        if isinstance(lead, dict)
        and lead.get("opportunity_type") == "client_project"
        and lead.get("client_fit") is True
        and lead.get("status", "new") not in {"do_not_contact", "lost"}
    ]
    created = 0
    skipped = []
    for lead in eligible:
        lead_id = str(lead.get("id", "")).strip()
        if not lead_id:
            skipped.append("Skipped client-project record without an ID")
            continue
        try:
            pack = build_pack_from_lead(lead_id, store_path=LEADS_FILE)
        except (ValueError, KeyError, TypeError) as exc:
            skipped.append(f"{lead_id}: {exc}")
            continue
        safe_id = "".join(ch for ch in lead_id if ch.isalnum() or ch in "-_")[:80]
        (OUT_DIR / f"{safe_id}.md").write_text(pack["proposal_markdown"], encoding="utf-8")
        (OUT_DIR / f"{safe_id}.json").write_text(
            json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        created += 1
    report = [
        "# Client Opportunity Draft Queue", "",
        f"- Saved leads scanned: {len(leads)}",
        f"- Client-project leads considered: {len(eligible)}",
        f"- Draft packs generated: {created}",
        f"- Drafts skipped: {len(skipped)}",
        "", "## Safety / review requirements",
        "- Every pack is an unapproved draft; no messages, bids, or proposals were sent.",
        "- Listings are not verified clients or guaranteed paid contracts.",
        "- Check listing is still active, eligibility, platform fees, scope, evidence, language, deadlines, and payment terms before any action.",
        "- Pricing is unset unless an operator explicitly supplied it.",
        "- Trading bot, Angel One, and MCX settings are not accessed or modified.",
        "", "## Skipped records", ""
    ]
    report.extend(f"- {item}" for item in skipped)
    (OUT_DIR / "README-review.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"saved_leads": len(leads), "eligible_client_projects": len(eligible),
                      "draft_packs_generated": created, "skipped": skipped,
                      "sent": False}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
