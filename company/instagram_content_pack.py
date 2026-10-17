"""Generate an approval-ready Instagram content pack without publishing or inventing results.

Usage:
  python company/instagram_content_pack.py --account tradinglab03 --topic "AI trading education" --offer "AI trading course" --cta "DM COURSE for details"
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "instagram_content_packs"

def clean(text: str) -> str:
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def build(args):
    account = clean(args.account)
    topic = clean(args.topic)
    offer = clean(args.offer)
    cta = clean(args.cta)
    audience = clean(args.audience)
    pillars = [
        ("Myth vs reality", f"An expensive mistake people make about {topic}", "Explain one misconception, then give a practical correction."),
        ("Tiny tutorial", f"One small {topic} improvement you can make today", "Show 3 clear steps; keep each step visible on screen."),
        ("Checklist", f"Before you try {topic}, check these 3 things", "Use a checklist and explain why each item matters."),
        ("Behind the scenes", f"What a careful workflow for {topic} actually looks like", "Show the process, tools and verification—not unsupported results."),
        ("Mistake to avoid", f"Don't skip this check when working on {topic}", "Describe the risk and the safer alternative."),
        ("FAQ", f"A question beginners ask about {topic}", "Answer directly, then add one useful caveat."),
        ("Offer / invitation", f"Who this {offer} is designed to help", "Explain deliverables and fit honestly; avoid income or outcome guarantees."),
    ]
    items = []
    for i, (pillar, hook, outline) in enumerate(pillars, 1):
        hook = clean(hook)
        caption = (
            f"{hook}.\n\n"
            f"Here is the practical takeaway for {audience}: {outline} "
            "Check claims before posting and replace any generic example with something you personally verified.\n\n"
            f"{cta}\n\n"
            "#learnonthego #smallbusiness #digitalskills"
        )
        caption = clean(caption).replace(".\n\n", ".\n\n")
        items.append({
            "day": i, "pillar": pillar, "format": "Reel (25–35 seconds)",
            "hook": hook, "on_screen_text": hook,
            "beat_sheet": [
                {"time": "0–3s", "beat": hook},
                {"time": "3–10s", "beat": "State the problem in plain language."},
                {"time": "10–24s", "beat": outline},
                {"time": "24–32s", "beat": "Summarize one useful action and invite a response."},
            ],
            "caption": caption,
            "cta": cta,
            "hashtags": ["#learnonthego", "#smallbusiness", "#digitalskills"],
            "review_flags": [
                "Verify every factual claim and any numbers before publication.",
                "Do not claim profits, guaranteed results, client outcomes or testimonials without evidence.",
                "Confirm the CTA, offer and account branding.",
                "This is a draft; no post has been scheduled or published."
            ],
        })
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "draft_for_human_review",
        "account": account,
        "topic": topic,
        "offer": offer,
        "audience": audience,
        "publishing": {"performed": False, "approval_required": True},
        "posts": items,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--account", required=True, choices=["tradinglab03", "nexora_ai"])
    p.add_argument("--topic", required=True)
    p.add_argument("--offer", required=True)
    p.add_argument("--audience", default="beginners and small-business owners")
    p.add_argument("--cta", default="Save this for later and ask a question in the comments.")
    args = p.parse_args()
    pack = build(args)
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT / f"{args.account}-{stamp}.json"
    path.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = OUT / f"{args.account}-{stamp}.md"
    lines = [f"# Instagram draft pack — {args.account}", "", f"- Topic: {args.topic}", f"- Offer: {args.offer}", "- Status: DRAFT — approval required", "- Publishing: NOT performed", ""]
    for post in pack["posts"]:
        lines += [f"## Day {post['day']}: {post['pillar']}", "", f"**Hook:** {post['hook']}", "", "**Beat sheet**"]
        lines += [f"- {b['time']}: {b['beat']}" for b in post["beat_sheet"]]
        lines += ["", "**Caption**", "", post["caption"], "", "**Review before posting**"]
        lines += [f"- {flag}" for flag in post["review_flags"]]
        lines += [""]
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Created {len(pack['posts'])} draft posts for {args.account}")
    print(f"JSON: {path}")
    print(f"Markdown: {md}")
    print("No publishing or external messaging was performed.")

if __name__ == "__main__":
    main()
