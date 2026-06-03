# 适用于 Codex 的 YouTube Clipper Skill

这是一个给 Codex 用的通用视频剪辑 skill，基于 `yt-dlp` 支持的网站工作。它帮助 Codex 下载视频、根据字幕做语义分章、裁剪片段、准备双语字幕、把字幕烧录进视频，并生成摘要文案。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[English](README.md) | 简体中文

## 上游来源

这个仓库是从 [op7418/Youtube-clipper-skill](https://github.com/op7418/Youtube-clipper-skill) 克隆后继续改造而来，当前版本主要面向 Codex 工作流和本地环境适配。

## 安装方式

最省事的安装方式，是直接使用这个目录里的打包产物：

```text
outputs\youtube-clipper-codex-package
```

进入这个目录后，在 PowerShell 里执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_to_codex_skills.ps1
```

脚本会把 skill 安装到：

```text
%USERPROFILE%\.codex\skills\youtube-clipper
```

如果你想手动安装，就把：

```text
outputs\youtube-clipper-codex-package\youtube-clipper
```

复制到：

```text
%USERPROFILE%\.codex\skills\
```

安装完成后，至少应当确认这个文件存在：

```text
%USERPROFILE%\.codex\skills\youtube-clipper\SKILL.md
```

打包目录里也附带了一份独立安装说明：

```text
outputs\youtube-clipper-codex-package\INSTALL.md
```

## 这次改造的重点

这个仓库原本是偏 Claude 的 skill，现在已经改成更适合 Codex 使用的版本：

- 去掉了 Claude 专属的 skill 元数据和工具假设
- 文档统一成 Windows PowerShell + Codex 的语境
- Python 示例统一改成不依赖本机路径的通用写法
- 字幕翻译不再假设“模型会自动补完”，而是改成显式 JSON 流程
- 中间文件放在 `work/`，用户交付结果放在 `outputs/`

## 环境要求

### Python

请使用你自己的 Python 环境：

```powershell
python
```

### 系统工具

- `yt-dlp`
- `ffmpeg`

### Python 包

- `yt-dlp`
- `pysrt`
- `python-dotenv`

安装命令：

```powershell
python -m pip install yt-dlp pysrt python-dotenv
```

## 快速检查

```powershell
yt-dlp --version
ffmpeg -version
python -c "import yt_dlp, pysrt; print('python deps ok')"
```

## 在 Codex 里如何使用这个 Skill

安装完成后，你可以直接在 Codex 里用自然语言下达任务，只要描述目标并附上视频链接即可触发这个 skill。

### 指令模板

可以按这个结构来表达：

```text
帮我<目标>这个视频：
<video_url>
```

### 常见示例

下载视频并提取可剪辑片段：

```text
帮我下载这个视频，并提取可剪辑片段：
https://example.com/video
```

下载视频、给出语义分章并生成双语字幕：

```text
帮我下载这个视频，给出语义分章，并生成双语字幕：
https://example.com/video
```

按指定时间范围裁出一个片段：

```text
帮我把这个视频裁成 00:30 到 02:10 的片段：
https://example.com/video
```

把双语字幕烧录进最终视频：

```text
帮我给这个视频的成品片段烧录双语字幕：
https://example.com/video
```

### Skill 会自动做什么

根据你的指令和字幕可用情况，这个 skill 通常会：

- 从 `yt-dlp` 支持的网站下载视频和可用字幕
- 分析字幕内容并给出语义上的可剪辑片段候选
- 裁剪你指定的时间段或推荐片段
- 生成始终包含中文的双语字幕
- 在 FFmpeg 支持字幕滤镜时，把字幕烧录进输出视频

## 在 Codex 里的典型流程

### 1. 下载视频和字幕

```powershell
python scripts\download_video.py <video_url> work
```

### 2. 分析字幕内容

```powershell
python scripts\analyze_subtitles.py <subtitle_path>
```

然后由 Codex 在对话里完成语义分章，给出：

- 标题
- 时间范围
- 摘要
- 关键词

### 3. 裁剪视频片段

```powershell
python scripts\clip_video.py <video_path> <start_time> <end_time> <output_mp4>
```

### 4. 提取对应字幕片段

```powershell
python scripts\extract_subtitle_clip.py <subtitle_vtt> <start_time> <end_time> <output_srt>
```

### 5. 为 Codex 生成翻译载荷

```powershell
python scripts\translate_subtitles.py <segment_srt> <payload_json>
```

这个命令会生成带 `translation` 占位值的 JSON，之后由 Codex 显式补全翻译内容。

### 6. 生成双语字幕

翻译完成后，可以调用 `scripts/translate_subtitles.py` 里的辅助函数：

```python
from scripts.translate_subtitles import create_bilingual_subtitles

create_bilingual_subtitles(translated_rows, "outputs\\20260601_120000\\clip\\clip_bilingual.srt")
```

双语字幕规则：

- 双语字幕里必须有一侧是中文
- 如果原始字幕就是中文，则生成 `中文 + 英文`
- 如果原始字幕不是中文，则生成 `原始语言 + 中文`
- 默认走本地双语生成方案，即使站点本身提供了多条字幕轨
- 如果存在多条非中文字幕轨，只选一条主字幕进入最终双语字幕成品，其他字幕轨仅作为参考输入
- 多条候选字幕轨并存时，优先选择“更接近原始语音、且为人工字幕”的那一条作为主字幕

### 7. 烧录字幕到视频

```powershell
python scripts\burn_subtitles.py <clip_mp4> <bilingual_srt> <burned_mp4>
```

## 输出目录约定

建议使用：

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

## 说明

- 语义分章是模型步骤，不是纯脚本步骤。
- 字幕翻译也是模型步骤，脚本只负责准备和写出结构化数据。
- 如果 FFmpeg 不支持字幕滤镜，视频裁剪仍然可能成功，只是烧录字幕会失败。
- 站点是否兼容取决于本机 `yt-dlp` 的支持范围，不只限于 YouTube。
- 双语字幕输出必须始终包含中文。

## 相关文件

- [SKILL.md](SKILL.md)：Codex skill 使用说明
- [TECHNICAL_NOTES.md](TECHNICAL_NOTES.md)：上游实现说明
- [FIXES_AND_IMPROVEMENTS.md](FIXES_AND_IMPROVEMENTS.md)：上游修复记录
- [references/](references/)：FFmpeg、yt-dlp、字幕格式参考
