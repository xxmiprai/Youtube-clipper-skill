import tempfile
import unittest
from pathlib import Path

from scripts import utils


class UtilsWorkspaceTests(unittest.TestCase):
    def test_create_output_dir_uses_timestamped_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = utils.create_output_dir(tmp)
            self.assertTrue(Path(output_dir).exists())
            self.assertEqual(Path(output_dir).parent, Path(tmp))
            self.assertRegex(Path(output_dir).name, r"^\d{8}_\d{6}$")

    def test_create_workspace_output_dir_defaults_to_outputs_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = utils.create_workspace_output_dir(base_workspace=tmp)
            output_path = Path(output_dir)
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.parent.parent, Path(tmp))
            self.assertEqual(output_path.parent.name, "outputs")

    def test_validate_url_accepts_generic_https_video_pages(self):
        self.assertTrue(utils.validate_url("https://www.youtube.com/watch?v=Ckt1cj0xjRM"))
        self.assertTrue(utils.validate_url("https://www.pornhub.com/view_video.php?viewkey=ph5f1234567890"))
        self.assertTrue(utils.validate_url("https://example.com/videos/clip-123"))
        self.assertFalse(utils.validate_url("ftp://example.com/video.mp4"))
        self.assertFalse(utils.validate_url("invalid_url"))


if __name__ == "__main__":
    unittest.main()
