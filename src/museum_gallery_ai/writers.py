from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import TrackEvent


class JsonlEventWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", encoding="utf-8")

    def write(self, event: TrackEvent) -> None:
        self._file.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    def close(self) -> None:
        self._file.close()


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
