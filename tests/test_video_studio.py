from pathlib import Path


def test_video_studio_exposes_real_local_webm_rendering():
    source = Path("public-site/video-studio.html").read_text(encoding="utf-8")
    assert 'id="renderDraft"' in source
    assert 'id="draftPreview"' in source
    assert 'id="downloadVideo"' in source
    assert "MediaRecorder" in source
    assert "captureStream(30)" in source
    assert "URL.createObjectURL(blob)" in source


def test_video_studio_does_not_claim_cloud_or_ai_video_generation():
    source = Path("public-site/video-studio.html").read_text(encoding="utf-8").lower()
    assert "not an ai-generated photorealistic 3d film" in source
    assert "not uploaded automatically" in source
    assert "no data is uploaded" in source


def test_video_studio_has_required_capability_fallbacks():
    source = Path("public-site/video-studio.html").read_text(encoding="utf-8")
    assert "does not support local video recording" in source
    assert "cannot encode WebM video" in source
    assert "Local rendering failed:" in source
