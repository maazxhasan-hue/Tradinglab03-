#!/usr/bin/env python3
"""Validate basic technical properties of a short-form video using ffprobe.

This is a technical gate, not a substitute for visual or audio review.
Requires ffprobe (normally installed with FFmpeg).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def probe(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
    except FileNotFoundError as exc:
        raise RuntimeError("ffprobe is not installed or is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffprobe timed out while reading the video") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ffprobe exited {result.returncode}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned invalid JSON") from exc


def number(value: Any) -> float | None:
    try:
        parsed = float(value)
        return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else None
    except (TypeError, ValueError):
        return None


def check_video(path: Path, min_duration: float, max_duration: float,
                aspect: str | None, require_audio: bool, min_width: int) -> dict[str, Any]:
    report: dict[str, Any] = {"file": str(path), "passed": False, "checks": [], "errors": []}

    def add(name: str, passed: bool, detail: str) -> None:
        report["checks"].append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            report["errors"].append(f"{name}: {detail}")

    if not path.is_file():
        add("file_exists", False, "Input file does not exist.")
        return report
    add("file_exists", True, f"{path.stat().st_size} bytes")

    try:
        data = probe(path)
    except RuntimeError as exc:
        add("ffprobe", False, str(exc))
        return report

    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    add("video_stream", bool(videos), "Video stream found." if videos else "No video stream found.")
    if not videos:
        report["metadata"] = {"format": fmt.get("format_name"), "duration": fmt.get("duration")}
        return report

    video = videos[0]
    duration = number(video.get("duration")) or number(fmt.get("duration"))
    add("duration_15_20s", duration is not None and min_duration <= duration <= max_duration,
        f"Duration={duration}s; required {min_duration}–{max_duration}s.")
    width, height = int(video.get("width") or 0), int(video.get("height") or 0)
    add("minimum_width", width >= min_width, f"Dimensions={width}x{height}; minimum width={min_width}px.")
    add("dimensions_valid", width > 0 and height > 0, f"Dimensions={width}x{height}.")
    if aspect and width > 0 and height > 0:
        try:
            expected_w, expected_h = (float(v) for v in aspect.split(":", 1))
            actual = width / height
            expected = expected_w / expected_h
            delta = abs(actual - expected)
            add("aspect_ratio", delta <= 0.025, f"Actual={actual:.4f}; expected {aspect} ({expected:.4f}); tolerance=0.025.")
        except (ValueError, ZeroDivisionError):
            add("aspect_ratio_argument", False, f"Invalid aspect ratio '{aspect}'. Use W:H, e.g. 9:16.")
    fps_raw = str(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1")
    try:
        n, d = fps_raw.split("/", 1)
        fps = float(n) / float(d) if float(d) else 0.0
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    add("frame_rate", fps >= 24, f"Average frame rate={fps:.3f} fps; minimum=24 fps.")
    add("audio_present_if_required", bool(audios) or not require_audio,
        "Audio stream found." if audios else ("Audio is required but no audio stream exists." if require_audio else "No audio stream; allowed by this job's settings."))

    if audios and duration is not None:
        audio_duration = number(audios[0].get("duration"))
        if audio_duration is None:
            audio_duration = number(fmt.get("duration"))
        delta = abs(audio_duration - duration) if audio_duration is not None else None
        add("audio_video_duration_alignment", delta is not None and delta <= 0.25,
            f"Audio/video duration difference={delta}s; maximum=0.25s." if delta is not None else "Could not determine audio duration.")

    report["metadata"] = {
        "duration_seconds": duration, "width": width, "height": height,
        "aspect_ratio_actual": round(width / height, 5) if width and height else None,
        "frame_rate": round(fps, 3), "video_codec": video.get("codec_name"),
        "audio_codec": audios[0].get("codec_name") if audios else None,
        "format": fmt.get("format_name"), "size_bytes": number(fmt.get("size")),
    }
    report["passed"] = all(item["passed"] for item in report["checks"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Rendered video file to inspect")
    parser.add_argument("--min-duration", type=float, default=15.0)
    parser.add_argument("--max-duration", type=float, default=20.0)
    parser.add_argument("--aspect-ratio", help="Expected ratio, e.g. 9:16, 16:9, 1:1")
    parser.add_argument("--require-audio", action="store_true", help="Fail if no audio stream is present")
    parser.add_argument("--min-width", type=int, default=1080, help="Minimum pixel width (default: 1080)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report")
    args = parser.parse_args()

    if args.min_duration <= 0 or args.max_duration < args.min_duration or args.min_width <= 0:
        parser.error("duration and width limits must be positive and max-duration >= min-duration")

    report = check_video(args.video, args.min_duration, args.max_duration,
                         args.aspect_ratio, args.require_audio, args.min_width)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Video QA: {'PASS' if report['passed'] else 'FAIL'} — {report['file']}")
        for item in report["checks"]:
            print(f"[{'PASS' if item['passed'] else 'FAIL'}] {item['name']}: {item['detail']}")
        for error in report["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        print("Note: technical checks do not replace visual/audio inspection.")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
