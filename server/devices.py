"""Device connection management."""
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Dict

from fastapi import WebSocket


@dataclass
class DeviceConnection:
    device_id: str
    websocket: WebSocket
    loop: asyncio.AbstractEventLoop


class DeviceHub:
    """Tracks active device sockets for notifications and reauth prompts."""

    def __init__(self) -> None:
        self._devices: Dict[str, DeviceConnection] = {}
        self._lock = threading.Lock()

    async def register(self, device_id: str, websocket: WebSocket) -> None:
        with self._lock:
            self._devices[device_id] = DeviceConnection(
                device_id=device_id,
                websocket=websocket,
                loop=asyncio.get_running_loop(),
            )

    async def unregister(self, device_id: str) -> None:
        with self._lock:
            self._devices.pop(device_id, None)

    async def notify_all(self, payload: dict) -> None:
        with self._lock:
            devices = list(self._devices.values())
        for device in devices:
            await device.websocket.send_json(payload)

    async def notify_device(self, device_id: str, payload: dict) -> None:
        with self._lock:
            device = self._devices.get(device_id)
        if device:
            await device.websocket.send_json(payload)

    def notify_all_threadsafe(self, payload: dict) -> None:
        """Send a notification from a non-async thread."""

        with self._lock:
            devices = list(self._devices.values())
        for device in devices:
            asyncio.run_coroutine_threadsafe(
                device.websocket.send_json(payload),
                device.loop,
            )

    def notify_device_threadsafe(self, device_id: str, payload: dict) -> None:
        """Send a notification to a single device from a non-async thread."""

        with self._lock:
            device = self._devices.get(device_id)
        if not device:
            return
        asyncio.run_coroutine_threadsafe(
            device.websocket.send_json(payload),
            device.loop,
        )

    async def count(self) -> int:
        """Return the number of connected devices."""

        with self._lock:
            return len(self._devices)
