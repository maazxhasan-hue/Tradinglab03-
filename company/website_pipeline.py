"""Build a project-specific static website draft and run a local quality gate."""
from __future__ import annotations
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
    manifest_path = out / "site_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    contact_path = out / "contact.html"
    contact_page = contact_path.read_text(encoding="utf-8") if contact_path.exists() else ""
    contact_form_handoff = (
        'action="mailto:' in contact_page
        and 'method="post"' in contact_page
        and 'name="Message"' in contact_page
        and 'type="submit"' in contact_page
        if manifest.get("contact_email_supplied") is True
        else "Public contact details are pending client approval" in contact_page
    )
    requested_pages = manifest.get("requested_pages", [])
    page_checks = {
        f"requested_page_exists:{entry.get('file', '')}": (out / str(entry.get("file", ""))).is_file()
        for entry in requested_pages if isinstance(entry, dict) and entry.get("file")
    }
    feature_checks = {
        f"feature_in_scope:{i}": str(feature).casefold() in page.casefold()
        for i, feature in enumerate(manifest.get("version_1_features", []), start=1)
    }
    checks = {
        "html_lang": '<html lang="en">' in page,
        "viewport": 'name="viewport"' in page,
        "title": "<title>" in page and "</title>" in page,
        "primary_heading": "<h1>" in page and "</h1>" in page,
        "contact_path": 'id="contact"' in (out / "contact.html").read_text(encoding="utf-8") if (out / "contact.html").exists() else False,
        "responsive_layout": "auto-fit" in page and "minmax(" in page,
        "mobile_navigation_toggle": 'class="mobile-menu"' in page and "<summary>Menu</summary>" in page and 'class="desktop-nav"' in page,
        "contact_form_handoff": contact_form_handoff,
        "keyboard_focus": ":focus-visible" in page,
        "no_template_tokens": "TAGLINE" not in page and "BUSINESS" not in page and "COLOR" not in page,
        "manifest_requires_review": manifest.get("review_required") is True,
        "deployment_disabled": manifest.get("production_deployment_enabled") is False,
        **page_checks,
        **feature_checks,
    }
    errors = [name for name, passed in checks.items() if not passed]
    return {
        "passed": not errors,
        "checks": [{"name": name, "passed": passed} for name, passed in checks.items()],
        "errors": errors,
        "review_required": True,
        "production_deployment_enabled": False,
        "manifest": manifest,
        "limitations": [
            "Generated pages are draft scaffolding, not proof that requested interactive features are implemented.",
            "Forms, authentication, payments, booking, backend behavior, and integrations require separate implementation and functional tests.",
            "Static checks do not replace browser, accessibility, security, legal, or client review.",
        ],
    }


def build_from_brief(brief: dict, output_dir: str | Path) -> dict:
    allowed = {
        "business_name", "tagline", "services", "contact_email", "primary_color",
        "pages_screens_deliverables", "version_1_must_have_features", "observed_need",
        "target_audience", "design_direction_and_references", "content_and_assets",
        "integrations_and_data",
    }
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
        pages_screens_deliverables=brief.get("pages_screens_deliverables"),
        version_1_must_have_features=brief.get("version_1_must_have_features"),
        observed_need=str(brief.get("observed_need", "")),
        target_audience=str(brief.get("target_audience", "")),
        design_direction_and_references=str(brief.get("design_direction_and_references", "")),
        content_and_assets=str(brief.get("content_and_assets", "")),
        integrations_and_data=str(brief.get("integrations_and_data", "")),
    )
    report = quality_check(path)
    (path / "quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Build and check a static website draft")
    parser.add_argument("--brief", default=str(DEFAULT_BRIEF))
    parser.add_argument("--output", default=str(ROOT / "data" / "website_drafts" / "example"))
    args = parser.parse_args(argv)
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    print(json.dumps(build_from_brief(brief, args.output), ensure_ascii=False, indent=2))
    report = quality_check(args.output)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
