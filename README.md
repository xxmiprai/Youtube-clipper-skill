# YouTube Clipper Skill for Codex

AI-assisted video clipping for Codex using `yt-dlp` supported sites. This repository helps Codex download a video, derive semantic chapters from subtitles, cut clips, prepare bilingual subtitles, burn subtitles into video, and generate summary copy.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

English | [简体中文](README.zh-CN.md)

## What Changed

This repository started as a Claude-oriented skill. The Codex adaptation:

- removes Claude-only skill metadata and tool assumptions
- rewrites docs for Windows PowerShell and Codex
- pins the Python examples to the local `codex-conda-python` interpreter
- makes subtitle translation explicit instead of assuming hidden model-side execution
- uses `work/` for intermediate files and `outputs/` for user-facing artifacts

## Requirements

### Python

Use this interpreter on this machine:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe
```

### System tools

- `yt-dlp`
- `ffmpeg`

### Python packages

- `yt-dlp`
- `pysrt`
- `python-dotenv`

Install Python packages with:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe -m pip install -i https://mirrors.sustech.edu.cn/pypi/simple yt-dlp pysrt python-dotenv
```

## Quick Verification

```powershell
yt-dlp --version
ffmpeg -version
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe -c "import yt_dlp, pysrt; print('python deps ok')"
```

## Typical Workflow in Codex

### 1. Download video and subtitles

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\download_video.py <video_url> work
```

### 2. Analyze subtitle content

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\analyze_subtitles.py <subtitle_path>
```

Codex should then read the subtitle text and propose semantic chapters with:

- title
- time range
- summary
- keywords

### 3. Cut a clip

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\clip_video.py <video_path> <start_time> <end_time> <output_mp4>
```

### 4. Extract a subtitle segment

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\extract_subtitle_clip.py <subtitle_vtt> <start_time> <end_time> <output_srt>
```

### 5. Prepare translation payload for Codex

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\translate_subtitles.py <segment_srt> <payload_json>
```

This writes JSON with `translation` placeholders. Codex must fill those values explicitly.

### 6. Write bilingual subtitles

Use the helper function from `scripts/translate_subtitles.py` after translation is complete:

```python
from scripts.translate_subtitles import create_bilingual_subtitles

create_bilingual_subtitles(translated_rows, "outputs\\20260601_120000\\clip\\clip_bilingual.srt")
```

Bilingual subtitle rule:

- one language must always be Chinese
- if the source subtitle is Chinese, generate `Chinese + English`
- if the source subtitle is not Chinese, generate `Source Language + Chinese`
- default to local bilingual generation, even if the site exposes multiple subtitle tracks
- if multiple non-Chinese subtitle tracks exist, choose one primary track for the final bilingual subtitle file and keep the other tracks only as reference input
- prefer the original-language, human-authored subtitle track as the primary track

### 7. Burn subtitles into the video

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\burn_subtitles.py <clip_mp4> <bilingual_srt> <burned_mp4>
```

## Output Layout

Use this convention:

```text
work/
outputs/
  20260601_120000/
    clip-title/
      clip.mp4
      clip_bilingual.srt
      clip_with_subtitles.mp4
      summary.md
```

## Notes

- Semantic chaptering is an AI step, not a deterministic script step.
- Translation is also an AI step. The script only prepares and serializes structured data.
- If FFmpeg lacks subtitle filter support, clipping can still succeed even if burn-in fails.
- Site compatibility is determined by the local `yt-dlp` build, not by this skill alone.
- Bilingual subtitle output must always include Chinese as one side of the pair.

## Files

- [SKILL.md](SKILL.md): Codex skill instructions
- [TECHNICAL_NOTES.md](TECHNICAL_NOTES.md): upstream implementation notes
- [FIXES_AND_IMPROVEMENTS.md](FIXES_AND_IMPROVEMENTS.md): upstream notes and fixes
- [references/](references/): FFmpeg, yt-dlp, and subtitle references
