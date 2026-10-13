"""Generate a clean static website starter from a validated business brief."""
from pathlib import Path
import html, json

def generate_website(*, output_dir: str, business_name: str, tagline: str,
                     services: list[str], contact_email: str, primary_color: str = "#0b7a75") -> Path:
    if not business_name.strip() or not tagline.strip() or not services:
        raise ValueError("Business name, tagline, and at least one service are required")
    if not (primary_color.startswith("#") and len(primary_color) in (4, 7)
            and all(c in "0123456789abcdefABCDEF" for c in primary_color[1:])):
        raise ValueError("primary_color must be a hex color")
    name, tag, email = map(html.escape, (business_name, tagline, contact_email))
    cards = "".join(
        '<article class="card"><h3>' + html.escape(s) +
        '</h3><p>Talk with us about a tailored solution for your goals.</p></article>'
        for s in services
    )
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="TAGLINE"><title>BUSINESS | Official Website</title>
<style>
:root{--brand:COLOR;--ink:#17212b;--muted:#5a6875;--paper:#f6f8fa}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,sans-serif;color:var(--ink);line-height:1.6}
header{padding:1rem max(1.25rem,calc((100% - 1120px)/2));display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid #e7ecef}
.brand{font-weight:800}a{color:var(--brand)}.hero{padding:6rem 1.25rem;background:linear-gradient(135deg,#eef7f5,var(--paper));text-align:center}
.hero-inner{max-width:820px;margin:auto}h1{font-size:clamp(2.2rem,6vw,4.5rem);line-height:1.05;letter-spacing:-.04em}.button{display:inline-block;background:var(--brand);color:white;text-decoration:none;padding:.85rem 1.2rem;border-radius:.7rem;font-weight:700}
section{max-width:1120px;margin:auto;padding:3rem 1.25rem}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}.card{border:1px solid #e4e9ed;border-radius:1rem;padding:1.25rem;background:white}
footer{padding:2rem 1.25rem;background:#101a22;color:white;text-align:center}:focus-visible{outline:3px solid #f0b429;outline-offset:3px}
</style></head><body>
<header><div class="brand">BUSINESS</div><a href="#contact">Contact</a></header>
<main><section class="hero"><div class="hero-inner"><p>WELCOME</p><h1>TAGLINE</h1><p>Clear solutions, thoughtfully built around your business.</p><a class="button" href="#contact">Discuss your project</a></div></section>
<section><h2>What we do</h2><div class="cards">CARDS</div></section>
<section id="contact"><h2>Let's talk</h2><p>Tell us what you are building and we will follow up with next steps.</p><p><a href="mailto:EMAIL">EMAIL</a></p></section></main>
<footer>© BUSINESS. Replace this footer with approved legal and business details before launch.</footer></body></html>"""
    page = page.replace("TAGLINE", tag).replace("BUSINESS", name).replace("COLOR", primary_color)
    page = page.replace("CARDS", cards).replace("EMAIL", email)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "site_manifest.json").write_text(json.dumps({
        "business_name": business_name, "services": services,
        "review_required": True, "production_deployment_enabled": False
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
