"""Persistent, lightweight lead tracker for TradingLab03.

Only records and updates lead metadata. It never contacts leads or marks revenue
as verified without an explicit operator-supplied status and evidence.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data" / "leads.json"
STATUSES = {"new", "researching", "qualified", "proposal_draft", "proposal_sent_human",
            "negotiation", "won_pending_payment", "paid_verified", "lost", "do_not_contact"}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_store(path: str | Path = DEFAULT_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        return {"schema_version": 1, "updated_at": _now(), "leads": []}
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("leads"), list):
        raise ValueError("Lead store must contain a leads list")
    return data

def save_store(store: dict, path: str | Path = DEFAULT_PATH) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    store["updated_at"] = _now()
    p.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def add_lead(store: dict, *, business_name: str, service: str, need: str,
             website_url: str = "", source_url: str = "", evidence: str = "",
             contact_name: str = "", notes: str = "") -> dict:
    business_name = " ".join(business_name.split())[:160]
    service = " ".join(service.split())[:120]
    need = " ".join(need.split())[:1000]
    if not business_name or not service or not need:
        raise ValueError("business_name, service, and need are required")
    lead_id = f"TL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{len(store['leads'])+1:03d}"
    lead = {
        "id": lead_id, "business_name": business_name, "service": service, "need": need,
        "website_url": website_url.strip()[:500], "source_url": source_url.strip()[:1000],
        "evidence": evidence.strip()[:1500], "contact_name": contact_name.strip()[:160],
        "notes": notes.strip()[:2000], "status": "new", "status_history": [{"status":"new","at":_now(),"note":"Lead created; verify before outreach."}],
        "created_at": _now(), "updated_at": _now(), "quote_inr": None,
        "revenue_inr": None, "revenue_evidence": "", "contacted": False,
        "next_action": "Verify business, need, source, and lawful contact route."
    }
    store["leads"].append(lead)
    return lead

def update_lead(store: dict, lead_id: str, *, status: str | None = None,
                note: str = "", quote_inr: float | None = None,
                revenue_inr: float | None = None, revenue_evidence: str = "",
                contacted: bool | None = None, next_action: str | None = None) -> dict:
    if status is not None and status not in STATUSES:
        raise ValueError(f"Invalid status: {status}")
    lead = next((x for x in store["leads"] if x.get("id") == lead_id), None)
    if lead is None:
        raise KeyError(f"Lead not found: {lead_id}")
    if status is not None:
        lead["status"] = status
        lead.setdefault("status_history", []).append({"status":status,"at":_now(),"note":note[:1000]})
    if quote_inr is not None:
        if quote_inr < 0: raise ValueError("quote_inr cannot be negative")
        lead["quote_inr"] = round(float(quote_inr), 2)
    if revenue_inr is not None:
        if revenue_inr < 0: raise ValueError("revenue_inr cannot be negative")
        if status != "paid_verified" and lead.get("status") != "paid_verified":
            raise ValueError("Revenue can only be recorded on a paid_verified lead")
        if not revenue_evidence.strip():
            raise ValueError("Provide human-verified revenue evidence")
        lead["revenue_inr"] = round(float(revenue_inr), 2)
        lead["revenue_evidence"] = revenue_evidence.strip()[:1500]
    if contacted is not None:
        if contacted and lead.get("status") == "do_not_contact":
            raise ValueError("This lead is marked do_not_contact")
        lead["contacted"] = bool(contacted)
    if next_action is not None:
        lead["next_action"] = next_action.strip()[:500]
    lead["updated_at"] = _now()
    return lead

def summary(store: dict) -> dict:
    counts = {s: sum(1 for lead in store["leads"] if lead.get("status") == s) for s in sorted(STATUSES)}
    revenue = sum(float(x.get("revenue_inr") or 0) for x in store["leads"] if x.get("status") == "paid_verified")
    return {"total_leads": len(store["leads"]), "by_status": counts,
            "verified_revenue_inr": round(revenue, 2),
            "note": "Only operator-recorded paid_verified entries count; this is not a payment processor."}

def main() -> None:
    p = argparse.ArgumentParser(description="TradingLab03 persistent lead tracker")
    p.add_argument("--store", default=str(DEFAULT_PATH))
    sub = p.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    for name in ("business-name","service","need"):
        add.add_argument("--"+name, required=True)
    for name in ("website-url","source-url","evidence","contact-name","notes"):
        add.add_argument("--"+name, default="")
    upd = sub.add_parser("update")
    upd.add_argument("--id", required=True)
    upd.add_argument("--status", choices=sorted(STATUSES))
    upd.add_argument("--note", default="")
    upd.add_argument("--quote-inr", type=float)
    upd.add_argument("--revenue-inr", type=float)
    upd.add_argument("--revenue-evidence", default="")
    upd.add_argument("--contacted", choices=["yes","no"])
    upd.add_argument("--next-action")
    sub.add_parser("list")
    sub.add_parser("summary")
    args = p.parse_args()
    store = load_store(args.store)
    if args.command == "add":
        lead = add_lead(store, business_name=getattr(args,"business_name"), service=args.service,
            need=args.need, website_url=args.website_url, source_url=args.source_url,
            evidence=args.evidence, contact_name=args.contact_name, notes=args.notes)
        save_store(store,args.store); print(json.dumps(lead,ensure_ascii=False,indent=2))
    elif args.command == "update":
        lead = update_lead(store,args.id,status=args.status,note=args.note,quote_inr=args.quote_inr,
            revenue_inr=args.revenue_inr,revenue_evidence=args.revenue_evidence,
            contacted=None if args.contacted is None else args.contacted=="yes",next_action=args.next_action)
        save_store(store,args.store); print(json.dumps(lead,ensure_ascii=False,indent=2))
    elif args.command == "list":
        print(json.dumps(store["leads"],ensure_ascii=False,indent=2))
    else:
        print(json.dumps(summary(store),ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
