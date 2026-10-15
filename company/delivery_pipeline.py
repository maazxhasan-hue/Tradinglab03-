"""Human-reviewed end-to-end client pack + website draft pipeline.

This joins existing proposal and website builders into one reproducible run.
It does not contact clients, deploy websites, or record revenue.
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


def run_delivery(*, brief: dict, output_dir: str | Path, lead_store: str | Path = ROOT / "data" / "leads.json") -> dict:
    """Build proposal + static site + combined QA manifest from an explicit brief."""
    required = ("business_name", "tagline", "services", "contact_email", "observed_need")
    missing = [key for key in required if not brief.get(key)]
    if missing:
        raise ValueError("Missing required brief fields: " + ", ".join(missing))
    service = brief.get("service", "business_website")
    if service not in SERVICE_MAP:
        raise ValueError("Unsupported proposal service: " + str(service))
    if not isinstance(brief["services"], list) or not all(isinstance(x, str) and x.strip() for x in brief["services"]):
        raise ValueError("services must be a non-empty list of strings")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    proposal = build_client_pack(
        business_name=str(brief["business_name"]),
        website_url=str(brief.get("website_url", "")),
        service=service,
        observed_need=str(brief["observed_need"]),
        evidence=str(brief.get("evidence", "")),
        price_quote=str(brief.get("price_quote", "")),
        sender_name=str(brief.get("sender_name", "TradingLab03")),
    )
    (out / "proposal.md").write_text(proposal["proposal_markdown"], encoding="utf-8")
    (out / "proposal.json").write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    website_brief = {
        "business_name": str(brief["business_name"]),
        "tagline": str(brief["tagline"]),
        "services": brief["services"],
        "contact_email": str(brief["contact_email"]),
        "primary_color": str(brief.get("primary_color", "#0b7a75")),
    }
    site_report = build_from_brief(website_brief, out / "website")
    required_files = ["proposal.md", "proposal.json", "website/index.html", "website/quality_report.json"]
    missing_files = [name for name in required_files if not (out / name).is_file()]
    checks = {
        "proposal_generated": (out / "proposal.md").is_file(),
        "proposal_requires_human_review": proposal["status"] == "draft_requires_human_review" and not proposal["sent"],
        "website_generated": (out / "website/index.html").is_file(),
        "website_static_quality_gate": bool(site_report.get("passed")),
        "no_automatic_outreach_or_deployment": True,
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_human_review" if all(checks.values()) and not missing_files else "blocked",
        "checks": checks,
        "missing_files": missing_files,
        "proposal_status": proposal["status"],
        "sent": False,
        "production_deployment_enabled": False,
        "verified_revenue": 0,
        "notes": [
            "This pipeline produces drafts only; no client was contacted.",
            "Website static checks do not replace browser, accessibility, security, or client review.",
            "Review proposal scope, evidence, price, timeline, claims, contact permissions, and website content before use.",
        ],
    }
    (out / "delivery_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a proposal and website draft bundle for human review")
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
