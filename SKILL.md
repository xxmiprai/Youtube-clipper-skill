---
name: youtube-clipper
description: Use when the user wants to download a video from a yt-dlp-supported site, identify highlight chapters, cut clips, prepare bilingual subtitles, burn subtitles into video, or package short-form video assets in Codex
---

# YouTube Clipper

Use this skill when the user wants Codex to turn a video from a `yt-dlp`-supported site into one or more reusable clips with subtitles, summaries, or burn-in output.

## Environment

Use this Python interpreter on this machine:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe
```

Before doing real work, verify:

```powershell
yt-dlp --version
ffmpeg -version
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe -c "import yt_dlp, pysrt; print('python deps ok')"
```

If a dependency is missing and installation is required, ask for permission before installing it.

## Workflow

### 1. Download the source video

Run:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\download_video.py <video_url> work
```

Expected outputs:

- video file in `work/`
- subtitle file in `work/`, usually `.en.vtt`

Supported sites depend on the local `yt-dlp` build. This is not limited to YouTube.

### 2. Analyze subtitles into semantic chapters

Run:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\analyze_subtitles.py <subtitle_path>
```

Then do the chaptering in-model:

- read the subtitle content
- identify natural topic changes
- produce 2-5 minute chapters when possible
- give each chapter a title, time range, short summary, and keywords

Do not split mechanically by fixed time. The point of this skill is semantic chaptering.

### 3. Let the user choose clips and outputs

Confirm:

- which chapter numbers to clip
- whether bilingual subtitles are needed
- whether subtitle burn-in is needed
- whether summary markdown is needed

### 4. Produce clip artifacts

For each chosen chapter:

Clip video:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\clip_video.py <video_path> <start_time> <end_time> <output_mp4>
```

Extract subtitle segment:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\extract_subtitle_clip.py <subtitle_vtt> <start_time> <end_time> <output_srt>
```

Prepare translation payload:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\translate_subtitles.py <segment_srt> <payload_json>
```

Then translate in-model. The script prepares JSON placeholders; Codex must fill the `translation` values explicitly.

After translation, use `scripts.translate_subtitles.create_bilingual_subtitles(...)` or the existing subtitle merge path to write the bilingual `.srt`.

Bilingual subtitle rule:

- one side must always be Chinese
- Chinese source subtitles should become `Chinese + English`
- non-Chinese source subtitles should become `Source Language + Chinese`
- default to local bilingual generation even when the site exposes multiple subtitle tracks
- if multiple non-Chinese subtitle tracks exist, choose one primary track for the final bilingual output and treat the others as reference material only
- prefer the original-language, human-authored subtitle track as the primary track when multiple candidates exist

If burn-in is requested:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\burn_subtitles.py <clip_mp4> <bilingual_srt> <burned_mp4>
```

If summary output is requested:

```powershell
D:\software\python\Anaconda3\envs\codex-conda-python\python.exe scripts\generate_summary.py <chapter_info>
```

## Output Convention

Use:

- `work/` for intermediate files
- `outputs/<timestamp>/` for user-facing results

Keep each clip in its own folder under the run output directory when there are multiple chapters.

## AI vs Script Responsibilities

Codex does:

- semantic chaptering
- subtitle translation text
- clip titles and summaries

Scripts do:

- download
- clipping
- subtitle extraction and serialization
- subtitle burn-in
- file writing

## Failure Handling

- If subtitles are unavailable, say so clearly and explain whether auto captions were attempted.
- If FFmpeg lacks subtitle filter support, continue with non-burned outputs if possible.
- If some outputs succeed and others fail, keep completed artifacts and report the exact failed step.

## Verification

Before claiming the adaptation or a clip run succeeded, run the relevant commands and inspect the output.
