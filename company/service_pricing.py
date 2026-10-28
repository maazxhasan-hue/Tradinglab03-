"""Owner-managed service pricing with persistent SQLite storage and a strict INR 499 cap."""
from __future__ import annotations
import sqlite3
from company.database import connect_database, database_target, is_postgres_target
from pathlib import Path

MAX_SERVICE_PRICE = 499
DEFAULT_SERVICES = (
    ("business-website", "Business website starter"),
    ("landing-page", "Landing page starter"),
    ("seo-setup", "SEO setup starter"),
    ("workflow-automation", "Workflow automation starter"),
)

class PricingValidationError(ValueError):
    """Invalid service pricing input."""

def _validate_price(price: object) -> int:
    if isinstance(price, bool):
        raise PricingValidationError("Price must be a whole INR amount from ₹1 to ₹499.")
    try:
        value = int(price)
    except (TypeError, ValueError):
        raise PricingValidationError("Price must be a whole INR amount from ₹1 to ₹499.")
    if str(price).strip() != str(value) or not 1 <= value <= MAX_SERVICE_PRICE:
        raise PricingValidationError("Price must be a whole INR amount from ₹1 to ₹499.")
    return value

class PricingStore:
    def __init__(self, path: str | Path):
        self.path = database_target(path)
        if not is_postgres_target(self.path):
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS service_prices (
                service_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                price INTEGER NOT NULL CHECK(price BETWEEN 1 AND 499),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            for service_id, name in DEFAULT_SERVICES:
                db.execute("INSERT OR IGNORE INTO service_prices(service_id,name,price) VALUES(?,?,?)",
                           (service_id, name, MAX_SERVICE_PRICE))

    def _connect(self):
        return connect_database(self.path, timeout=10)

    def list_services(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT service_id,name,price,updated_at FROM service_prices ORDER BY service_id").fetchall()
            return [dict(row) for row in rows]

    def update_service(self, service_id: str, price: object) -> dict:
        service_id = str(service_id).strip()
        if not service_id or len(service_id) > 80:
            raise PricingValidationError("A valid service ID is required.")
        value = _validate_price(price)
        with self._connect() as db:
            cur = db.execute("UPDATE service_prices SET price=?, updated_at=CURRENT_TIMESTAMP WHERE service_id=?",
                             (value, service_id))
            if cur.rowcount != 1:
                raise KeyError(service_id)
            row = db.execute("SELECT service_id,name,price,updated_at FROM service_prices WHERE service_id=?",
                             (service_id,)).fetchone()
            return dict(row)
