"""Persistent storage utilities for pairing and device state."""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict


class JsonStore:
    """Thread-safe JSON store for small state payloads."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        with self._lock:
            if not self.path.exists():
                return {}
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

    def save(self, payload: Dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
