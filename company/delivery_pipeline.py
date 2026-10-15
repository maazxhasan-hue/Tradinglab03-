"""Human-reviewed end-to-end client pack + project-specific website draft pipeline.

This pipeline creates drafts only. It never contacts clients, deploys websites,
records revenue, or treats static checks as proof of feature completion.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

from .client_pipeline import build_client_pack, build_pack_from_lead
from .website_pipeline import build_from_brief

ROOT = Path(__file__).resolve().parents[1]
SERVICE_MAP = {
    "business_website": "business_website",
    "landing_page": "landing_page",
    "website_audit": "website_audit",
    "seo_content": "seo_content",
    "short_video": "short_video",
    "business_automation": "business_automation",
}


def _text_items(value) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.replace(";", "\\n").splitlines() if x.strip()]
    return []


def run_delivery(*, brief: dict, output_dir: str | Path, lead_store: str | Path = ROOT / "data" / "leads.json") -> dict:
    """Build proposal + pages from requirements + scope docs + truthful QA manifest."""
    required = ("business_name", "tagline", "services", "contact_email")
    missing = [key for key in required if not brief.get(key)]
    if not brief.get("lead_id") and not brief.get("observed_need"):
        missing.append("observed_need (or a saved client-project lead_id)")
    if missing:
        raise ValueError("Missing required brief fields: " + ", ".join(missing))
    service = brief.get("service", "business_website")
    if service not in SERVICE_MAP:
        raise ValueError("Unsupported proposal service: " + str(service))
    if not isinstance(brief["services"], list) or not all(isinstance(x, str) and x.strip() for x in brief["services"]):
        raise ValueError("services must be a non-empty list of strings")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    def field(label: str, key: str) -> str:
        value = brief.get(key, "")
        if isinstance(value, list):
            value = "\\n".join(f"- {item}" for item in value if str(item).strip())
        value = str(value).strip()
        return f"## {label}\\n\\n{value if value else '_Not supplied — confirm with the client before build._'}\\n"

    scope_sections = [
        "# Client Project Brief — Draft for Written Confirmation", "",
        f"- Client: {brief['business_name']}",
        f"- Project type: {service}",
        f"- Scope version: {brief.get('scope_version', 1)}",
        f"- Status: {brief.get('approval_status', 'not_approved')}",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}", "",
        "> Do not start production work until the client and owner approve scope, price, timeline, dependencies, and acceptance criteria in writing.", "",
        field("Business goal / problem", "observed_need"),
        field("Target audience", "target_audience"),
        field("Version 1 pages / screens / deliverables", "pages_screens_deliverables"),
        field("Version 1 required features", "version_1_must_have_features"),
        field("Design direction and references", "design_direction_and_references"),
        field("Content and assets", "content_and_assets"),
        field("Integrations and data", "integrations_and_data"),
        field("Constraints, dependencies, exclusions", "constraints_dependencies_exclusions"),
        field("Budget range", "budget_range"),
        field("Target deadline / milestones", "target_deadline"),
        field("Post-launch support requested", "post_launch_support"),
        field("Acceptance criteria", "acceptance_criteria"),
        field("Future feature backlog (not included in v1 unless separately approved)", "future_features_backlog"),
        "## Commercial agreement", "",
        f"- Quote supplied to pipeline: {brief.get('price_quote') or 'Not set'}",
        "- Payment milestones, tax, revisions, ownership, cancellation, delivery date, and support boundary: confirm and agree in writing.",
        "- Client approval recorded: not recorded by this generator.", "",
    ]
    (out / "project_brief.md").write_text("\\n".join(scope_sections), encoding="utf-8")

    future = brief.get("future_features_backlog", "")
    future_items = _text_items(future)
    future_doc = [
        "# Future Feature Backlog", "",
        "This list is for discovery and prioritization only. These items are not included in version 1 unless the signed scope explicitly includes them.", "",
        ("\\n".join(f"- {item}" for item in future_items) if future_items else "_No future features supplied yet. Ask the client what they may need later, but do not invent commitments._"), "",
        "## Prioritization for review",
        "- Value to the user's business", "- Effort and ongoing maintenance",
        "- Security, privacy, accessibility, and integration risks", "- Dependencies and data ownership",
        "- Budget and timeline impact", "- Proposed release/version and acceptance criteria", "",
        "Any accepted future item requires a written change request and updated scope/version.",
    ]
    (out / "future_features_backlog.md").write_text("\\n".join(future_doc) + "\\n", encoding="utf-8")
    acceptance = [
        "# Acceptance Checklist — Complete with Client", "",
        "Replace each example with a concrete, agreed pass/fail criterion. Do not treat a blank checkbox as passed.", "",
        "- [ ] Client-approved scope version and deliverables are recorded.",
        "- [ ] Every version 1 feature has an expected behavior and test case.",
        "- [ ] Responsive/mobile layout checked at agreed viewports.",
        "- [ ] Keyboard navigation and visible focus reviewed.",
        "- [ ] Links, contact actions, and forms/integrations tested.",
        "- [ ] Empty, error, and loading states checked where relevant.",
        "- [ ] Copy, spelling, metadata, and client-approved assets reviewed.",
        "- [ ] Browser/device coverage agreed and tested.",
        "- [ ] Privacy/security checks completed for data and integrations.",
        "- [ ] Accessibility checks appropriate to project risk completed.",
        "- [ ] Known limitations and excluded features documented.",
        "- [ ] Client reviewed preview and acceptance recorded in writing.",
        "- [ ] Owner approved release; deployment is separately authorized.", "",
        "Automated static checks are not a substitute for browser testing, independent QA, or client acceptance.",
    ]
    (out / "acceptance_checklist.md").write_text("\\n".join(acceptance) + "\\n", encoding="utf-8")
    change = [
        "# Client Change Request", "", "- Client / project:", "- Current scope version:",
        "- Requested change:", "- Business reason / expected outcome:", "- User story / expected behavior:",
        "- Acceptance criteria:", "- Price impact (owner-approved):", "- Timeline impact:",
        "- Dependencies / risks:", "- Future version or current scope:", "- Client decision and date:",
        "- Owner approval and date:", "",
        "Do not implement a scope-changing request until price, timeline, and acceptance criteria are agreed in writing.",
    ]
    (out / "change_request_template.md").write_text("\\n".join(change) + "\\n", encoding="utf-8")
    handover = [
        "# Client Handover & Next-Step Plan", "", "- Delivered items:", "- Acceptance checks passed:",
        "- Known limitations / exclusions:", "- Source files and ownership transfer:",
        "- Deployment / backup / rollback notes:", "- Access transfer method (never paste secrets in this document):",
        "- Support window and exclusions:", "- Client acceptance recorded:",
        "- Optional next priorities (not commitments):", "- Follow-up permission / preferred channel:", "",
        "Offer maintenance or future features only if relevant and wanted. Do not send unsolicited follow-ups or imply a subscription has been started.",
    ]
    (out / "handover_and_next_steps.md").write_text("\\n".join(handover) + "\\n", encoding="utf-8")

    if brief.get("lead_id"):
        proposal = build_pack_from_lead(str(brief["lead_id"]), store_path=lead_store,
                                        price_quote=str(brief.get("price_quote", "")),
                                        sender_name=str(brief.get("sender_name", "TradingLab03")))
        if proposal["service"] != service:
            raise ValueError("Selected service must match the saved lead service mapping: " + proposal["service"])
        if str(brief["business_name"]).strip() != proposal["business_name"]:
            raise ValueError("business_name must match the saved lead when lead_id is used")
    else:
        proposal = build_client_pack(
            business_name=str(brief["business_name"]), website_url=str(brief.get("website_url", "")),
            service=service, observed_need=str(brief["observed_need"]), evidence=str(brief.get("evidence", "")),
            price_quote=str(brief.get("price_quote", "")), sender_name=str(brief.get("sender_name", "TradingLab03")),
        )
    (out / "proposal.md").write_text(proposal["proposal_markdown"], encoding="utf-8")
    (out / "proposal.json").write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")

    website_brief = {
        "business_name": str(brief["business_name"]), "tagline": str(brief["tagline"]),
        "services": brief["services"], "contact_email": str(brief["contact_email"]),
        "primary_color": str(brief.get("primary_color", "#0b7a75")),
        "pages_screens_deliverables": brief.get("pages_screens_deliverables", ""),
        "version_1_must_have_features": brief.get("version_1_must_have_features", ""),
        "observed_need": str(brief.get("observed_need", "")),
        "target_audience": str(brief.get("target_audience", "")),
        "design_direction_and_references": str(brief.get("design_direction_and_references", "")),
        "content_and_assets": str(brief.get("content_and_assets", "")),
        "integrations_and_data": str(brief.get("integrations_and_data", "")),
    }
    site_report = build_from_brief(website_brief, out / "website")
    required_files = [
        "proposal.md", "proposal.json", "project_brief.md", "future_features_backlog.md",
        "acceptance_checklist.md", "change_request_template.md", "handover_and_next_steps.md",
        "website/index.html", "website/quality_report.json",
    ]
    missing_files = [name for name in required_files if not (out / name).is_file()]

    # Scope readiness is deliberately separate from draft-generation success.
    # Missing client details can be reviewed, but never silently count as approved.
    scope_required = {
        "business_goal": bool(str(brief.get("observed_need", "")).strip()),
        "pages_or_deliverables": bool(_text_items(brief.get("pages_screens_deliverables"))),
        "version_1_features": bool(_text_items(brief.get("version_1_must_have_features"))),
        "acceptance_criteria": bool(str(brief.get("acceptance_criteria", "")).strip()),
        "target_audience": bool(str(brief.get("target_audience", "")).strip()),
        "approved_contact_email": bool(str(brief.get("contact_email", "")).strip()),
        "budget_range": bool(str(brief.get("budget_range", "")).strip()),
        "target_deadline": bool(str(brief.get("target_deadline", "")).strip()),
    }
    scope_missing = [name for name, present in scope_required.items() if not present]
    checks = {
        "proposal_generated": (out / "proposal.md").is_file(),
        "proposal_requires_human_review": proposal["status"] == "draft_requires_human_review" and not proposal["sent"],
        "website_generated": (out / "website/index.html").is_file(),
        "website_static_quality_gate": bool(site_report.get("passed")),
        "client_scope_documents_generated": all((out / name).is_file() for name in [
            "project_brief.md", "future_features_backlog.md", "acceptance_checklist.md",
            "change_request_template.md", "handover_and_next_steps.md",
        ]),
        "no_automatic_outreach_or_deployment": True,
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_human_review" if all(checks.values()) and not missing_files else "blocked",
        "checks": checks,
        "missing_files": missing_files,
        "scope_readiness": "complete_for_owner_review" if not scope_missing else "incomplete",
        "scope_missing_fields": scope_missing,
        "production_release_status": "blocked_pending_written_approval" if scope_missing else "blocked_pending_written_approval_and_functional_qa",
        "functional_feature_implementation_verified": False,
        "proposal_status": proposal["status"],
        "sent": False,
        "production_deployment_enabled": False,
        "verified_revenue": 0,
        "notes": [
            "This pipeline produces drafts only; no client was contacted.",
            "Requested pages and feature descriptions are included in generated draft scaffolding; this does not prove complex features are implemented.",
            "Forms, authentication, payments, booking, backend behavior, and integrations require separate implementation and functional tests.",
            "Review proposal scope, evidence, price, timeline, claims, contact permissions, and website content before use.",
            "Confirm project brief, budget, deadline, features, and acceptance criteria with the client in writing before production work.",
            "Future backlog items are not part of version 1 unless approved in writing.",
            "Use the acceptance checklist, change request, and handover documents to control QA, scope changes, and repeat support.",
        ],
    }
    (out / "delivery_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a proposal and project-specific website draft bundle for human review")
    parser.add_argument("--brief", required=True, help="JSON file with approved business details and observed need")
    parser.add_argument("--output", default=str(ROOT / "data" / "delivery_bundles" / "latest"))
    args = parser.parse_args(argv)
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    report = run_delivery(brief=brief, output_dir=args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "ready_for_human_review":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
