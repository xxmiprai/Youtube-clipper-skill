import subprocess
import tempfile
import unittest
from pathlib import Path


PYTHON = r"D:\software\python\Anaconda3\envs\codex-conda-python\python.exe"


class ClipAndExtractCliTests(unittest.TestCase):
    def test_extract_subtitle_clip_cli_handles_gbk_console_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            vtt_path = tmp_path / "sample.zh-CN.vtt"
            output_path = tmp_path / "segment.srt"
            vtt_path.write_text(
                "WEBVTT\n\n"
                "00:00:00.000 --> 00:00:02.000\n"
                "第一句字幕\n\n"
                "00:00:02.000 --> 00:00:04.000\n"
                "第二句字幕\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    PYTHON,
                    "scripts/extract_subtitle_clip.py",
                    str(vtt_path),
                    "00:00:00",
                    "00:00:03",
                    str(output_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                env={"PYTHONIOENCODING": "gbk", "PATH": ""},
            )

            output_exists = output_path.exists()

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(output_exists)

    def test_clip_video_cli_handles_gbk_console_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "missing.mp4"

            result = subprocess.run(
                [
                    PYTHON,
                    "scripts/clip_video.py",
                    str(tmp_path / "does-not-exist.mp4"),
                    "00:00:00",
                    "00:00:03",
                    str(output_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                env={"PYTHONIOENCODING": "gbk", "PATH": ""},
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Video file not found", result.stdout)


if __name__ == "__main__":
    unittest.main()
