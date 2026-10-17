"""Import suitable public opportunity listings into the persistent lead register.

Listings are imported as unverified leads for human review. No outreach, applications,
bids, or payment actions are performed.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .lead_tracker import load_store, save_store, add_lead, summary
from .opportunity_scout import score_listing

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "data" / "opportunities"
DEFAULT_STORE = ROOT / "data" / "leads.json"
SOURCE_CONFIG = ROOT / "config" / "opportunity_sources.json"

def enabled_source_names(config_path: str | Path = SOURCE_CONFIG) -> set[str]:
    """Return sources allowed for lead import, excluding research-only feeds."""
    try:
        sources = json.loads(Path(config_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(sources, list):
        return set()
    return {
        str(source.get("name", "")).strip()
        for source in sources
        if isinstance(source, dict)
        and source.get("enabled", True)
        and str(source.get("action_policy", "review_allowed")).strip() == "review_allowed"
        and str(source.get("name", "")).strip()
    }

def infer_service(title: str, description: str) -> str:
    text = f"{title} {description}".casefold()
    if any(x in text for x in ("video editing", "short-form video", "reels editor", "youtube editor", "montage vidéo", "montage video")):
        return "short_video"
    if any(x in text for x in ("seo", "search engine optimization", "content marketing", "référencement", "reseaux sociaux", "réseaux sociaux", "gestion des réseaux sociaux")):
        return "seo_content"
    if any(x in text for x in ("shopify", "e-commerce", "ecommerce", "online store", "boutique en ligne")):
        return "business_website"
    if any(x in text for x in ("landing page", "conversion page")):
        return "landing_page"
    if any(x in text for x in ("automation", "workflow automation", "zapier", "make.com")):
        return "business_automation"
    if any(x in text for x in ("design", "figma", "ui/ux", "graphic", "graphisme", "identité visuelle")):
        return "design_or_website"
    if any(x in text for x in ("site internet", "site web", "création de site", "refonte de site", "développement web")):
        return "website_or_digital_service"
    return "website_or_digital_service"

def import_report(report: dict, store: dict, allowed_sources: set[str] | None = None) -> dict:
    if allowed_sources is None:
        allowed_sources = enabled_source_names()
    existing_urls = {str(x.get("source_url", "")).strip() for x in store["leads"] if x.get("source_url")}
    imported, duplicates, skipped = [], 0, 0
    for item in report.get("opportunities", []):
        url = str(item.get("url", "")).strip()
        title = " ".join(str(item.get("title", "")).split())[:160]
        description = " ".join(str(item.get("description", "")).split())[:1000]
        source_name = str(item.get("source_name", "")).strip()
        if not url or not title or not url.startswith("https://"):
            skipped += 1
            continue
        # Reports can outlive config changes. Never import a listing from a feed
        # that has since been disabled (e.g. rate-limited or irrelevant job boards).
        if not source_name or source_name not in allowed_sources:
            skipped += 1
            continue
        if url in existing_urls:
            duplicates += 1
            continue
        # Keep direct buyer projects and freelance work in separate types. A
        # freelance role can be a paid-work opportunity without being a client lead.
        eligible = item.get("client_fit") is True or item.get("freelance_work_fit") is True
        if (item.get("risk_flags") or item.get("location_restrictions")
                or not eligible or item.get("priority") not in {"high", "review"}):
            skipped += 1
            continue
        source_name = source_name[:160]
        score = item.get("score", 0)
        service = infer_service(title, description)
        evidence = f"Public listing title: {title}. Source: {source_name}. Match score: {score}. Payment/contract status is unverified."
        lead = add_lead(
            store,
            business_name=title,
            service=service,
            need=description or title,
            source_url=url,
            evidence=evidence,
            notes=("Auto-imported from public opportunity scout. This is a job/project listing, "
                   "not a verified client. Confirm freelance eligibility, payment, legitimacy, "
                   "scope, deadlines, and platform rules before acting. "
                   f"Scout priority={item.get('priority')}; score={score}; listing_id={item.get('id','')}.")
        )
        lead["source_type"] = "public_opportunity_listing"
        lead["source_name"] = source_name
        lead["opportunity_score"] = score
        lead["opportunity_priority"] = item.get("priority", "review")
        lead["paid_contract_verified"] = False
        lead["client_fit"] = item.get("client_fit") is True
        lead["freelance_work_fit"] = item.get("freelance_work_fit") is True
        lead["opportunity_type"] = item.get("opportunity_type", "client_project" if item.get("client_fit") else "freelance_work")
        lead["contract_signals"] = item.get("contract_signals", [])
        lead["project_signals"] = item.get("project_signals", [])
        lead["disqualifiers"] = item.get("disqualifiers", [])
        if lead["opportunity_type"] == "client_project":
            lead["next_action"] = "Verify buyer intent, scope, payment terms, legitimacy, and platform rules before any proposal."
        else:
            lead["next_action"] = "Review the freelance work listing; verify country eligibility, actual pay/rates, scope, legitimacy, and application rules. This is not a direct client lead."
        existing_urls.add(url)
        imported.append(lead["id"])
    # Reclassify legacy auto-imported listings using the current buyer-intent rules.
    # Do not delete records or change their workflow status; simply remove false
    # client-lead claims and make the next action explicit for human review.
    reclassified = 0
    for lead in store["leads"]:
        if lead.get("source_type") != "public_opportunity_listing":
            continue
        result = score_listing(
            str(lead.get("business_name", "")),
            str(lead.get("need", "")),
            str(lead.get("source_name", "")),
        )
        old_type = lead.get("opportunity_type")
        new_type = result.get("opportunity_type", "unqualified")
        lead["client_fit"] = bool(result.get("client_fit"))
        lead["freelance_work_fit"] = bool(result.get("freelance_work_fit"))
        lead["opportunity_type"] = new_type
        lead["opportunity_score"] = result.get("score", 0)
        lead["opportunity_priority"] = result.get("priority", "low")
        lead["project_signals"] = result.get("project_signals", [])
        lead["disqualifiers"] = result.get("disqualifiers", [])
        if old_type != new_type:
            reclassified += 1
        if new_type == "client_project":
            lead["next_action"] = "Verify buyer intent, scope, payment terms, legitimacy, and platform rules before any proposal."
        elif new_type == "freelance_work":
            lead["next_action"] = "Review as a possible freelance-work listing, not a direct client lead; verify pay, eligibility, scope, and rules."
        else:
            lead["next_action"] = "Do not treat as an actionable client lead: buyer intent is not established or job-vacancy signals were detected. Keep for reference only."
        lead["notes"] = (str(lead.get("notes", "")) + " Rechecked by current opportunity classifier; classification and payment remain unverified.").strip()[:2000]
    types = {}
    for lead in store["leads"]:
        kind = lead.get("opportunity_type", "legacy_or_unclassified")
        types[kind] = types.get(kind, 0) + 1
    return {"imported_count": len(imported), "imported_ids": imported,
            "reclassified_existing_listings": reclassified,
            "duplicates_skipped": duplicates, "low_priority_or_risky_skipped": skipped,
            "total_leads": len(store["leads"]), "opportunity_type_counts": types,
            "ledger_summary": summary(store)}

def latest_report(report_dir: str | Path = DEFAULT_REPORT_DIR) -> Path:
    paths = sorted(Path(report_dir).glob("opportunities-*.json"), key=lambda p: p.stat().st_mtime)
    if not paths:
        raise FileNotFoundError(f"No opportunity JSON reports found in {report_dir}")
    return paths[-1]

def main() -> None:
    parser = argparse.ArgumentParser(description="Import suitable public opportunity listings into lead tracker")
    parser.add_argument("--report", help="Explicit opportunity report JSON path")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--store", default=str(DEFAULT_STORE))
    args = parser.parse_args()
    report_path = Path(args.report) if args.report else latest_report(args.report_dir)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    store = load_store(args.store)
    result = import_report(report, store)
    save_store(store, args.store)
    result["report_path"] = str(report_path)
    result["store_path"] = str(args.store)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
