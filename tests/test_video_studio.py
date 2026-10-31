from pathlib import Path
import unittest


class VideoStudioRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("public-site/video-studio.html").read_text(encoding="utf-8")
        cls.lower = cls.source.lower()

    def test_exposes_real_local_webm_rendering(self):
        for required in (
            'id="renderDraft"', 'id="draftPreview"', 'id="downloadVideo"',
            "MediaRecorder", "captureStream(30)", "URL.createObjectURL(blob)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.source)

    def test_does_not_claim_cloud_or_ai_video_generation(self):
        self.assertIn("not an ai-generated photorealistic 3d film", self.lower)
        self.assertIn("not uploaded automatically", self.lower)
        self.assertIn("no data is uploaded", self.lower)

    def test_has_required_capability_fallbacks(self):
        for required in (
            "does not support local video recording",
            "cannot encode WebM video",
            "Local rendering failed:",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.source)


if __name__ == "__main__":
    unittest.main()
