# Nexora AI social-preview and image-alt audit

Audit date: 2026-10-23
Repository: `maazxhasan-hue/Tradinglab03-`
Public origin: `https://nexora-ai-public.onrender.com`

## Image inventory

The 17 HTML pages in `public-site/` were checked for literal HTML `<img>` and `<picture>` elements. None were found. The inspected pages are:

- `/` (`index.html`)
- `/about/`
- `/pricing/`
- `/privacy.html`
- `/video-studio.html`
- `/dashboard/website.html`
- `/dashboard/mythos.html`
- `/blog/seo-guide/`
- `/blog/small-business-website-checklist/`
- `/blog/landing-page-conversion/`
- `/blog/business-workflow-automation/`
- `/dashboard/login.html`
- `/dashboard/referrals.html`
- `/dashboard/privacy.html`
- `/pay.html`
- `/studio-agent.html`
- `/404.html`

No HTML image alt attributes need changing in this inventory because there are no inline HTML images. Decorative inline images, if introduced later, should use `alt=""`; meaningful images should use concise, context-specific descriptions of their visible content.

## Existing share image

- File: `public-site/og-image.svg`
- Public URL: `https://nexora-ai-public.onrender.com/og-image.svg`
- Dimensions declared in SVG: 1200 × 630
- Description/alt for metadata: `Nexora AI — thoughtful digital work, delivered clearly.`
- The root-level `og-image.svg` is also present in the repository.

This existing branded image is used as the site-wide default. No placeholder image was necessary. If the artwork is replaced later, replace `public-site/og-image.svg` (and keep the root copy synchronized if still used by another deployment path) with a 1200 × 630 asset, or update the metadata URLs accordingly. Social platform support for SVG varies; if a target platform does not render SVG previews reliably, supply a 1200 × 630 PNG fallback and point `og:image` and `twitter:image` at that PNG.

## Metadata policy

All 17 HTML pages receive unique page titles/descriptions in Open Graph and Twitter metadata, canonical-aligned `og:url` where a canonical exists, the shared absolute image URL, `og:image:alt`, and `twitter:card=summary_large_image`. Blog guide pages use `og:type=article`; other pages use `website`. Existing noindex directives remain in place for private/internal/duplicate pages.
