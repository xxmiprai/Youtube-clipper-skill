#!/usr/bin/env python3
"""Shared helpers for clipping, subtitles, and workspace output management."""

import os
import re
from datetime import datetime
from pathlib import Path


def time_to_seconds(time_str: str) -> float:
    """Convert HH:MM:SS.mmm, MM:SS.mmm, or SS.mmm to seconds."""
    time_str = time_str.strip()
    parts = time_str.split(":")

    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    return float(parts[0])


def seconds_to_time(seconds: float, include_hours: bool = True, use_comma: bool = False) -> str:
    """Convert seconds to a display timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    separator = "," if use_comma else "."

    if include_hours or hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", separator)
    return f"{minutes:02d}:{secs:06.3f}".replace(".", separator)


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """Remove filename characters that are unsafe across platforms."""
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = filename.strip(". ")
    filename = filename.replace(" ", "_")
    filename = re.sub(r"_+", "_", filename)

    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        if ext:
            filename = name[: max_length - len(ext)] + ext
        else:
            filename = filename[:max_length]

    return filename


def create_output_dir(base_dir: str = None) -> Path:
    """Create a timestamped output directory."""
    root = Path(base_dir) if base_dir else Path.cwd() / "youtube-clips"
    output_dir = root / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def create_workspace_output_dir(base_workspace: str = None) -> Path:
    """Create a timestamped output directory under `<workspace>/outputs`."""
    workspace = Path(base_workspace) if base_workspace else Path.cwd()
    return create_output_dir(workspace / "outputs")


def format_file_size(size_bytes: int) -> str:
    """Format bytes into a human-readable file size."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def parse_time_range(time_range: str) -> tuple:
    """Parse `start-end` time range strings into second offsets."""
    parts = time_range.replace(" ", "").split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid time range format: {time_range}")

    start_time = time_to_seconds(parts[0])
    end_time = time_to_seconds(parts[1])

    if start_time >= end_time:
        raise ValueError(f"Start time must be before end time: {time_range}")

    return start_time, end_time


def adjust_subtitle_time(time_seconds: float, offset: float) -> float:
    """Shift subtitle time relative to a clip start."""
    return max(0.0, time_seconds - offset)


def get_video_duration_display(seconds: float) -> str:
    """Format a duration for display."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def validate_url(url: str) -> bool:
    """Validate that the input looks like an HTTP(S) video page URL."""
    return bool(re.match(r"^https?://[^\s]+$", url))


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not already exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    assert time_to_seconds("01:23:45.678") == 5025.678
    assert time_to_seconds("23:45.678") == 1425.678
    assert time_to_seconds("45.678") == 45.678
    assert sanitize_filename("Hello: World?") == "Hello_World"
    assert parse_time_range("00:00 - 03:15") == (0.0, 195.0)
    assert parse_time_range("01:30:00-01:33:15") == (5400.0, 5595.0)
    assert validate_url("https://youtube.com/watch?v=Ckt1cj0xjRM") is True
    assert validate_url("https://www.pornhub.com/view_video.php?viewkey=ph5f1234567890") is True
    assert validate_url("invalid_url") is False
    print("All tests passed.")
