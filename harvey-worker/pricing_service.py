"""Persistent pricing catalog, publication snapshots, and audit history for Nexora HQ.

Prices are stored as integer paise to avoid floating-point rounding. Editing a
published record updates its draft data only; the customer-facing snapshot changes
only after the owner explicitly publishes it.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from app import db, now

CATEGORIES = {"service", "subscription", "client_quote"}
BILLING_PERIODS = {"one_time", "monthly", "yearly", "custom"}
STATUSES = {"draft", "published", "archived"}
MAX_PRICE_PAISE = 1_000_000_000_00  # ₹1,000,000,000.00
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PricingValidationError(ValueError):
    pass


def ensure_pricing_tables() -> None:
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS pricing_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            draft_json TEXT NOT NULL,
            published_json TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_pricing_items_status ON pricing_items(status)")
        conn.execute("""CREATE TABLE IF NOT EXISTS pricing_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            actor TEXT NOT NULL,
            before_json TEXT,
            after_json TEXT,
            created_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_pricing_audit_item_time ON pricing_audit_log(item_id, created_at)")


def _price_paise(value: Any, field: str = "amount_inr", optional: bool = False) -> int | None:
    if value is None and optional:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise PricingValidationError(f"{field} must be a valid INR amount.") from None
    if not amount.is_finite() or amount < 0:
        raise PricingValidationError(f"{field} must be a non-negative amount.")
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded != amount:
        raise PricingValidationError(f"{field} may have at most two decimal places.")
    paise = int(rounded * 100)
    if paise > MAX_PRICE_PAISE:
        raise PricingValidationError(f"{field} exceeds the allowed maximum.")
    return paise


def normalize_price(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title", "")).strip()
    slug = str(payload.get("slug", "")).strip().lower()
    category = str(payload.get("category", "")).strip().lower()
    description = str(payload.get("description", "")).strip()
    billing_period = str(payload.get("billing_period", "one_time")).strip().lower()
    discount_raw = payload.get("discount_percent", 0)
    try:
        discount = Decimal(str(discount_raw))
    except (InvalidOperation, ValueError, TypeError):
        raise PricingValidationError("discount_percent must be a number from 0 to 100.") from None
    if not discount.is_finite() or discount < 0 or discount > 100 or discount.as_tuple().exponent < -2:
        raise PricingValidationError("discount_percent must be between 0 and 100 with at most two decimal places.")
    if not title or len(title) > 120:
        raise PricingValidationError("Title is required and must be 120 characters or fewer.")
    if not SLUG_RE.fullmatch(slug) or len(slug) > 100:
        raise PricingValidationError("Slug must use lowercase letters, numbers, and single hyphens.")
    if category not in CATEGORIES:
        raise PricingValidationError("Choose service, subscription, or client_quote.")
    if billing_period not in BILLING_PERIODS:
        raise PricingValidationError("Choose one_time, monthly, yearly, or custom billing.")
    if len(description) > 2000:
        raise PricingValidationError("Description must be 2,000 characters or fewer.")
    amount_paise = _price_paise(payload.get("amount_inr"))
    promo_paise = _price_paise(payload.get("promo_price_inr"), "promo_price_inr", optional=True)
    if promo_paise is not None and promo_paise >= amount_paise:
        raise PricingValidationError("Promotional price must be lower than the regular price.")
    if discount > 0 and amount_paise == 0:
        raise PricingValidationError("A discount cannot be applied to a zero-priced item.")
    return {
        "title": title,
        "slug": slug,
        "category": category,
        "description": description,
        "amount_paise": amount_paise,
        "currency": "INR",
        "billing_period": billing_period,
        "discount_percent": str(discount.quantize(Decimal("0.01"))),
        "promo_price_paise": promo_paise,
    }


def _from_json(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else None


def _display(item: dict[str, Any], status: str, published: dict[str, Any] | None,
             created_at: str, updated_at: str, published_at: str | None) -> dict[str, Any]:
    data = dict(item)
    data["amount_inr"] = f"{(Decimal(int(data.pop('amount_paise'))) / Decimal(100)):.2f}"
    promo = data.pop("promo_price_paise")
    data["promo_price_inr"] = f"{(Decimal(int(promo)) / Decimal(100)):.2f}" if promo is not None else None
    data.update({
        "status": status,
        "published": published is not None and status != "archived",
        "has_unpublished_changes": published is not None and item != published and status != "archived",
        "published_at": published_at,
        "created_at": created_at,
        "updated_at": updated_at,
    })
    return data


def _audit(conn, item_id: int, event: str, before: dict[str, Any] | None,
           after: dict[str, Any] | None, actor: str = "owner") -> None:
    conn.execute(
        "INSERT INTO pricing_audit_log(item_id,event,actor,before_json,after_json,created_at) VALUES(?,?,?,?,?,?)",
        (item_id, event, actor, json.dumps(before, sort_keys=True) if before is not None else None,
         json.dumps(after, sort_keys=True) if after is not None else None, now()),
    )


def list_items(include_archived: bool = False) -> list[dict[str, Any]]:
    ensure_pricing_tables()
    where = "" if include_archived else "WHERE status != 'archived'"
    with db() as conn:
        rows = conn.execute(
            f"SELECT id,slug,draft_json,published_json,status,created_at,updated_at,published_at FROM pricing_items {where} ORDER BY id DESC"
        ).fetchall()
    result = []
    for row in rows:
        draft = _from_json(row["draft_json"]) or {}
        published = _from_json(row["published_json"])
        item = _display(draft, row["status"], published, row["created_at"], row["updated_at"], row["published_at"])
        item["id"] = int(row["id"])
        item["slug"] = row["slug"]
        result.append(item)
    return result


def create_item(payload: dict[str, Any], actor: str = "owner") -> dict[str, Any]:
    ensure_pricing_tables()
    item = normalize_price(payload)
    stamp = now()
    with db() as conn:
        existing = conn.execute("SELECT id FROM pricing_items WHERE slug=?", (item["slug"],)).fetchone()
        if existing:
            raise PricingValidationError("That slug is already in use. Choose a unique slug.")
        cursor = conn.execute(
            "INSERT INTO pricing_items(slug,draft_json,published_json,status,created_at,updated_at,published_at) VALUES(?,?,?,?,?,?,?)",
            (item["slug"], json.dumps(item, sort_keys=True), None, "draft", stamp, stamp, None),
        )
        item_id = getattr(cursor, "lastrowid", None)
        if item_id is None:
            row = conn.execute("SELECT id FROM pricing_items WHERE slug=?", (item["slug"],)).fetchone()
            item_id = row["id"]
        _audit(conn, int(item_id), "created_draft", None, item, actor)
    return next(entry for entry in list_items(include_archived=True) if entry["id"] == int(item_id))


def update_item(item_id: int, payload: dict[str, Any], actor: str = "owner") -> dict[str, Any]:
    ensure_pricing_tables()
    item = normalize_price(payload)
    stamp = now()
    with db() as conn:
        row = conn.execute(
            "SELECT id,slug,draft_json,published_json,status,created_at,updated_at,published_at FROM pricing_items WHERE id=?",
            (item_id,),
        ).fetchone()
        if not row:
            raise KeyError("Pricing item not found.")
        if row["status"] == "archived":
            raise PricingValidationError("Archived items cannot be edited. Create a new item instead.")
        slug_owner = conn.execute("SELECT id FROM pricing_items WHERE slug=? AND id<>?", (item["slug"], item_id)).fetchone()
        if slug_owner:
            raise PricingValidationError("That slug is already in use. Choose a unique slug.")
        before = _from_json(row["draft_json"]) or {}
        event = "draft_updated" if row["published_json"] is None else "published_item_draft_updated"
        conn.execute("UPDATE pricing_items SET slug=?,draft_json=?,updated_at=? WHERE id=?",
                     (item["slug"], json.dumps(item, sort_keys=True), stamp, item_id))
        _audit(conn, item_id, event, before, item, actor)
    return next(entry for entry in list_items(include_archived=True) if entry["id"] == item_id)


def publish_item(item_id: int, actor: str = "owner") -> dict[str, Any]:
    ensure_pricing_tables()
    stamp = now()
    with db() as conn:
        row = conn.execute(
            "SELECT id,slug,draft_json,published_json,status,created_at,updated_at,published_at FROM pricing_items WHERE id=?",
            (item_id,),
        ).fetchone()
        if not row:
            raise KeyError("Pricing item not found.")
        if row["status"] == "archived":
            raise PricingValidationError("Archived items cannot be published.")
        draft = _from_json(row["draft_json"]) or {}
        # Revalidate the persisted draft at the publication boundary.
        draft = normalize_price({
            **draft,
            "amount_inr": Decimal(int(draft["amount_paise"])) / 100,
            "promo_price_inr": Decimal(int(draft["promo_price_paise"])) / 100 if draft.get("promo_price_paise") is not None else None,
        })
        before = _from_json(row["published_json"])
        conn.execute(
            "UPDATE pricing_items SET draft_json=?,published_json=?,status='published',updated_at=?,published_at=? WHERE id=?",
            (json.dumps(draft, sort_keys=True), json.dumps(draft, sort_keys=True), stamp, stamp, item_id),
        )
        _audit(conn, item_id, "published", before, draft, actor)
    return next(entry for entry in list_items(include_archived=True) if entry["id"] == item_id)


def archive_item(item_id: int, actor: str = "owner") -> dict[str, Any]:
    ensure_pricing_tables()
    stamp = now()
    with db() as conn:
        row = conn.execute(
            "SELECT id,slug,draft_json,published_json,status,created_at,updated_at,published_at FROM pricing_items WHERE id=?",
            (item_id,),
        ).fetchone()
        if not row:
            raise KeyError("Pricing item not found.")
        before = _from_json(row["draft_json"])
        conn.execute("UPDATE pricing_items SET status='archived',updated_at=? WHERE id=?", (stamp, item_id))
        _audit(conn, item_id, "archived", before, before, actor)
    return next(entry for entry in list_items(include_archived=True) if entry["id"] == item_id)


def public_items() -> list[dict[str, Any]]:
    ensure_pricing_tables()
    with db() as conn:
        rows = conn.execute(
            "SELECT slug,published_json,published_at FROM pricing_items WHERE status='published' AND published_json IS NOT NULL ORDER BY id"
        ).fetchall()
    result = []
    for row in rows:
        item = _from_json(row["published_json"]) or {}
        # Client-specific quotes are never part of the public catalog, even when
        # the owner publishes their internal snapshot in HQ.
        if item.get("category") == "client_quote":
            continue
        data = dict(item)
        data["amount_inr"] = f"{(Decimal(int(data.pop('amount_paise'))) / Decimal(100)):.2f}"
        promo = data.pop("promo_price_paise")
        data["promo_price_inr"] = f"{(Decimal(int(promo)) / Decimal(100)):.2f}" if promo is not None else None
        data["slug"] = row["slug"]
        data["published_at"] = row["published_at"]
        result.append(data)
    return result


def audit_history(item_id: int, limit: int = 50) -> list[dict[str, Any]]:
    ensure_pricing_tables()
    with db() as conn:
        rows = conn.execute(
            "SELECT id,item_id,event,actor,before_json,after_json,created_at FROM pricing_audit_log WHERE item_id=? ORDER BY id DESC LIMIT ?",
            (item_id, max(1, min(int(limit), 100))),
        ).fetchall()
    result = []
    for row in rows:
        result.append({
            "id": int(row["id"]), "item_id": int(row["item_id"]), "event": row["event"],
            "actor": row["actor"], "before": _from_json(row["before_json"]),
            "after": _from_json(row["after_json"]), "created_at": row["created_at"],
        })
    return result
