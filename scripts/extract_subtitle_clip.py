#!/usr/bin/env python3
"""Extract a subtitle segment from a VTT file and save it as SRT."""

import re
import sys
from datetime import timedelta
from pathlib import Path
from typing import Dict, List


def parse_vtt_time(time_str: str) -> float:
    """Convert VTT timestamps to seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    return float(parts[0])


def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format."""
    td = timedelta(seconds=seconds)
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    secs = int(total_seconds % 60)
    millis = int((total_seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def parse_vtt_blocks(vtt_text: str) -> List[Dict[str, object]]:
    """Parse VTT text into structured subtitle rows."""
    cleaned = re.sub(r"^WEBVTT.*?\n\n", "", vtt_text, flags=re.DOTALL)
    subtitles = []

    for block in cleaned.strip().split("\n\n"):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        timestamp_line = next((line for line in lines if "-->" in line), None)
        if not timestamp_line:
            continue

        text_lines = [line for line in lines if "-->" not in line and not line.isdigit()]
        if not text_lines:
            continue

        start_text, end_text = [part.strip() for part in timestamp_line.split("-->")]
        start_text = start_text.split()[0]
        end_text = end_text.split()[0]

        subtitles.append(
            {
                "start": parse_vtt_time(start_text),
                "end": parse_vtt_time(end_text),
                "text": " ".join(text_lines),
            }
        )

    return subtitles


def extract_subtitle_clip(
    vtt_file: str,
    start_time: str,
    end_time: str,
    output_file: str,
) -> List[Dict[str, object]]:
    """Extract subtitles that fall within a time range and write them as SRT."""
    vtt_path = Path(vtt_file)
    output_path = Path(output_file)

    if not vtt_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {vtt_path}")

    start_seconds = parse_vtt_time(start_time)
    end_seconds = parse_vtt_time(end_time)
    if start_seconds >= end_seconds:
        raise ValueError("Start time must be before end time")

    print("Extracting subtitle segment...")
    print(f"Input subtitle: {vtt_path}")
    print(f"Time range: {start_time} - {end_time}")

    subtitles = parse_vtt_blocks(vtt_path.read_text(encoding="utf-8"))
    segment_rows = []
    for subtitle in subtitles:
        sub_start = subtitle["start"]
        sub_end = subtitle["end"]
        if sub_start >= start_seconds and sub_end <= end_seconds:
            segment_rows.append(
                {
                    "start": sub_start - start_seconds,
                    "end": sub_end - start_seconds,
                    "text": subtitle["text"],
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for index, subtitle in enumerate(segment_rows, start=1):
            handle.write(f"{index}\n")
            handle.write(
                f"{format_srt_time(subtitle['start'])} --> "
                f"{format_srt_time(subtitle['end'])}\n"
            )
            handle.write(f"{subtitle['text']}\n\n")

    print(f"Extracted {len(segment_rows)} subtitle rows")
    print(f"Saved subtitle segment: {output_path}")
    return segment_rows


def main():
    """CLI entry point."""
    if len(sys.argv) != 5:
        print(
            "Usage: python extract_subtitle_clip.py "
            "<vtt_file> <start_time> <end_time> <output_file>"
        )
        print(
            "Example: python extract_subtitle_clip.py "
            "input.vtt 00:05:47 00:09:19 output.srt"
        )
        sys.exit(1)

    try:
        extract_subtitle_clip(
            sys.argv[1],
            sys.argv[2],
            sys.argv[3],
            sys.argv[4],
        )
    except Exception as exc:
        print(f"Error: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
