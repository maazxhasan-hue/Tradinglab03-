"""Autonomy-first client execution coordinator.

Decomposes briefs, runs the existing delivery pipeline, creates service-specific
drafts, and records requirement-level evidence. External actions remain disabled.
"""
from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .delivery_pipeline import run_delivery, SERVICE_MAP

ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROLES = {
    "business_website": ["Project Manager", "Website Builder", "UX/UI Designer", "QA Tester", "Delivery Coordinator"],
    "landing_page": ["Project Manager", "UX/UI Designer", "Copywriter", "Frontend Developer", "QA Tester"],
    "website_audit": ["Website Auditor", "SEO Specialist", "Accessibility Auditor", "QA Tester"],
    "seo_content": ["SEO Specialist", "Content Marketing Agent", "Copywriter", "QA Tester"],
    "short_video": ["Creative Director", "Video Editor", "Copywriter", "Social Media Manager"],
    "business_automation": ["Automation Developer", "Integration Engineer", "Security Reviewer", "QA Tester"],
}

def _items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.replace(";", "\n").splitlines() if x.strip()]
    return []

def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")

def _service_artifact(service: str, brief: dict, out: Path) -> list[str]:
    name = str(brief["business_name"])
    need = str(brief.get("observed_need", "Business goal to confirm"))
    audience = str(brief.get("target_audience", "Audience to confirm"))
    services = ", ".join(_items(brief.get("services"))) or "Not supplied"
    if service == "website_audit":
        filename = "website_audit_plan.md"
        body = f"""# Website Audit Plan — Not an Audit Result

Client: {name}
URL: {brief.get('website_url') or 'Not supplied'}
Goal: {need}

## Execution checklist
- [ ] Verify URL and pages in the agreed scope.
- [ ] Test navigation, links, forms, and responsive layouts.
- [ ] Measure performance and retain reproducible evidence.
- [ ] Review titles, descriptions, headings, content relevance, and indexability.
- [ ] Review keyboard access, labels, focus, contrast, and image alt text.
- [ ] Review security and data collection only within authorized scope.
- [ ] Prioritize findings by impact, confidence, evidence, and effort.

Status: this is a prepared plan. No live site was crawled or tested by this local workflow.
"""
    elif service == "seo_content":
        filename = "seo_content_draft.md"
        body = f"""# SEO Content Draft — Review Required

Client: {name}
Audience: {audience}
Goal: {need}
Services: {services}

## Search-intent hypotheses
1. People seeking the core service and its practical benefits.
2. People comparing providers, process, cost, or suitability.
3. People seeking verified trust signals, service area, or next steps.

## Suggested page structure
- Accurate H1 and concise introduction for the intended audience.
- One section per approved service, based on verified facts.
- Process, genuine differentiators, and FAQs grounded in client answers.
- Clear call to action using approved contact details.

## Before publishing
- [ ] Validate search demand and geography with evidence.
- [ ] Verify claims with the client.
- [ ] Check metadata, internal links, schema eligibility, and indexability.
- [ ] Never promise rankings or fabricate search-volume figures.
"""
    elif service == "short_video":
        filename = "short_video_package.md"
        body = f"""# Short-Form Video Package — Draft

Client: {name}
Audience: {audience}
Goal: {need}

## Concept 1 — Problem and solution
Hook: “Still struggling with [verified customer problem]?”
Beats: show the problem; explain the approved service; demonstrate a real benefit; finish with a clear call to action.
Production: vertical 9:16, captions, readable safe areas, clear audio, quick cuts.
Caption draft: A practical look at how {name} helps with {need}. Verify all claims before posting.

## Concept 2 — Three useful tips
Hook: “Three things to check before choosing [service].”
Beats: three genuinely useful points; one common mistake; invite a relevant question.
Production: use owned/licensed footage and review the thumbnail and captions.

## Before publishing
- [ ] Replace bracketed text with verified facts.
- [ ] Confirm rights to footage, music, fonts, and logos.
- [ ] Confirm platform, duration, CTA, and approval.
- [ ] Views and growth are not guaranteed.
"""
    elif service == "business_automation":
        filename = "automation_design.md"
        body = f"""# Business Automation Design — Draft

Client: {name}
Goal: {need}
Systems and data: {brief.get('integrations_and_data') or 'Not supplied'}

## Execution plan
1. Map the trigger, steps, owner, exception paths, and expected result.
2. Verify API/connector support and system ownership.
3. Minimize data collection and define access and retention.
4. Build in a test environment with least-privilege credentials.
5. Test success, duplicates, retries, rate limits, invalid data, and recovery.
6. Add monitoring, manual fallback, ownership, and handover notes.

No external integration was connected by this generator. Verify APIs, credentials, permissions, and acceptance examples before execution.
"""
    else:
        filename = "website_implementation_notes.md"
        body = f"""# Website Implementation Notes — Draft

Client: {name}
Goal: {need}
Pages: {", ".join(_items(brief.get("pages_screens_deliverables")) or ["Home", "Services", "Contact"])}
Required features: {", ".join(_items(brief.get("version_1_must_have_features")) or ["Confirm with client"])}

The current builder creates static page scaffolding. Custom backend logic, real forms, authentication, payments, booking, and third-party integrations require implementation and functional testing before they can be marked complete.
"""
    _write(out / filename, body)
    return [filename]

def execute_client_project(*, brief: dict, output_dir: str | Path) -> dict:
    service = str(brief.get("service", "business_website")).strip()
    if service not in SERVICE_ROLES:
        raise ValueError("Unsupported service: " + service)
    if not str(brief.get("business_name", "")).strip():
        raise ValueError("business_name is required")
    if not _items(brief.get("services")):
        raise ValueError("services must be a non-empty list")
    if not brief.get("lead_id") and not str(brief.get("observed_need", "")).strip():
        raise ValueError("observed_need is required unless lead_id is supplied")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    delivery = run_delivery(brief=brief, output_dir=out / "delivery_bundle")
    artifacts = _service_artifact(service, brief, out)
    website_dir = out / "delivery_bundle" / "website"
    requirements: list[dict[str, Any]] = []
    pages = _items(brief.get("pages_screens_deliverables")) or ["Home", "Services", "Contact"]
    for i, page in enumerate(pages, 1):
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in page).strip("-")
        filename = "index.html" if slug in {"home", "homepage", "home-page"} else f"{slug}.html"
        exists = (website_dir / filename).is_file()
        requirements.append({
            "requirement_id": f"PAGE-{i:03d}", "requirement": f"Page: {page}",
            "owner_role": "Website Builder",
            "status": "draft_generated" if exists else "blocked",
            "verification": "file_exists" if exists else "missing_generated_file",
            "evidence": str((website_dir / filename).relative_to(out)) if exists else "",
        })
    for i, feature in enumerate(_items(brief.get("version_1_must_have_features")), 1):
        requirements.append({
            "requirement_id": f"FEAT-{i:03d}", "requirement": feature,
            "owner_role": "Frontend Developer / Integration Engineer",
            "status": "needs_implementation_and_acceptance_test",
            "verification": "not_claimed_by_static_scaffold",
            "evidence": "delivery_bundle/website/quality_report.json",
        })

    plan = [
        "# Autonomous Execution Plan", "",
        f"Client: {brief['business_name']}",
        f"Service: {service}",
        f"Started: {datetime.now(timezone.utc).isoformat()}",
        "Mode: local supported steps only; no external side effects.", "",
        "## Specialist sequence",
        *[f"{i}. {role}: complete assigned work, attach evidence, and pass blockers forward."
          for i, role in enumerate(SERVICE_ROLES[service], 1)],
        "", "## Executed automatically",
        "- Validated brief and generated proposal, scope, acceptance, change-request, and handover artifacts.",
        "- Generated static website draft and its static quality report.",
        *[f"- Generated service artifact: {x}" for x in artifacts],
        "- Recorded requirement-level traceability.",
        "", "## Not claimed complete",
        "- Custom features without implementation and acceptance tests.",
        "- Live audit/integration work not actually performed by this local run.",
        "- Client acceptance, commercial agreement, outreach, and production release.",
    ]
    _write(out / "agent_task_plan.md", "\n".join(plan))
    with (out / "requirement_traceability.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement_id", "requirement", "owner_role", "status", "verification", "evidence"])
        writer.writeheader()
        writer.writerows(requirements)

    report = {
        "client": brief["business_name"], "service": service,
        "status": "completed_with_limitations",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "roles_assigned": SERVICE_ROLES[service],
        "delivery_bundle_status": delivery.get("status"),
        "delivery_checks": delivery.get("checks", {}),
        "service_artifacts": artifacts, "requirements": requirements,
        "counts": {
            "requirements_tracked": len(requirements),
            "draft_generated": sum(x["status"] == "draft_generated" for x in requirements),
            "needs_implementation_and_acceptance_test": sum(x["status"] == "needs_implementation_and_acceptance_test" for x in requirements),
            "blocked": sum(x["status"] == "blocked" for x in requirements),
        },
        "external_actions_performed": [],
        "production_deployment_enabled": False, "sent": False, "verified_revenue": 0,
        "limitations": [
            "Specialist roles are represented as an execution plan, not independent model agents.",
            "Static website generation does not implement arbitrary interactive features or backend integrations.",
            "Audit output is a plan, not a claim that a live site was crawled.",
            "SEO and video outputs are drafts requiring fact-checking and approval.",
            "No external messages, bids, purchases, payments, or production deployments were performed.",
        ],
    }
    _write(out / "agent_execution_report.json", json.dumps(report, ensure_ascii=False, indent=2))
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description="Execute supported client delivery steps autonomously")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--output", default=str(ROOT / "data" / "client_executions" / "latest"))
    args = parser.parse_args(argv)
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    report = execute_client_project(brief=brief, output_dir=args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
