import argparse
import unittest

from museum_gallery_ai.cli import _apply_process_overrides
from museum_gallery_ai.models import CameraConfig, DetectorConfig, PipelineConfig, ProcessingConfig


class CliOverrideTests(unittest.TestCase):
    def test_process_overrides_keep_original_config_immutable(self):
        config = PipelineConfig(
            camera=CameraConfig(camera_id="camera_1", gallery_id="gallery_1"),
            detector=DetectorConfig(image_size=1280),
            processing=ProcessingConfig(frame_stride=1, max_frames=None, write_overlay=True),
        )
        args = argparse.Namespace(max_frames=25, frame_stride=3, image_size=640, no_overlay=True)

        overridden = _apply_process_overrides(config, args)

        self.assertEqual(overridden.processing.max_frames, 25)
        self.assertEqual(overridden.processing.frame_stride, 3)
        self.assertFalse(overridden.processing.write_overlay)
        self.assertEqual(overridden.detector.image_size, 640)
        self.assertIsNone(config.processing.max_frames)
        self.assertEqual(config.processing.frame_stride, 1)
        self.assertTrue(config.processing.write_overlay)
        self.assertEqual(config.detector.image_size, 1280)


if __name__ == "__main__":
    unittest.main()
