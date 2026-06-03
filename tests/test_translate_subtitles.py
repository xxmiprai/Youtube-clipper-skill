import json
import tempfile
import unittest
from pathlib import Path

from scripts.translate_subtitles import (
    build_translation_payload,
    create_bilingual_subtitles,
    write_translated_json,
)


class TranslateSubtitlesTests(unittest.TestCase):
    def test_build_translation_payload_preserves_batch_metadata(self):
        subtitles = [
            {"start": 0.0, "end": 1.5, "text": "Hello"},
            {"start": 1.5, "end": 3.0, "text": "World"},
        ]

        payload = build_translation_payload(subtitles, batch_size=1, target_lang="Chinese")

        self.assertEqual(payload["target_language"], "Chinese")
        self.assertEqual(payload["batch_size"], 1)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["batches"]), 2)
        self.assertEqual(payload["batches"][0][0]["text"], "Hello")

    def test_write_translated_json_and_bilingual_srt(self):
        translated = [
            {"start": 0.0, "end": 1.0, "text": "Hello", "translation": "你好"},
            {"start": 1.0, "end": 2.0, "text": "World", "translation": "世界"},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "translated.json"
            srt_path = Path(tmp) / "bilingual.srt"

            write_translated_json(translated, json_path)
            create_bilingual_subtitles(translated, srt_path)

            saved_json = json.loads(json_path.read_text(encoding="utf-8"))
            srt_text = srt_path.read_text(encoding="utf-8")

        self.assertEqual(saved_json[0]["translation"], "你好")
        self.assertIn("Hello", srt_text)
        self.assertIn("你好", srt_text)

    def test_create_bilingual_subtitles_supports_chinese_first_layout(self):
        translated = [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "你好",
                "translation": "Hello",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            srt_path = Path(tmp) / "bilingual_cn_first.srt"
            create_bilingual_subtitles(translated, srt_path, english_first=False)
            srt_text = srt_path.read_text(encoding="utf-8")

        self.assertIn("你好", srt_text)
        self.assertIn("Hello", srt_text)


if __name__ == "__main__":
    unittest.main()
