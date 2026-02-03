"""Runtime statistics tracking for the HeardDat PC server."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class StatsSnapshot:
    """Immutable snapshot of runtime stats for settings/diagnostics UI."""

    started_at: float
    last_ingest_at: float | None
    last_egress_at: float | None
    ingest_bytes: int
    ingest_frames: int
    egress_bytes: int
    egress_frames: int

    def as_dict(self) -> Dict[str, object]:
        """Serialize snapshot to a JSON-friendly dict."""

        now = time.time()
        uptime_s = int(now - self.started_at)
        return {
            "started_at": self.started_at,
            "uptime_s": uptime_s,
            "last_ingest_at": self.last_ingest_at,
            "last_egress_at": self.last_egress_at,
            "ingest_bytes": self.ingest_bytes,
            "ingest_frames": self.ingest_frames,
            "egress_bytes": self.egress_bytes,
            "egress_frames": self.egress_frames,
        }


class RuntimeStats:
    """Thread-safe tracker for live server statistics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._last_ingest_at: float | None = None
        self._last_egress_at: float | None = None
        self._ingest_bytes = 0
        self._ingest_frames = 0
        self._egress_bytes = 0
        self._egress_frames = 0

    def record_ingest(self, payload_size: int) -> None:
        """Track audio packets arriving from devices or browser."""

        now = time.time()
        with self._lock:
            self._last_ingest_at = now
            self._ingest_bytes += payload_size
            self._ingest_frames += 1

    def record_egress(self, payload_size: int) -> None:
        """Track audio packets leaving the server to clients."""

        now = time.time()
        with self._lock:
            self._last_egress_at = now
            self._egress_bytes += payload_size
            self._egress_frames += 1

    def snapshot(self) -> StatsSnapshot:
        """Return a consistent snapshot for UI rendering."""

        with self._lock:
            return StatsSnapshot(
                started_at=self._started_at,
                last_ingest_at=self._last_ingest_at,
                last_egress_at=self._last_egress_at,
                ingest_bytes=self._ingest_bytes,
                ingest_frames=self._ingest_frames,
                egress_bytes=self._egress_bytes,
                egress_frames=self._egress_frames,
            )
