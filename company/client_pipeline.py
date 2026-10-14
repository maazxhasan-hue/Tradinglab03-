"""Build a no-cost, human-reviewed client outreach and proposal pack.

This module generates drafts only. It never contacts a prospect, sends a bid,
sets a binding price, or claims unverified work/results.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "client_packs"

SERVICE_PACKS = {
    "business_website": {
        "label": "Business website",
        "deliverables": ["Responsive homepage and up to 4 agreed pages", "Contact CTA and supplied business details", "Basic metadata and semantic headings", "Mobile and link QA checklist"],
        "exclusions": ["Domain/hosting fees", "Paid plugins or stock assets", "Custom backend, payments, or booking integrations unless separately agreed"],
        "questions": ["Who will provide the logo, copy, and images?", "Which pages and contact methods are required?", "Who owns the domain and hosting?"],
    },
    "landing_page": {
        "label": "Landing page",
        "deliverables": ["One responsive landing page", "Clear value proposition and call to action", "Basic metadata and form/contact-path placeholder", "Mobile and link QA checklist"],
        "exclusions": ["Paid ad spend", "CRM integrations or live form processing unless separately agreed", "Domain/hosting fees"],
        "questions": ["What action should visitors take?", "Who is the target customer?", "Are brand assets and approved copy available?"],
    },
    "website_audit": {
        "label": "Website audit",
        "deliverables": ["Review of the agreed public pages", "Prioritized technical and content observations", "Evidence and reproducible checks where possible", "Action list grouped by impact and effort"],
        "exclusions": ["Penetration testing", "Guaranteed ranking or conversion improvements", "Changes to the live website"],
        "questions": ["Which pages matter most?", "Are there specific performance, SEO, or accessibility concerns?", "What access, if any, can be safely provided after approval?"],
    },
    "seo_content": {
        "label": "SEO and content starter",
        "deliverables": ["Keyword/topic hypothesis list for review", "Page-title and meta-description drafts", "Content outline for agreed pages", "On-page review checklist"],
        "exclusions": ["Guaranteed search rankings", "Paid tools or link purchases", "Publishing without client approval"],
        "questions": ["Which locations or audiences do you serve?", "Which services/products are priorities?", "Are analytics or search-console reports available?"],
    },
    "short_video": {
        "label": "Short-form video package",
        "deliverables": ["Agreed number of short-video concepts", "Hooks, scripts, captions, and shot/edit notes", "Platform-specific format checklist", "One consolidated revision round if agreed"],
        "exclusions": ["Filming, licensed music, paid stock, or posting unless agreed", "Guaranteed views or follower growth"],
        "questions": ["Which platform and audience are targeted?", "Will the client supply footage and brand assets?", "How many videos and what duration are needed?"],
    },
    "business_automation": {
        "label": "Business workflow automation",
        "deliverables": ["Current-process discovery checklist", "Proposed workflow map", "Small scoped automation plan", "Test and handover checklist"],
        "exclusions": ["Production access before approval", "Paid third-party services", "Handling sensitive customer data without a reviewed plan"],
        "questions": ["Which repetitive task is being improved?", "Which apps are involved?", "What data and permissions are strictly necessary?"],
    },
}

def _clean(value: str, limit: int = 1200) -> str:
    return " ".join((value or "").split())[:limit]

def build_client_pack(*, business_name: str, website_url: str, service: str,
                      observed_need: str, evidence: str = "", price_quote: str = "",
                      sender_name: str = "TradingLab03") -> dict:
    if service not in SERVICE_PACKS:
        raise ValueError(f"Unsupported service: {service}")
    business_name = _clean(business_name, 120)
    website_url = _clean(website_url, 300)
    observed_need = _clean(observed_need, 700)
    evidence = _clean(evidence, 1000)
    price_quote = _clean(price_quote, 120)
    sender_name = _clean(sender_name, 120) or "TradingLab03"
    if not business_name or not observed_need:
        raise ValueError("business_name and observed_need are required")
    pack = SERVICE_PACKS[service]
    evidence_line = f"Evidence to verify: {evidence}" if evidence else "Evidence: not supplied; verify the need before contacting."
    price_line = f"Indicative quote supplied by operator: {price_quote} (confirm scope, currency, taxes, and terms before sharing)." if price_quote else "Price: not set. Confirm scope and effort before issuing a quote."
    outreach = (
        f"Subject: A possible {pack['label'].lower()} improvement for {business_name}\n\n"
        f"Hello {business_name} team,\n\n"
        f"I'm preparing a small, tailored service proposal from {sender_name}. "
        f"The potential area to explore is: {observed_need}. "
        f"{evidence_line} This is an initial observation, not a claim that your current setup is failing.\n\n"
        f"If this is relevant, would you be open to a brief conversation about your priorities? "
        f"I can share a clear scope for your review. No obligation.\n\n"
        f"Regards,\n{sender_name}"
    )
    proposal = [
        f"# Draft proposal — {pack['label']}",
        "",
        f"**Client:** {business_name}",
        f"**Website:** {website_url or 'Not provided'}",
        f"**Prepared by:** {sender_name}",
        f"**Status:** Draft for human review — not sent or accepted",
        "",
        "## Context to verify",
        observed_need,
        "",
        evidence_line,
        "",
        "## Proposed deliverables",
        *[f"- {item}" for item in pack["deliverables"]],
        "",
        "## Exclusions / dependencies",
        *[f"- {item}" for item in pack["exclusions"]],
        "",
        "## Questions before final scope",
        *[f"- {item}" for item in pack["questions"]],
        "",
        "## Commercial terms",
        price_line,
        "Timeline: confirm after the client approves the scope and supplies required materials.",
        "Payment milestones, revisions, ownership, cancellation, taxes, and acceptance criteria: agree in writing before work begins.",
        "",
        "## Acceptance checklist",
        "- Human verifies the prospect, need, evidence, and contact channel.",
        "- Human reviews and edits the message and proposal.",
        "- Client approves scope, price, timeline, and terms in writing.",
        "- No deployment, account access, or paid purchase until separately approved.",
        "",
        "## Outreach draft (not sent)",
        "",
        outreach,
        "",
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "business_name": business_name,
        "website_url": website_url,
        "service": service,
        "service_label": pack["label"],
        "observed_need": observed_need,
        "evidence": evidence,
        "price_quote": price_quote,
        "outreach_draft": outreach,
        "proposal_markdown": "\n".join(proposal),
        "status": "draft_requires_human_review",
        "sent": False,
    }

def build_pack_from_lead(lead_id: str, *, store_path: str | Path = ROOT / "data" / "leads.json",
                         price_quote: str = "", sender_name: str = "TradingLab03") -> dict:
    """Build a draft from a saved lead only when it is explicitly a client project."""
    store = json.loads(Path(store_path).read_text(encoding="utf-8"))
    leads = store.get("leads") if isinstance(store, dict) else None
    if not isinstance(leads, list):
        raise ValueError("Lead store must contain a leads list")
    lead = next((x for x in leads if isinstance(x, dict) and str(x.get("id", "")) == lead_id), None)
    if lead is None:
        raise ValueError(f"Lead ID not found: {lead_id}")
    if lead.get("opportunity_type") != "client_project" and lead.get("client_fit") is not True:
        raise ValueError("This listing is not classified as a potential client project; no pack generated.")
    service_map = {
        "business_website": "business_website", "landing_page": "landing_page",
        "website_audit": "website_audit", "seo_content": "seo_content",
        "short_video": "short_video", "business_automation": "business_automation",
        "design_or_website": "business_website", "website_or_digital_service": "business_website",
    }
    source_service = str(lead.get("service", ""))
    service = service_map.get(source_service)
    if not service:
        raise ValueError(f"Lead service needs human mapping before proposal: {source_service}")
    website = str(lead.get("website_url", "")).strip()
    if not website.startswith("https://"):
        website = ""
    evidence = str(lead.get("evidence", "")).strip()
    evidence = (evidence + " " if evidence else "") + "Original listing: " + str(lead.get("source_url", "not supplied"))
    return build_client_pack(
        business_name=str(lead.get("business_name", "")),
        website_url=website,
        service=service,
        observed_need=str(lead.get("need", "")),
        evidence=evidence,
        price_quote=price_quote,
        sender_name=sender_name,
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a free client outreach and proposal draft.")
    parser.add_argument("--lead-id", default=os.getenv("CLIENT_LEAD_ID", ""), help="Optional saved lead ID; must be a potential client project")
    parser.add_argument("--lead-store", default=str(ROOT / "data" / "leads.json"))
    parser.add_argument("--business", default=os.getenv("CLIENT_BUSINESS", ""))
    parser.add_argument("--website", default=os.getenv("CLIENT_WEBSITE", ""))
    parser.add_argument("--service", default=os.getenv("CLIENT_SERVICE", "business_website"))
    parser.add_argument("--need", default=os.getenv("CLIENT_NEED", ""))
    parser.add_argument("--evidence", default=os.getenv("CLIENT_EVIDENCE", ""))
    parser.add_argument("--price", default=os.getenv("CLIENT_PRICE", ""))
    parser.add_argument("--sender", default=os.getenv("CLIENT_SENDER", "TradingLab03"))
    parser.add_argument("--output", default=str(OUT_DIR))
    args = parser.parse_args()
    if args.lead_id:
        pack = build_pack_from_lead(args.lead_id, store_path=args.lead_store,
                                    price_quote=args.price, sender_name=args.sender)
    else:
        pack = build_client_pack(business_name=args.business, website_url=args.website,
                                 service=args.service, observed_need=args.need,
                                 evidence=args.evidence, price_quote=args.price,
                                 sender_name=args.sender)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"client-pack-{stamp}"
    (out / f"{stem}.md").write_text(pack["proposal_markdown"], encoding="utf-8")
    (out / f"{stem}.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": pack["status"], "sent": False, "markdown": str(out / f"{stem}.md"),
                      "json": str(out / f"{stem}.json")}, ensure_ascii=False))

if __name__ == "__main__":
    main()
