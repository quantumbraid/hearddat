"""LAN discovery helpers for mobile devices."""
from __future__ import annotations

import json
import socket
import threading
from typing import Dict

DISCOVERY_PORT = 33333
DISCOVERY_MAGIC = "HEARDDAT_DISCOVERY"


class DiscoveryResponder:
    """Responds to UDP broadcast discovery requests."""

    def __init__(self, response_payload: Dict[str, str]) -> None:
        self.response_payload = response_payload
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

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
        self._thread = None
        self._stop_event = threading.Event()

    def _run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)
            sock.bind(("", DISCOVERY_PORT))
            while not self._stop_event.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                except socket.timeout:
                    continue
                if data.decode("utf-8", errors="ignore") != DISCOVERY_MAGIC:
                    continue
                payload = json.dumps(self.response_payload).encode("utf-8")
                sock.sendto(payload, addr)
