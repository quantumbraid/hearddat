"""IP monitoring helper to detect local network changes."""
from __future__ import annotations

import socket
import threading
from typing import Callable


def get_primary_ip() -> str:
    """Best-effort local IP detection using a UDP socket."""

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"


class IPMonitor:
    """Polls for IP changes and triggers callbacks."""

    def __init__(self, interval_s: int, on_change: Callable[[str], None]) -> None:
        self.interval_s = interval_s
        self.on_change = on_change
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_ip = get_primary_ip()

    def start(self) -> None:
        if self._thread:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval_s):
            current_ip = get_primary_ip()
            if current_ip != self._last_ip:
                self._last_ip = current_ip
                self.on_change(current_ip)
