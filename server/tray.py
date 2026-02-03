"""Taskbar tray integration for the desktop server."""
from __future__ import annotations

import threading
from typing import Callable, List

import pystray
from PIL import Image, ImageDraw


class TrayApp:
    """Wrapper around pystray with menu callbacks."""

    def __init__(
        self,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
        on_restart: Callable[[], None],
        on_reconnect: Callable[[], None],
        on_clear_restart: Callable[[], None],
        list_devices: Callable[[], List[str]],
        on_device_select: Callable[[str], None],
    ) -> None:
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_restart = on_restart
        self._on_reconnect = on_reconnect
        self._on_clear_restart = on_clear_restart
        self._list_devices = list_devices
        self._on_device_select = on_device_select
        self._icon = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the tray icon in a background thread."""

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    def _run(self) -> None:
        image = Image.new("RGB", (64, 64), color="black")
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill="white")

        def device_items() -> List[pystray.MenuItem]:
            items = []
            for device_id in self._list_devices():
                items.append(
                    pystray.MenuItem(
                        device_id,
                        lambda _, d=device_id: self._on_device_select(d),
                    )
                )
            if not items:
                items.append(pystray.MenuItem("No devices", None, enabled=False))
            return items

        menu = pystray.Menu(
            pystray.MenuItem("Start server", lambda _: self._on_start()),
            pystray.MenuItem("Stop server", lambda _: self._on_stop()),
            pystray.MenuItem("Restart server", lambda _: self._on_restart()),
            pystray.MenuItem("Reconnect to device", lambda _: self._on_reconnect()),
            pystray.MenuItem(
                "Devices", pystray.Menu(*device_items()),
            ),
            pystray.MenuItem(
                "Restart service (clear temp)",
                lambda _: self._on_clear_restart(),
            ),
        )
        self._icon = pystray.Icon("hearddat", image, "HeardDat", menu)
        self._icon.run()
