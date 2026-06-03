import tempfile
import unittest
from pathlib import Path

from scripts.burn_subtitles import (
    build_burn_command,
    build_subtitle_filter,
    prepare_output_path,
)


class BurnSubtitlesTests(unittest.TestCase):
    def test_build_subtitle_filter_escapes_windows_path(self):
        subtitle_filter = build_subtitle_filter(
            r"C:\Users\xxmip\AppData\Local\Temp\youtube_clipper_x\subtitle.srt",
            font_size=24,
            margin_v=30,
        )

        self.assertIn("subtitles='C\\:/Users/xxmip/AppData/Local/Temp/youtube_clipper_x/subtitle.srt'", subtitle_filter)
        self.assertIn("FontSize=24", subtitle_filter)
        self.assertIn("MarginV=30", subtitle_filter)

    def test_build_burn_command_uses_player_friendly_mp4_settings(self):
        command = build_burn_command(
            ffmpeg_path="ffmpeg",
            input_video="video.mp4",
            subtitle_filter="subtitles='clip.srt'",
            output_video="output.mp4",
        )

        self.assertIn("-movflags", command)
        self.assertIn("+faststart", command)
        self.assertIn("-c:v", command)
        self.assertIn("libx264", command)
        self.assertIn("-pix_fmt", command)
        self.assertIn("yuv420p", command)
        self.assertIn("-c:a", command)
        self.assertIn("aac", command)

    def test_prepare_output_path_creates_destination_file_in_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "output.mp4"
            prepared = prepare_output_path(str(target))

            self.assertEqual(Path(prepared), target)
            self.assertTrue(target.parent.exists())


if __name__ == "__main__":
    unittest.main()
