"""Import suitable public opportunity listings into the persistent lead register.

Listings are imported as unverified leads for human review. No outreach, applications,
bids, or payment actions are performed.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .lead_tracker import load_store, save_store, add_lead, summary

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "data" / "opportunities"
DEFAULT_STORE = ROOT / "data" / "leads.json"

def infer_service(title: str, description: str) -> str:
    text = f"{title} {description}".casefold()
    if any(x in text for x in ("video editing", "short-form video", "reels editor", "youtube editor")):
        return "short_video"
    if any(x in text for x in ("seo", "search engine optimization", "content marketing")):
        return "seo_content"
    if any(x in text for x in ("shopify", "e-commerce", "ecommerce", "online store")):
        return "business_website"
    if any(x in text for x in ("landing page", "conversion page")):
        return "landing_page"
    if any(x in text for x in ("automation", "workflow automation", "zapier", "make.com")):
        return "business_automation"
    if any(x in text for x in ("design", "figma", "ui/ux", "graphic")):
        return "design_or_website"
    return "website_or_digital_service"

def import_report(report: dict, store: dict) -> dict:
    existing_urls = {str(x.get("source_url", "")).strip() for x in store["leads"] if x.get("source_url")}
    imported, duplicates, skipped = [], 0, 0
    for item in report.get("opportunities", []):
        url = str(item.get("url", "")).strip()
        title = " ".join(str(item.get("title", "")).split())[:160]
        description = " ".join(str(item.get("description", "")).split())[:1000]
        if not url or not title or not url.startswith("https://"):
            skipped += 1
            continue
        if url in existing_urls:
            duplicates += 1
            continue
        # Import only explicit contract/freelance opportunities. A high keyword
        # score alone is not proof that a listing is a client project.
        if (item.get("risk_flags") or item.get("disqualifiers")
                or item.get("client_fit") is not True
                or item.get("priority") not in {"high", "review"}):
            skipped += 1
            continue
        source_name = str(item.get("source_name", "Public listing"))[:160]
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
        lead["client_fit"] = True
        lead["contract_signals"] = item.get("contract_signals", [])
        lead["disqualifiers"] = item.get("disqualifiers", [])
        lead["next_action"] = "Verify client/project status, country eligibility, payment terms, scope, legitimacy, and platform rules before any proposal."
        existing_urls.add(url)
        imported.append(lead["id"])
    return {"imported_count": len(imported), "imported_ids": imported,
            "duplicates_skipped": duplicates, "low_priority_or_risky_skipped": skipped,
            "total_leads": len(store["leads"]), "ledger_summary": summary(store)}

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
