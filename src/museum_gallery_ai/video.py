from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoFrame:
    frame_index: int
    timestamp_seconds: float
    image: object


class VideoSource:
    def __init__(self, source: str | Path) -> None:
        self.source = str(source)
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for video processing. Install requirements.txt.") from exc
        self._cv2 = cv2
        self._capture = cv2.VideoCapture(self.source)
        if not self._capture.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source}")
        self.fps = float(self._capture.get(cv2.CAP_PROP_FPS) or 0.0) or 30.0
        self.width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        self.height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        self._frame_index = 0

    def read(self) -> VideoFrame | None:
        ok, frame = self._capture.read()
        if not ok:
            return None
        timestamp = self._frame_index / self.fps
        video_frame = VideoFrame(self._frame_index, timestamp, frame)
        self._frame_index += 1
        return video_frame

    def close(self) -> None:
        self._capture.release()
