from pathlib import Path
import unittest

from museum_gallery_ai.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_demo_config_is_camera_aware(self):
        config = load_config(Path("configs/demo.yaml"))

        self.assertEqual(config.camera.camera_id, "camera_1")
        self.assertEqual(config.camera.gallery_id, "gallery_1")
        self.assertEqual(config.zones[0].camera_id, "camera_1")
        self.assertEqual(config.lines[0].gallery_id, "gallery_1")

    def test_detector_iou_defaults_to_0_4(self):
        config = load_config(Path("configs/demo.yaml"))
        self.assertEqual(config.detector.iou, 0.4)


if __name__ == "__main__":
    unittest.main()
