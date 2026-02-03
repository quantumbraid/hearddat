"""Audio quality presets and state for the settings UI."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class AudioQualityPreset:
    """Named audio quality preset for client guidance."""

    label: str
    sample_rate: int
    bitrate_kbps: int

    def as_dict(self) -> Dict[str, object]:
        """Return preset in a JSON-friendly format."""

        return {
            "label": self.label,
            "sample_rate": self.sample_rate,
            "bitrate_kbps": self.bitrate_kbps,
        }


class AudioQualityState:
    """Stateful selector for audio quality presets."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._presets: List[AudioQualityPreset] = [
            AudioQualityPreset(label="Low", sample_rate=16000, bitrate_kbps=16),
            AudioQualityPreset(label="Balanced", sample_rate=16000, bitrate_kbps=24),
            AudioQualityPreset(label="High", sample_rate=24000, bitrate_kbps=32),
        ]
        self._index = 1

    def current(self) -> AudioQualityPreset:
        """Return the currently selected audio preset."""

        with self._lock:
            return self._presets[self._index]

    def increase(self) -> AudioQualityPreset:
        """Move to the next higher quality preset."""

        with self._lock:
            if self._index < len(self._presets) - 1:
                self._index += 1
            return self._presets[self._index]

    def decrease(self) -> AudioQualityPreset:
        """Move to the next lower quality preset."""

        with self._lock:
            if self._index > 0:
                self._index -= 1
            return self._presets[self._index]

    def snapshot(self) -> Dict[str, object]:
        """Provide the current preset plus available choices."""

        with self._lock:
            return {
                "current": self._presets[self._index].as_dict(),
                "presets": [preset.as_dict() for preset in self._presets],
            }
