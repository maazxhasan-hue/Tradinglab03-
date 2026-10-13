"""Verify Stripe webhook signatures and record idempotent paid/refund events.

This module does not create charges or payment links. It only reconciles provider-signed
webhook payloads when a separately configured endpoint passes raw bytes and signature.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

def verify_stripe_signature(payload: bytes, signature_header: str, secret: str, *,
                            tolerance_seconds: int = 300, now: int | None = None) -> bool:
    if not payload or not signature_header or not secret:
        return False
    fields: dict[str, list[str]] = {}
    for part in signature_header.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields.setdefault(key.strip(), []).append(value.strip())
    try:
        timestamp = int(fields["t"][0])
    except (KeyError, ValueError, IndexError):
        return False
    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > tolerance_seconds:
        return False
    signed = str(timestamp).encode() + b"." + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in fields.get("v1", []))

class RevenueLedger:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS provider_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    amount_minor INTEGER NOT NULL DEFAULT 0,
                    currency TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                )
            """)
    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=10)
        con.row_factory = sqlite3.Row
        return con
    def ingest_stripe_event(self, payload: bytes, signature_header: str, webhook_secret: str,
                            *, now: int | None = None) -> dict[str, Any]:
        if not verify_stripe_signature(payload, signature_header, webhook_secret, now=now):
            raise ValueError("Invalid or expired Stripe webhook signature")
        try:
            event = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Webhook payload is not valid JSON") from exc
        event_id = event.get("id")
        event_type = event.get("type")
        obj = (event.get("data") or {}).get("object") or {}
        object_id = obj.get("id")
        if not all(isinstance(x, str) and x for x in (event_id, event_type, object_id)):
            raise ValueError("Webhook is missing event id, type, or object id")
        amount, currency, status = 0, str(obj.get("currency", "")).upper(), "ignored"
        if event_type == "checkout.session.completed":
            if obj.get("payment_status") == "paid":
                amount = int(obj.get("amount_total") or 0)
                status = "paid" if amount > 0 else "ignored_zero_amount"
        elif event_type in {"charge.refunded", "refund.updated"}:
            amount = int(obj.get("amount_refunded") or obj.get("amount") or 0)
            status = "refund" if amount > 0 else "ignored_zero_refund"
        with self._connect() as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO provider_events(event_id,event_type,object_id,amount_minor,currency,status) VALUES(?,?,?,?,?,?)",
                (event_id, event_type, object_id, amount, currency, status),
            )
            inserted = cur.rowcount == 1
        return {"event_id": event_id, "event_type": event_type, "object_id": object_id,
                "amount_minor": amount, "currency": currency, "status": status,
                "duplicate": not inserted, "recorded": inserted}
    def summary(self) -> dict[str, Any]:
        with self._connect() as con:
            rows = con.execute("SELECT currency, status, SUM(amount_minor) AS amount_minor, COUNT(*) AS events FROM provider_events GROUP BY currency,status").fetchall()
        grouped = [{"currency": r["currency"], "status": r["status"],
                    "amount_minor": r["amount_minor"] or 0, "events": r["events"]} for r in rows]
        return {"provider_events": grouped,
                "note": "Amounts are grouped by currency and event status; refunds are not netted against sales automatically."}
