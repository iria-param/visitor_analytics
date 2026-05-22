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
        args = argparse.Namespace(max_frames=25, frame_stride=3, image_size=640, no_overlay=True, overlay=False, detector_iou=None)

        overridden = _apply_process_overrides(config, args)

        self.assertEqual(overridden.processing.max_frames, 25)
        self.assertEqual(overridden.processing.frame_stride, 3)
        self.assertFalse(overridden.processing.write_overlay)
        self.assertEqual(overridden.detector.image_size, 640)
        self.assertIsNone(config.processing.max_frames)
        self.assertEqual(config.processing.frame_stride, 1)
        self.assertTrue(config.processing.write_overlay)
        self.assertEqual(config.detector.image_size, 1280)

    def test_overlay_override_can_force_overlay_on(self):
        config = PipelineConfig(
            camera=CameraConfig(camera_id="camera_1", gallery_id="gallery_1"),
            detector=DetectorConfig(),
            processing=ProcessingConfig(write_overlay=False),
        )
        args = argparse.Namespace(max_frames=None, frame_stride=None, image_size=None, no_overlay=False, overlay=True, detector_iou=None)

        overridden = _apply_process_overrides(config, args)

        self.assertTrue(overridden.processing.write_overlay)

    def test_overlay_flags_are_mutually_exclusive(self):
        config = PipelineConfig(
            camera=CameraConfig(camera_id="camera_1", gallery_id="gallery_1"),
            detector=DetectorConfig(),
            processing=ProcessingConfig(),
        )
        args = argparse.Namespace(max_frames=None, frame_stride=None, image_size=None, no_overlay=True, overlay=True, detector_iou=None)

        with self.assertRaises(ValueError):
            _apply_process_overrides(config, args)

    def test_detector_iou_override_applies_to_detector_config(self):
        config = PipelineConfig(
            camera=CameraConfig(camera_id="camera_1", gallery_id="gallery_1"),
            detector=DetectorConfig(),
            processing=ProcessingConfig(),
        )
        args = argparse.Namespace(max_frames=None, frame_stride=None, image_size=None, no_overlay=False, overlay=False, detector_iou=0.5)

        overridden = _apply_process_overrides(config, args)

        self.assertEqual(overridden.detector.iou, 0.5)
        self.assertEqual(config.detector.iou, 0.4)

    def test_detector_iou_override_rejects_out_of_range(self):
        config = PipelineConfig(
            camera=CameraConfig(camera_id="camera_1", gallery_id="gallery_1"),
            detector=DetectorConfig(),
            processing=ProcessingConfig(),
        )
        args = argparse.Namespace(max_frames=None, frame_stride=None, image_size=None, no_overlay=False, overlay=False, detector_iou=1.5)

        with self.assertRaises(ValueError):
            _apply_process_overrides(config, args)


if __name__ == "__main__":
    unittest.main()
