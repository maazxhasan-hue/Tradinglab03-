"""Prepare proposal drafts only for active client projects allowed by source policy."""
from __future__ import annotations
import json
from pathlib import Path
from company.client_pipeline import build_pack_from_lead
from company.daily_company_review import _exclusion_reason, _source_policies

ROOT = Path(__file__).resolve().parents[1]
LEADS_FILE = ROOT / "data" / "leads.json"
OUT_DIR = ROOT / "data" / "client_packs" / "daily_review"


def main() -> int:
    store = json.loads(LEADS_FILE.read_text(encoding="utf-8"))
    leads = store.get("leads", []) if isinstance(store, dict) else []
    if not isinstance(leads, list):
        raise ValueError("Lead store must contain a leads list")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_policies = _source_policies()
    candidate_projects = [
        lead for lead in leads
        if isinstance(lead, dict)
        and lead.get("opportunity_type") == "client_project"
        and lead.get("client_fit") is True
    ]
    eligible = [
        lead for lead in candidate_projects
        if not _exclusion_reason(lead, source_policies)
    ]
    policy_excluded = [
        lead for lead in candidate_projects
        if _exclusion_reason(lead, source_policies)
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

    ranked = sorted(
        eligible,
        key=lambda lead: (
            {"high": 0, "review": 1, "medium": 1, "low": 2}.get(
                str(lead.get("opportunity_priority", "")).lower(), 3
            ),
            -(int(lead.get("opportunity_score", 0))
              if str(lead.get("opportunity_score", "")).lstrip("-").isdigit() else 0),
        ),
    )
    shortlist = [
        "# Client Opportunity Shortlist", "",
        "Review this shortlist before applying or contacting anyone. Listings can expire and are not verified clients.",
        "",
        f"- Client-project records scanned: {len(candidate_projects)}",
        f"- Source/status-policy eligible for proposal drafting: {len(ranked)}",
        f"- Excluded by source/status policy: {len(policy_excluded)}",
        f"- Drafts prepared in this run: {created}", "",
        "| Rank | Lead | Score | Service | Status | Original listing | Draft |",
        "|---:|---|---:|---|---|---|---|",
    ]
    for index, lead in enumerate(ranked[:15], start=1):
        lead_id = str(lead.get("id", "")).strip()
        safe_id = "".join(ch for ch in lead_id if ch.isalnum() or ch in "-_")[:80]
        name = str(lead.get("business_name", "Untitled listing")).replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        service = str(lead.get("service", "unmapped")).replace("|", "/")
        status = str(lead.get("status", "new")).replace("|", "/")
        score = lead.get("opportunity_score", "—")
        source_url = str(lead.get("source_url", "")).strip()
        source_link = f"[Open listing]({source_url})" if source_url.startswith("https://") else "URL missing — verify manually"
        draft_link = f"[Draft]({safe_id}.md)" if safe_id and (OUT_DIR / f"{safe_id}.md").exists() else "Not generated"
        shortlist.append(f"| {index} | {name} ({lead_id}) | {score} | {service} | {status} | {source_link} | {draft_link} |")
    shortlist.extend([
        "", "## Before applying",
        "- Confirm the listing is still open and the buyer is genuinely seeking the listed deliverable.",
        "- Check language, country eligibility, platform rules/fees, scope, deadline, budget and payment protection.",
        "- Tailor each draft to the listing and your actual skills/portfolio; do not claim experience or results you cannot prove.",
        "- Research-only, disabled, unconfigured, closed, and do-not-contact records are not drafted for outreach.",
        "- No bids, messages, or proposals were sent by this workflow.",
    ])
    (OUT_DIR / "SHORTLIST.md").write_text("\n".join(shortlist) + "\n", encoding="utf-8")

    report = [
        "# Client Opportunity Draft Queue", "",
        f"- Saved leads scanned: {len(leads)}",
        f"- Direct client-project records considered: {len(candidate_projects)}",
        f"- Eligible after source/status policy: {len(eligible)}",
        f"- Excluded by source/status policy: {len(policy_excluded)}",
        f"- Draft packs generated: {created}",
        f"- Drafts skipped due to missing IDs or pack errors: {len(skipped)}",
        "- Operator shortlist: SHORTLIST.md", "",
        "## Safety / review requirements",
        "- Every pack is an unapproved draft; no messages, bids, or proposals were sent.",
        "- Listings are not verified clients or guaranteed paid contracts.",
        "- Research-only or disabled sources are not treated as actionable for proposal drafting.",
        "- Check listing is still active, eligibility, platform fees, scope, evidence, language, deadlines, and payment terms before any action.",
        "- Pricing is unset unless an operator explicitly supplied it.",
        "- Trading bot, Angel One, and MCX settings are not accessed or modified.",
        "", "## Policy-excluded client-project records", "",
    ]
    report.extend(
        f"- {lead.get('id', 'missing-id')}: {_exclusion_reason(lead, source_policies)}"
        for lead in policy_excluded
    )
    report.extend(["", "## Skipped pack generation", ""])
    report.extend(f"- {item}" for item in skipped)
    (OUT_DIR / "README-review.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({
        "saved_leads": len(leads),
        "candidate_client_projects": len(candidate_projects),
        "eligible_after_source_policy": len(eligible),
        "excluded_by_policy": len(policy_excluded),
        "draft_packs_generated": created,
        "skipped": skipped,
        "sent": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
