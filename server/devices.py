"""Device connection management."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict

from fastapi import WebSocket


@dataclass
class DeviceConnection:
    device_id: str
    websocket: WebSocket


class DeviceHub:
    """Tracks active device sockets for notifications and reauth prompts."""

    def __init__(self) -> None:
        self._devices: Dict[str, DeviceConnection] = {}
        self._lock = asyncio.Lock()

    async def register(self, device_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._devices[device_id] = DeviceConnection(device_id=device_id, websocket=websocket)

    async def unregister(self, device_id: str) -> None:
        async with self._lock:
            self._devices.pop(device_id, None)

    async def notify_all(self, payload: dict) -> None:
        async with self._lock:
            devices = list(self._devices.values())
        for device in devices:
            await device.websocket.send_json(payload)

    async def notify_device(self, device_id: str, payload: dict) -> None:
        async with self._lock:
            device = self._devices.get(device_id)
        if device:
            await device.websocket.send_json(payload)

    async def count(self) -> int:
        """Return the number of connected devices."""

        async with self._lock:
            return len(self._devices)
