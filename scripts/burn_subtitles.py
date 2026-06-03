#!/usr/bin/env python3
"""Burn subtitles into a video with FFmpeg."""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict

try:
    from .utils import format_file_size
except ImportError:
    from utils import format_file_size


def detect_ffmpeg_variant() -> Dict:
    """Detect FFmpeg and whether it supports the subtitles filter."""
    print("Checking FFmpeg environment...")

    if platform.system() == "Darwin":
        for candidate in (
            "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
            "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
        ):
            if Path(candidate).exists():
                has_libass = check_libass_support(candidate)
                print(f"  Found ffmpeg-full: {candidate}")
                print(f"  subtitles filter support: {has_libass}")
                return {"type": "full", "path": candidate, "has_libass": has_libass}

    standard_path = shutil.which("ffmpeg")
    if standard_path:
        has_libass = check_libass_support(standard_path)
        variant_type = "full" if has_libass else "standard"
        print(f"  Found FFmpeg: {standard_path}")
        print(f"  Type: {variant_type}")
        print(f"  subtitles filter support: {has_libass}")
        return {"type": variant_type, "path": standard_path, "has_libass": has_libass}

    print("  FFmpeg not found")
    return {"type": "none", "path": None, "has_libass": False}


def check_libass_support(ffmpeg_path: str) -> bool:
    """Return whether the FFmpeg binary supports subtitle burn-in."""
    try:
        result = subprocess.run(
            [ffmpeg_path, "-filters"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return "subtitles" in result.stdout.lower()
    except Exception:
        return False


def install_ffmpeg_full_guide():
    """Print environment guidance for subtitle burn-in support."""
    print("\n" + "=" * 60)
    print("FFmpeg with subtitle filter support is required for burn-in.")
    print("=" * 60)


def escape_subtitle_filter_path(path: str) -> str:
    """Escape subtitle file paths for the FFmpeg subtitles filter."""
    normalized = Path(path).as_posix()
    if len(normalized) >= 2 and normalized[1] == ":":
        normalized = normalized[0] + "\\:" + normalized[2:]
    return normalized.replace("'", r"\'")


def build_subtitle_filter(subtitle_path: str, font_size: int, margin_v: int) -> str:
    """Build a Windows-safe FFmpeg subtitles filter string."""
    escaped_path = escape_subtitle_filter_path(subtitle_path)
    return (
        f"subtitles='{escaped_path}':"
        f"force_style='FontSize={font_size},MarginV={margin_v}'"
    )


def build_burn_command(
    ffmpeg_path: str,
    input_video: str,
    subtitle_filter: str,
    output_video: str,
) -> list:
    """Build a player-friendly FFmpeg command for subtitle burn-in."""
    return [
        ffmpeg_path,
        "-i",
        input_video,
        "-vf",
        subtitle_filter,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-y",
        output_video,
    ]


def prepare_output_path(output_path: str) -> Path:
    """Ensure the destination directory exists and return the final output path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path

    if platform.system() == "Darwin":
        print("macOS:")
        print("  brew install ffmpeg-full")
        print("  /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg")
        print("  /usr/local/opt/ffmpeg-full/bin/ffmpeg")
    else:
        print("Windows/Linux:")
        print("  Install an FFmpeg build that includes subtitle filter support.")
        print("  Then verify with:")
        print("  ffmpeg -filters")

    print("=" * 60)


def burn_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    ffmpeg_path: str = None,
    font_size: int = 24,
    margin_v: int = 30,
) -> str:
    """Burn subtitles into a video file."""
    video_path = Path(video_path)
    subtitle_path = Path(subtitle_path)
    output_path = prepare_output_path(output_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not subtitle_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

    if ffmpeg_path is None:
        ffmpeg_info = detect_ffmpeg_variant()
        if ffmpeg_info["type"] == "none":
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg not found.")
        if not ffmpeg_info["has_libass"]:
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg does not support subtitle burn-in.")
        ffmpeg_path = ffmpeg_info["path"]

    print("\nBurning subtitles into video...")
    print(f"  Video: {video_path.name}")
    print(f"  Subtitle: {subtitle_path.name}")
    print(f"  Output: {output_path.name}")
    print(f"  FFmpeg: {ffmpeg_path}")

    temp_dir = tempfile.mkdtemp(prefix="youtube_clipper_")
    print(f"  Temp directory: {temp_dir}")

    try:
        temp_video = os.path.join(temp_dir, "video.mp4")
        temp_subtitle = os.path.join(temp_dir, "subtitle.srt")
        temp_output = os.path.join(temp_dir, "output.mp4")

        shutil.copy(video_path, temp_video)
        shutil.copy(subtitle_path, temp_subtitle)

        subtitle_filter = build_subtitle_filter(
            temp_subtitle,
            font_size=font_size,
            margin_v=margin_v,
        )

        cmd = build_burn_command(
            ffmpeg_path=ffmpeg_path,
            input_video=temp_video,
            subtitle_filter=subtitle_filter,
            output_video=temp_output,
        )

        print("  Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("\nFFmpeg failed:")
            print(result.stderr)
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")

        if not Path(temp_output).exists():
            raise RuntimeError("Output file was not created.")

        shutil.copyfile(temp_output, output_path)

        output_size = output_path.stat().st_size
        print("Subtitle burn-in complete.")
        print(f"  Output file: {output_path}")
        print(f"  File size: {format_file_size(output_size)}")

        return str(output_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """CLI entry point."""
    if len(sys.argv) < 4:
        print("Usage: python burn_subtitles.py <video> <subtitle> <output> [font_size] [margin_v]")
        print()
        print("Arguments:")
        print("  video      - input video path")
        print("  subtitle   - input subtitle path in SRT format")
        print("  output     - output video path")
        print("  font_size  - optional font size, default 24")
        print("  margin_v   - optional bottom margin, default 30")
        print()
        print("Examples:")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4 28 40")
        print()
        print("In Codex, prefer using the configured Conda interpreter.")
        sys.exit(1)

    video_path = sys.argv[1]
    subtitle_path = sys.argv[2]
    output_path = sys.argv[3]
    font_size = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    margin_v = int(sys.argv[5]) if len(sys.argv) > 5 else 30

    try:
        result_path = burn_subtitles(
            video_path,
            subtitle_path,
            output_path,
            font_size=font_size,
            margin_v=margin_v,
        )
        print(f"\nDone. Output file: {result_path}")
    except Exception as exc:
        print(f"\nError: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
