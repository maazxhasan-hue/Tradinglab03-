"""Local content draft workflow. Does not publish or contact external services."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
from .policy import review_content

ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = ROOT / "config" / "course_facts.json"
OUT_DIR = ROOT / "data" / "drafts"

def load_facts() -> dict[str, Any]:
    return json.loads(FACTS_PATH.read_text(encoding="utf-8"))

def build_reel_draft(topic: str) -> dict[str, Any]:
    facts = load_facts()
    script = (
        f"Want to understand {topic}? Start with the fundamentals. "
        f"{facts['product_name']} is a beginner-oriented course with {facts['modules']} modules, "
        "a practical project, and workbook materials. Explore AI trading concepts, Python, "
        "backtesting, and paper trading. Education does not guarantee trading results. "
        f"Course details: {facts['course_url']} Price: ₹{facts['price_inr']}."
    )
    flags = review_content(script)
    digest = hashlib.sha256(script.encode("utf-8")).hexdigest()[:16]
    return {"id": digest, "type": "reel_script", "topic": topic, "script": script,
            "policy_flags": flags, "state": "blocked" if flags else "pending_approval",
            "external_publish_enabled": False}

def save_draft(draft: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{draft['id']}.json"
    if not path.exists():
        path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
