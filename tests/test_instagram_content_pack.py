"""Regression checks for approval-gated Instagram content generation."""
import argparse
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "instagram_content_pack", ROOT / "company" / "instagram_content_pack.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InstagramContentPackTests(unittest.TestCase):
    def make_pack(self):
        return MODULE.build(argparse.Namespace(
            account="nexora_ai",
            topic="AI services for small businesses",
            offer="Website and automation services",
            audience="small-business owners",
            cta="Message us to discuss your project",
        ))

    def test_builds_seven_reviewable_posts(self):
        pack = self.make_pack()
        self.assertEqual(len(pack["posts"]), 7)
        self.assertEqual([p["day"] for p in pack["posts"]], list(range(1, 8)))
        self.assertTrue(all(p["hook"] and p["caption"] and p["beat_sheet"] for p in pack["posts"]))

    def test_captions_keep_paragraph_breaks(self):
        pack = self.make_pack()
        for post in pack["posts"]:
            self.assertIn("\n\n", post["caption"])
            self.assertIn("\n\n", post["caption"])

    def test_generation_never_publishes_and_requires_review(self):
        pack = self.make_pack()
        self.assertEqual(pack["status"], "draft_for_human_review")
        self.assertEqual(pack["publishing"], {"performed": False, "approval_required": True})
        for post in pack["posts"]:
            self.assertTrue(any("draft" in flag.lower() for flag in post["review_flags"]))
            self.assertTrue(any("verify" in flag.lower() for flag in post["review_flags"]))


if __name__ == "__main__":
    unittest.main()
