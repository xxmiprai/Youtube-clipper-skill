#!/usr/bin/env python3
"""Helpers for Codex-driven subtitle translation workflows."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .utils import seconds_to_time
except ImportError:
    from utils import seconds_to_time


def build_translation_payload(
    subtitles: List[Dict],
    batch_size: int = 20,
    target_lang: str = "Chinese",
) -> Dict:
    """Build a structured translation payload for Codex to translate in batches."""
    batches = [
        subtitles[index:index + batch_size]
        for index in range(0, len(subtitles), batch_size)
    ]
    return {
        "target_language": target_lang,
        "batch_size": batch_size,
        "count": len(subtitles),
        "batches": batches,
    }


def determine_bilingual_languages(source_language: str) -> Dict[str, object]:
    """Return the bilingual subtitle language pairing, always including Chinese."""
    normalized = (source_language or "").strip()
    is_chinese = normalized.lower().startswith("zh")
    return {
        "source_language": normalized,
        "target_language": "en" if is_chinese else "zh-CN",
        "source_is_chinese": is_chinese,
    }


def _subtitle_track_score(track: Dict[str, object]) -> tuple:
    """Return a stable sort key for choosing the primary subtitle track."""
    language = str(track.get("language", "") or "").strip().lower()
    is_original = bool(track.get("is_original"))
    is_human = bool(track.get("is_human"))
    is_official = bool(track.get("is_official"))
    not_auto = not bool(track.get("is_auto"))

    language_priority = {
        "ja": 0,
        "ko": 1,
        "en": 2,
    }

    return (
        0 if is_original else 1,
        0 if is_human else 1,
        0 if is_official else 1,
        0 if not_auto else 1,
        language_priority.get(language, 99),
        language,
    )


def select_primary_subtitle_track(
    subtitle_tracks: List[Dict[str, object]],
) -> Optional[Dict[str, object]]:
    """Pick one primary subtitle track for final bilingual output."""
    if not subtitle_tracks:
        return None

    normalized_tracks = []
    for track in subtitle_tracks:
        normalized_track = dict(track)
        normalized_track["language"] = str(
            normalized_track.get("language", "") or ""
        ).strip()
        normalized_tracks.append(normalized_track)

    return sorted(normalized_tracks, key=_subtitle_track_score)[0]


def plan_bilingual_subtitle_strategy(
    subtitle_tracks: List[Dict[str, object]],
) -> Dict[str, object]:
    """Plan a stable bilingual strategy that always includes Chinese."""
    primary_track = select_primary_subtitle_track(subtitle_tracks)
    if primary_track is None:
        raise ValueError("At least one subtitle track is required")

    language_plan = determine_bilingual_languages(primary_track["language"])
    primary_language = language_plan["source_language"]
    target_language = language_plan["target_language"]

    reference_languages = []
    for track in subtitle_tracks:
        language = str(track.get("language", "") or "").strip()
        if not language or language == primary_language:
            continue
        reference_languages.append(language)

    return {
        "translation_mode": "local",
        "must_include_chinese": True,
        "primary_language": primary_language,
        "target_language": target_language,
        "primary_track": primary_track,
        "reference_languages": reference_languages,
    }


def translate_subtitles_batch(
    subtitles: List[Dict],
    batch_size: int = 20,
    target_lang: str = "Chinese",
) -> List[Dict]:
    """Print a translation payload and return subtitle placeholders."""
    payload = build_translation_payload(
        subtitles,
        batch_size=batch_size,
        target_lang=target_lang,
    )

    print("\nPrepare the following payload for Codex translation:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("\nReturn translated subtitle objects in this shape:")
    print(
        '[{"start": 0.0, "end": 3.5, "text": "original", '
        '"translation": "translated"}]'
    )

    return [
        {
            "start": sub["start"],
            "end": sub["end"],
            "text": sub["text"],
            "translation": "[translation pending]",
        }
        for sub in subtitles
    ]


def write_translated_json(subtitles: List[Dict], output_path: str) -> str:
    """Persist translated subtitle data as UTF-8 JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(subtitles, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(output_path)


def create_bilingual_subtitles(
    subtitles: List[Dict],
    output_path: str,
    english_first: bool = True,
) -> str:
    """Create a bilingual subtitle file in SRT format."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for index, subtitle in enumerate(subtitles, start=1):
            start_time = seconds_to_time(
                subtitle["start"],
                include_hours=True,
                use_comma=True,
            )
            end_time = seconds_to_time(
                subtitle["end"],
                include_hours=True,
                use_comma=True,
            )
            source_text = subtitle["text"]
            translated = subtitle.get("translation", "[translation pending]")

            handle.write(f"{index}\n")
            handle.write(f"{start_time} --> {end_time}\n")
            if english_first:
                handle.write(f"{source_text}\n{translated}\n\n")
            else:
                handle.write(f"{translated}\n{source_text}\n\n")

    return str(output_path)


def load_subtitles_from_srt(srt_path: str) -> List[Dict]:
    """Load subtitles from an SRT file into structured subtitle rows."""
    try:
        import pysrt
    except ImportError:
        print("Error: pysrt not installed")
        print("Install it with the configured Codex Python interpreter.")
        sys.exit(1)

    srt_path = Path(srt_path)
    if not srt_path.exists():
        raise FileNotFoundError(f"SRT file not found: {srt_path}")

    subtitles = []
    subs = pysrt.open(str(srt_path))
    for sub in subs:
        start = (
            sub.start.hours * 3600
            + sub.start.minutes * 60
            + sub.start.seconds
            + sub.start.milliseconds / 1000
        )
        end = (
            sub.end.hours * 3600
            + sub.end.minutes * 60
            + sub.end.seconds
            + sub.end.milliseconds / 1000
        )
        subtitles.append(
            {
                "start": start,
                "end": end,
                "text": sub.text.replace("\n", " "),
            }
        )
    return subtitles


def main():
    """CLI entry point for preparing translation payload JSON."""
    if len(sys.argv) < 2:
        print("Usage: python translate_subtitles.py <subtitle_file> [output_json] [batch_size]")
        print()
        print("Arguments:")
        print("  subtitle_file - source subtitle path in SRT format")
        print("  output_json   - optional JSON payload output path")
        print("  batch_size    - optional batch size, default 20")
        print()
        print("Example:")
        print("  python translate_subtitles.py subtitle.srt")
        print("  python translate_subtitles.py subtitle.srt translation_payload.json")
        print("  python translate_subtitles.py subtitle.srt translation_payload.json 30")
        print()
        print("This command prepares a translation payload for Codex.")
        print("Bilingual subtitle policy: one side must always be Chinese.")
        print("If the source subtitle is Chinese, translate it to English.")
        print("If the source subtitle is not Chinese, translate it to Chinese.")
        print("After Codex returns translated JSON, call create_bilingual_subtitles().")
        sys.exit(1)

    subtitle_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    try:
        subtitles = load_subtitles_from_srt(subtitle_file)
        translated = translate_subtitles_batch(subtitles, batch_size=batch_size)

        if output_file is None:
            subtitle_path = Path(subtitle_file)
            output_file = subtitle_path.parent / f"{subtitle_path.stem}_translation_payload.json"

        write_translated_json(translated, output_file)
        print(f"\nSaved translation placeholder JSON to: {output_file}")
        print("Replace each '[translation pending]' value with a real translation in Codex.")
    except Exception as exc:
        print(f"\nError: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
