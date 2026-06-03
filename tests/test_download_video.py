import tempfile
import unittest
from pathlib import Path

from scripts.download_video import find_subtitle_file


class DownloadVideoTests(unittest.TestCase):
    def test_find_subtitle_file_prefers_english_then_chinese_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            video_path = Path(tmp) / "sample.mp4"
            video_path.write_bytes(b"video")

            zh_cn = Path(tmp) / "sample.zh-CN.vtt"
            zh_cn.write_text("WEBVTT", encoding="utf-8")

            found = find_subtitle_file(video_path)
            self.assertEqual(found, zh_cn)

            en_vtt = Path(tmp) / "sample.en.vtt"
            en_vtt.write_text("WEBVTT", encoding="utf-8")

            found = find_subtitle_file(video_path)
            self.assertEqual(found, en_vtt)

    def test_find_subtitle_file_accepts_plain_vtt_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            video_path = Path(tmp) / "sample.mp4"
            video_path.write_bytes(b"video")

            plain_vtt = Path(tmp) / "sample.vtt"
            plain_vtt.write_text("WEBVTT", encoding="utf-8")

            found = find_subtitle_file(video_path)
            self.assertEqual(found, plain_vtt)


if __name__ == "__main__":
    unittest.main()
