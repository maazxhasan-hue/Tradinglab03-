"""Generate a project-specific static website draft from an approved brief.

This builder creates pages and content scaffolding from supplied requirements. It
does not claim to implement arbitrary backend features, forms, payments, booking,
or integrations; those remain explicit implementation/QA items for review.
"""
from __future__ import annotations

from pathlib import Path
import html
import json
import re


def _items(value) -> list[str]:
    """Normalize a list or newline/comma-separated brief field into clean items."""
    if isinstance(value, list):
        source = value
    elif isinstance(value, str):
        source = re.split(r"\n|;", value)
    else:
        source = []
    return [str(item).strip() for item in source if str(item).strip()]


def _slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def generate_website(
    *,
    output_dir: str,
    business_name: str,
    tagline: str,
    services: list[str],
    contact_email: str,
    primary_color: str = "#0b7a75",
    pages_screens_deliverables=None,
    version_1_must_have_features=None,
    observed_need: str = "",
    target_audience: str = "",
    design_direction_and_references: str = "",
    content_and_assets: str = "",
    integrations_and_data: str = "",
) -> Path:
    if not business_name.strip() or not tagline.strip() or not services:
        raise ValueError("Business name, tagline, and at least one service are required")
    if not (primary_color.startswith("#") and len(primary_color) in (4, 7)
            and all(c in "0123456789abcdefABCDEF" for c in primary_color[1:])):
        raise ValueError("primary_color must be a hex color")

    pages = _items(pages_screens_deliverables) or ["Home", "Services", "Contact"]
    features = _items(version_1_must_have_features)
    services = [str(s).strip() for s in services if str(s).strip()]
    if not services:
        raise ValueError("At least one non-empty service is required")

    # Ensure a usable Home page exists and avoid duplicate filenames.
    if not any(p.casefold() in {"home", "homepage", "home page"} for p in pages):
        pages.insert(0, "Home")
    unique_pages = []
    seen = set()
    for index, label in enumerate(pages, start=1):
        slug = _slug(label, f"page-{index}")
        if slug in seen:
            slug = f"{slug}-{index}"
        seen.add(slug)
        unique_pages.append((label, slug))
    if not any(slug == "contact" for _, slug in unique_pages):
        unique_pages.append(("Contact", "contact"))

    esc = html.escape
    name, tag = esc(business_name), esc(tagline)
    email = esc(contact_email.strip())
    service_cards = "".join(
        '<article class="card"><h3>' + esc(s) +
        '</h3><p>Explore how this service supports the agreed business goals.</p></article>'
        for s in services
    )
    feature_list = (
        '<ul class="feature-list">' + "".join(f"<li>{esc(f)}</li>" for f in features) + "</ul>"
        if features else
        '<p class="muted">Version 1 features have not yet been confirmed. Confirm them before implementation.</p>'
    )
    nav = "".join(
        '<a href="' + ("index.html" if slug in {"home", "homepage", "home-page"} else esc(slug + ".html")) + '">' + esc(label) + "</a>"
        for label, slug in unique_pages
    )
    contact_block = (
        f'<a href="mailto:{email}">{email}</a>'
        if email else
        '<p class="notice">Public contact details are pending client approval.</p>'
    )
    goal_block = f"<p>{esc(observed_need)}</p>" if observed_need.strip() else ""
    audience_block = f"<p><strong>Audience:</strong> {esc(target_audience)}</p>" if target_audience.strip() else ""
    design_block = f"<p><strong>Design direction:</strong> {esc(design_direction_and_references)}</p>" if design_direction_and_references.strip() else ""
    assets_block = f"<p><strong>Content/assets:</strong> {esc(content_and_assets)}</p>" if content_and_assets.strip() else ""
    integrations_block = f"<p><strong>Integrations/data to confirm:</strong> {esc(integrations_and_data)}</p>" if integrations_and_data.strip() else ""

    styles = """<style>
:root{--brand:COLOR;--ink:#17212b;--muted:#5a6875;--paper:#f6f8fa}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,sans-serif;color:var(--ink);line-height:1.6}
header{padding:1rem max(1.25rem,calc((100% - 1120px)/2));display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid #e7ecef;flex-wrap:wrap}
.brand{font-weight:800}nav{display:flex;gap:.8rem;flex-wrap:wrap}nav a,a{color:var(--brand)}nav a{text-decoration:none}
.hero{padding:5rem 1.25rem;background:linear-gradient(135deg,#eef7f5,var(--paper));text-align:center}.hero-inner{max-width:820px;margin:auto}
h1{font-size:clamp(2.2rem,6vw,4.2rem);line-height:1.05;letter-spacing:-.04em}
.button{display:inline-block;background:var(--brand);color:white;text-decoration:none;padding:.85rem 1.2rem;border-radius:.7rem;font-weight:700}
section{max-width:1120px;margin:auto;padding:2.5rem 1.25rem}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}
.card{border:1px solid #e4e9ed;border-radius:1rem;padding:1.25rem;background:white}.feature-list{padding-left:1.4rem}
.muted{color:var(--muted)}.notice{background:#fff8e5;border-left:4px solid #d39b19;padding:1rem}
footer{padding:2rem 1.25rem;background:#101a22;color:white;text-align:center}:focus-visible{outline:3px solid #f0b429;outline-offset:3px}
@media(max-width:600px){header{align-items:flex-start}nav{width:100%}.hero{padding:3rem 1rem}}
</style>""".replace("COLOR", primary_color)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    page_files = []
    for label, slug in unique_pages:
        safe_label = esc(label)
        if slug == "contact":
            content = (
                '<section id="contact"><h1>Contact</h1>'
                '<p>Contact information must be confirmed by the business owner before launch.</p>'
                + contact_block + "</section>"
            )
        elif slug in {"services", "service"}:
            content = '<section><h1>Services</h1><div class="cards">' + service_cards + "</div></section>"
        else:
            content = (
                '<section><h1>' + safe_label + '</h1>' +
                (goal_block if slug in {"home", "homepage", "home-page"} else "") +
                (audience_block if slug in {"home", "homepage", "home-page"} else "") +
                (design_block if slug in {"home", "homepage", "home-page"} else "") +
                (assets_block if slug in {"home", "homepage", "home-page"} else "") +
                (integrations_block if slug in {"home", "homepage", "home-page"} else "") +
                '<h2>Version 1 requirements</h2>' + feature_list +
                '<p class="muted">This draft records requested scope; each feature needs implementation and acceptance testing before release.</p></section>'
            )
        hero = ""
        if slug in {"home", "homepage", "home-page"}:
            hero = (
                '<section class="hero"><div class="hero-inner"><p>WELCOME</p><h1>' + tag +
                '</h1><p>' + (esc(observed_need) if observed_need.strip() else
                'A draft tailored to the supplied business brief.') +
                '</p><a class="button" href="contact.html">Contact</a></div></section>'
            )
            content = (
                '<section><h2>What we do</h2><div class="cards">' + service_cards + '</div></section>' +
                '<section><h2>Version 1 requirements</h2>' + feature_list + '</section>' +
                '<section><h2>Project context</h2>' + goal_block + audience_block + design_block +
                assets_block + integrations_block + '</section>'
            )
        page = (
            '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="description" content="' + tag + '">'
            '<title>' + name + ' | ' + safe_label + '</title>' + styles +
            '</head><body><header><a class="brand" href="index.html">' + name +
            '</a><nav aria-label="Main navigation">' + nav + '</nav></header><main>' +
            hero + content + '</main><footer>Draft for review · ' + name +
            ' · Confirm scope, content, contact details, and functionality before launch.</footer></body></html>'
        )
        filename = "index.html" if slug in {"home", "homepage", "home-page"} else f"{slug}.html"
        (out / filename).write_text(page, encoding="utf-8")
        page_files.append({"label": label, "slug": slug, "file": filename})

    (out / "site_manifest.json").write_text(json.dumps({
        "business_name": business_name,
        "services": services,
        "requested_pages": page_files,
        "version_1_features": features,
        "contact_email_supplied": bool(contact_email.strip()),
        "review_required": True,
        "production_deployment_enabled": False,
        "unimplemented_features_require_implementation_and_acceptance_testing": True,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
