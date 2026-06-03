#!/usr/bin/env python3
"""Download a video and preferred subtitle tracks with yt-dlp."""

import json
import sys
from pathlib import Path

try:
    from .utils import (
        ensure_directory,
        format_file_size,
        get_video_duration_display,
        validate_url,
    )
except ImportError:
    from utils import (
        ensure_directory,
        format_file_size,
        get_video_duration_display,
        validate_url,
    )


def download_video(url: str, output_dir: str = None) -> dict:
    """Download a video and preferred subtitle tracks."""
    try:
        import yt_dlp
    except ImportError:
        print("Error: yt-dlp is not installed.")
        print("Install it with the configured Codex Python environment.")
        sys.exit(1)

    if not validate_url(url):
        raise ValueError(f"Invalid video URL: {url}")

    output_path = Path(output_dir) if output_dir else Path.cwd()
    output_path = ensure_directory(output_path)

    print("Starting video download...")
    print(f"  URL: {url}")
    print(f"  Output directory: {output_path}")

    ydl_opts = {
        "format": (
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
            "best[height<=1080][ext=mp4]/best"
        ),
        "outtmpl": str(output_path / "%(id)s.%(ext)s"),
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", "zh-CN", "zh-Hans", "zh-Hant"],
        "subtitlesformat": "vtt",
        "writethumbnail": False,
        "quiet": False,
        "no_warnings": False,
        "progress_hooks": [_progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("\nFetching video metadata...")
            info = ydl.extract_info(url, download=False)

            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)
            video_id = info.get("id", "unknown")

            print(f"  Title: {title}")
            print(f"  Duration: {get_video_duration_display(duration)}")
            print(f"  Video ID: {video_id}")

            print("\nDownloading media...")
            info = ydl.extract_info(url, download=True)
            video_path = Path(ydl.prepare_filename(info))

            subtitle_path = find_subtitle_file(video_path)

            if not video_path.exists():
                raise RuntimeError("Video file was not created after download.")

            file_size = video_path.stat().st_size
            print(f"\nVideo download complete: {video_path.name}")
            print(f"  Size: {format_file_size(file_size)}")

            if subtitle_path and subtitle_path.exists():
                print(f"Subtitle download complete: {subtitle_path.name}")
            else:
                print("No preferred subtitle file was found.")
                print("Available subtitles or automatic captions may be missing for this video.")

            return {
                "video_path": str(video_path),
                "subtitle_path": str(subtitle_path) if subtitle_path else None,
                "title": title,
                "duration": duration,
                "file_size": file_size,
                "video_id": video_id,
            }
    except Exception as exc:
        print(f"\nDownload failed: {exc}")
        raise


def _progress_hook(status: dict):
    """Render yt-dlp progress updates."""
    if status["status"] == "downloading":
        downloaded = status.get("downloaded_bytes", 0)
        total = status.get("total_bytes") or status.get("total_bytes_estimate")
        speed = status.get("speed", 0)
        speed_str = f"{format_file_size(speed)}/s" if speed else "N/A"

        if total:
            percent = downloaded / total * 100
            bar_length = 30
            filled = int(bar_length * percent / 100)
            bar = "#" * filled + "-" * (bar_length - filled)
            print(
                f"\r  [{bar}] {percent:.1f}% - "
                f"{format_file_size(downloaded)}/{format_file_size(total)} - {speed_str}",
                end="",
                flush=True,
            )
        else:
            print(
                f"\r  Downloading... {format_file_size(downloaded)} - {speed_str}",
                end="",
                flush=True,
            )
    elif status["status"] == "finished":
        print()


def find_subtitle_file(video_path: Path) -> Path | None:
    """Find the best available subtitle file next to a downloaded video."""
    candidates = [
        video_path.with_suffix(".en.vtt"),
        video_path.parent / f"{video_path.stem}.en.vtt",
        video_path.with_suffix(".zh-CN.vtt"),
        video_path.parent / f"{video_path.stem}.zh-CN.vtt",
        video_path.with_suffix(".zh-Hans.vtt"),
        video_path.parent / f"{video_path.stem}.zh-Hans.vtt",
        video_path.with_suffix(".zh-Hant.vtt"),
        video_path.parent / f"{video_path.stem}.zh-Hant.vtt",
        video_path.with_suffix(".vtt"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <video_url> [output_dir]")
        print()
        print("Examples:")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM work")
        print("  python download_video.py https://example.com/video-page work")
        print()
        print("In Codex, prefer using the configured Conda interpreter.")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = download_video(url, output_dir)
        print("\n" + "=" * 60)
        print("Download result (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(f"\nError: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
