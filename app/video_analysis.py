from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg is required for video analysis but was not found on PATH"
        )
    if shutil.which("ffprobe") is None:
        raise RuntimeError(
            "ffprobe is required for video analysis but was not found on PATH"
        )


def get_video_duration_seconds(video_path: str) -> float:
    _require_ffmpeg()

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    duration_str = payload.get("format", {}).get("duration")
    if not duration_str:
        raise RuntimeError("Could not determine video duration")

    duration = float(duration_str)
    if duration <= 0:
        raise RuntimeError("Video duration must be greater than zero")

    return duration


def _sample_timestamps(duration: float) -> list[float]:
    if duration <= 0:
        return [0.0]

    fractions = [0.2, 0.5, 0.8]
    timestamps: list[float] = []

    for fraction in fractions:
        ts = duration * fraction
        ts = min(ts, max(duration - 0.1, 0.0))
        ts = max(0.0, ts)
        timestamps.append(ts)

    deduped: list[float] = []
    for ts in timestamps:
        rounded = round(ts, 2)
        if rounded not in [round(x, 2) for x in deduped]:
            deduped.append(ts)

    return deduped or [0.0]


def extract_keyframes(video_path: str, frame_count: int = 3) -> list[str]:
    _require_ffmpeg()

    duration = get_video_duration_seconds(video_path)
    timestamps = _sample_timestamps(duration)[:frame_count]

    output_dir = Path(tempfile.mkdtemp(prefix="lorewell_frames_"))
    frame_paths: list[str] = []

    for index, ts in enumerate(timestamps, start=1):
        frame_path = output_dir / f"frame_{index}.jpg"

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(ts),
                "-i",
                video_path,
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(frame_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if frame_path.exists():
            frame_paths.append(str(frame_path))

    if not frame_paths:
        raise RuntimeError("No key frames could be extracted from video")

    return frame_paths
