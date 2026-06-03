#!/usr/bin/env python3
"""Clip a video segment with FFmpeg."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Union

try:
    from .utils import (
        format_file_size,
        get_video_duration_display,
        seconds_to_time,
        time_to_seconds,
    )
except ImportError:
    from utils import (
        format_file_size,
        get_video_duration_display,
        seconds_to_time,
        time_to_seconds,
    )


def clip_video(
    video_path: str,
    start_time: Union[str, float],
    end_time: Union[str, float],
    output_path: str,
    ffmpeg_path: str = None,
) -> str:
    """Clip a video segment without re-encoding when possible."""
    video_path = Path(video_path)
    output_path = Path(output_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    start_seconds = (
        time_to_seconds(start_time) if isinstance(start_time, str) else float(start_time)
    )
    end_seconds = (
        time_to_seconds(end_time) if isinstance(end_time, str) else float(end_time)
    )
    if start_seconds >= end_seconds:
        raise ValueError(
            f"Start time ({start_seconds}s) must be before end time ({end_seconds}s)"
        )

    duration = end_seconds - start_seconds

    if ffmpeg_path is None:
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")

    print("Clipping video segment...")
    print(f"Input video: {video_path.name}")
    print(f"Start time: {seconds_to_time(start_seconds)} ({start_seconds}s)")
    print(f"End time: {seconds_to_time(end_seconds)} ({end_seconds}s)")
    print(f"Duration: {get_video_duration_display(duration)}")
    print(f"Output file: {output_path.name}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg_path,
        "-ss",
        str(start_seconds),
        "-i",
        str(video_path),
        "-t",
        str(duration),
        "-c",
        "copy",
        "-y",
        str(output_path),
    ]

    print("Running FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")

    if not output_path.exists():
        raise RuntimeError("Output file was not created")

    output_size = output_path.stat().st_size
    print("Clip completed")
    print(f"Saved clip: {output_path}")
    print(f"Output size: {format_file_size(output_size)}")
    return str(output_path)


def main():
    """CLI entry point."""
    if len(sys.argv) < 5:
        print("Usage: python clip_video.py <video> <start_time> <end_time> <output>")
        print()
        print("Arguments:")
        print("  video      - input video file path")
        print("  start_time - start time in seconds or HH:MM:SS")
        print("  end_time   - end time in seconds or HH:MM:SS")
        print("  output     - output video file path")
        print()
        print("Examples:")
        print("  python clip_video.py input.mp4 0 195 output.mp4")
        print("  python clip_video.py input.mp4 00:00:00 00:03:15 output.mp4")
        sys.exit(1)

    try:
        result_path = clip_video(
            sys.argv[1],
            sys.argv[2],
            sys.argv[3],
            sys.argv[4],
        )
        print(f"Done: {result_path}")
    except Exception as exc:
        print(f"Error: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
