import subprocess
import tempfile
import unittest
from pathlib import Path


class AnalyzeSubtitlesTests(unittest.TestCase):
    def test_cli_handles_gbk_console_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            vtt_path = Path(tmp) / "sample.zh-CN.vtt"
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
                    r"D:\software\python\Anaconda3\envs\codex-conda-python\python.exe",
                    "scripts/analyze_subtitles.py",
                    str(vtt_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                env={"PYTHONIOENCODING": "gbk", "PATH": ""},
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Analysis summary", result.stdout)


if __name__ == "__main__":
    unittest.main()
