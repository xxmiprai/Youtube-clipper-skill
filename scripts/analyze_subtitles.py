#!/usr/bin/env python3
"""Analyze VTT subtitle files and prepare structured chaptering data."""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

try:
    from .utils import get_video_duration_display, seconds_to_time, time_to_seconds
except ImportError:
    from utils import get_video_duration_display, seconds_to_time, time_to_seconds


def parse_vtt(vtt_path: str) -> List[Dict]:
    """Parse a VTT subtitle file into subtitle rows."""
    vtt_path = Path(vtt_path)
    if not vtt_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {vtt_path}")

    print(f"Parsing subtitle file: {vtt_path.name}")

    content = vtt_path.read_text(encoding="utf-8")
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    content = re.sub(r"STYLE.*?-->", "", content, flags=re.DOTALL)

    subtitles = []
    for block in content.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        timestamp_line = None
        text_lines = []
        for line in lines:
            if "-->" in line:
                timestamp_line = line
            elif line and not line.isdigit():
                text_lines.append(line)

        if not timestamp_line or not text_lines:
            continue

        try:
            timestamp_line = re.sub(r"align:.*|position:.*", "", timestamp_line).strip()
            start_str, end_str = [part.strip() for part in timestamp_line.split("-->")]
            start = time_to_seconds(start_str)
            end = time_to_seconds(end_str)
            text = re.sub(r"<[^>]+>", "", " ".join(text_lines)).strip()
            if text:
                subtitles.append({"start": start, "end": end, "text": text})
        except Exception:
            continue

    print(f"Found {len(subtitles)} subtitle rows")
    if subtitles:
        print(f"Total duration: {get_video_duration_display(subtitles[-1]['end'])}")
    return subtitles


def prepare_analysis_data(subtitles: List[Dict], target_chapter_duration: int = 180) -> Dict:
    """Prepare structured analysis data for Codex-driven semantic chaptering."""
    if not subtitles:
        raise ValueError("No subtitles to analyze")

    print("\nPreparing analysis data...")

    full_text_lines = []
    for subtitle in subtitles:
        time_str = seconds_to_time(subtitle["start"], include_hours=True, use_comma=False)
        full_text_lines.append(f"[{time_str}] {subtitle['text']}")

    total_duration = subtitles[-1]["end"]
    estimated_chapters = max(1, int(total_duration / target_chapter_duration))

    print(f"Subtitle count: {len(subtitles)}")
    print(f"Target chapter duration: {target_chapter_duration} seconds")
    print(f"Estimated chapters: {estimated_chapters}")

    return {
        "subtitle_text": "\n".join(full_text_lines),
        "total_duration": total_duration,
        "subtitle_count": len(subtitles),
        "target_chapter_duration": target_chapter_duration,
        "estimated_chapters": estimated_chapters,
        "subtitles_raw": subtitles,
    }


def save_analysis_data(data: Dict, output_path: str):
    """Save analysis data to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved analysis data: {output_path}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_subtitles.py <vtt_file> [target_duration] [output_json]")
        print()
        print("Arguments:")
        print("  vtt_file         - input subtitle file in VTT format")
        print("  target_duration  - target chapter duration in seconds, default 180")
        print("  output_json      - optional output path for structured analysis JSON")
        print()
        print("Examples:")
        print("  python analyze_subtitles.py video.vtt")
        print("  python analyze_subtitles.py video.vtt 240")
        print("  python analyze_subtitles.py video.vtt 240 analysis.json")
        sys.exit(1)

    vtt_file = sys.argv[1]
    target_duration = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    output_json = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        subtitles = parse_vtt(vtt_file)
        if not subtitles:
            print("No valid subtitle rows were found.")
            sys.exit(1)

        analysis_data = prepare_analysis_data(subtitles, target_duration)

        print("\n" + "=" * 60)
        print("Subtitle preview (first 50 lines):")
        print("=" * 60)
        lines = analysis_data["subtitle_text"].split("\n")
        preview_lines = lines[:50]
        print("\n".join(preview_lines))
        if len(lines) > 50:
            print(f"\n... ({len(lines) - 50} more lines)")

        if output_json:
            save_analysis_data(analysis_data, output_json)

        print("\n" + "=" * 60)
        print("Analysis summary")
        print("=" * 60)
        print(
            json.dumps(
                {
                    "total_duration": analysis_data["total_duration"],
                    "total_duration_display": get_video_duration_display(analysis_data["total_duration"]),
                    "subtitle_count": analysis_data["subtitle_count"],
                    "target_chapter_duration": analysis_data["target_chapter_duration"],
                    "estimated_chapters": analysis_data["estimated_chapters"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )

        print("\nYou can now use the subtitle text above for semantic clip selection.")
    except Exception as exc:
        print(f"\nError: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
