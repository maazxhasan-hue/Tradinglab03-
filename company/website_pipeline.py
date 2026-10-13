"""Build a website starter and run a local quality gate; deployment stays disabled."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .website_builder import generate_website

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BRIEF = ROOT / "config" / "website_brief.example.json"

def quality_check(output_dir: str | Path) -> dict:
    out = Path(output_dir)
    page_path = out / "index.html"
    if not page_path.exists():
        return {"passed": False, "checks": [], "errors": ["index.html not found"]}
    page = page_path.read_text(encoding="utf-8")
    checks = {
        "html_lang": '<html lang="en">' in page,
        "viewport": 'name="viewport"' in page,
        "title": "<title>" in page and "</title>" in page,
        "primary_heading": "<h1>" in page and "</h1>" in page,
        "contact_path": 'id="contact"' in page and "mailto:" in page,
        "responsive_layout": "auto-fit" in page and "minmax(" in page,
        "keyboard_focus": ":focus-visible" in page,
        "no_placeholder_business_token": "BUSINESS" not in page and "TAGLINE" not in page,
    }
    errors = [name for name, passed in checks.items() if not passed]
    manifest_path = out / "site_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    return {
        "passed": not errors,
        "checks": [{"name": name, "passed": passed} for name, passed in checks.items()],
        "errors": errors,
        "review_required": True,
        "production_deployment_enabled": False,
        "manifest": manifest,
        "note": "Static checks are not a substitute for browser, accessibility, security, legal, or client review.",
    }

def build_from_brief(brief: dict, output_dir: str | Path) -> dict:
    allowed = {"business_name", "tagline", "services", "contact_email", "primary_color"}
    unknown = set(brief) - allowed
    if unknown:
        raise ValueError("Unexpected brief fields: " + ", ".join(sorted(unknown)))
    if not isinstance(brief.get("services"), list) or not all(isinstance(x, str) for x in brief["services"]):
        raise ValueError("services must be a list of strings")
    path = generate_website(
        output_dir=str(output_dir),
        business_name=str(brief.get("business_name", "")),
        tagline=str(brief.get("tagline", "")),
        services=brief.get("services", []),
        contact_email=str(brief.get("contact_email", "")),
        primary_color=str(brief.get("primary_color", "#0b7a75")),
    )
    report = quality_check(path)
    (path / "quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and check a static website draft")
    parser.add_argument("--brief", default=str(DEFAULT_BRIEF))
    parser.add_argument("--output", default=str(ROOT / "data" / "website_drafts" / "example"))
    args = parser.parse_args(argv)
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    print(json.dumps(build_from_brief(brief, args.output), ensure_ascii=False, indent=2))
    # Build can produce a draft even when quality checks fail; report honestly via exit code.
    report = quality_check(args.output)
    if not report["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
