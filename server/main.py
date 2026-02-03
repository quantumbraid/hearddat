"""Entry point for running the PC server."""
from __future__ import annotations

import argparse
import asyncio
import logging
import threading
import time

import uvicorn

from .audio import AudioRouter
from .config import ServerConfig
from .devices import DeviceHub
from .discovery import DiscoveryResponder
from .ip_monitor import IPMonitor
from .pairing import PairingRegistry
from .quality import AudioQualityState
from .storage import JsonStore
from .stats import RuntimeStats
from .tray import TrayApp
from .web import build_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerRuntime:
    """Holds running server components for lifecycle management."""

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self._router = AudioRouter()
        self._device_hub = DeviceHub()
        self._store = JsonStore(config.data_dir / "pairings.json")
        self._pairing = PairingRegistry(self._store)
        self._stats = RuntimeStats()
        self._quality = AudioQualityState()
        self._http_thread: threading.Thread | None = None
        self._https_thread: threading.Thread | None = None
        self._discovery: DiscoveryResponder | None = None
        self._ip_monitor: IPMonitor | None = None

    def start(self) -> None:
        logger.info("Starting HeardDat server")
        app = build_app(
            self._pairing,
            self._router,
            self._device_hub,
            self._stats,
            self._quality,
            self.config.host,
            self.config.http_port,
        )
        self._start_server(app)
        self._start_discovery()
        self._start_ip_monitor()

    def stop(self) -> None:
        logger.info("Stopping HeardDat server")
        if self._discovery:
            self._discovery.stop()
        if self._ip_monitor:
            self._ip_monitor.stop()

    def restart(self) -> None:
        self.stop()
        self.start()

    def reconnect_device(self) -> None:
        logger.info("Reconnect requested - devices must reauthenticate on LAN")
        asyncio.run(
            self._device_hub.notify_all(
                {"type": "reauth_required", "reason": "user_initiated"}
            )
        )

    def clear_and_restart(self) -> None:
        logger.info("Restart requested with temp cleanup")
        self.restart()

    def list_devices(self) -> list[str]:
        return [record.device_id for record in self._pairing.list_devices()]

    def device_selected(self, device_id: str) -> None:
        logger.info("Device selected for reauth: %s", device_id)
        asyncio.run(
            self._device_hub.notify_device(
                device_id, {"type": "reauth_required", "reason": "user_selected"}
            )
        )

    def open_settings(self) -> None:
        """Open the local settings & diagnostics page."""

        import webbrowser

        url = f"http://127.0.0.1:{self.config.http_port}/settings"
        logger.info("Opening settings page at %s", url)
        webbrowser.open(url)

    def _start_discovery(self) -> None:
        payload = {
            "host": self.config.host,
            "http_port": str(self.config.http_port),
            "https_port": str(self.config.https_port),
        }
        self._discovery = DiscoveryResponder(payload)
        self._discovery.start()

    def _start_ip_monitor(self) -> None:
        def handle_change(new_ip: str) -> None:
            logger.info("IP change detected: %s", new_ip)
            asyncio.run(
                self._device_hub.notify_all(
                    {"type": "ip_change", "ip": new_ip, "reason": "monitor"}
                )
            )

        self._ip_monitor = IPMonitor(self.config.ip_check_interval_s, handle_change)
        self._ip_monitor.start()

    def _start_server(self, app) -> None:
        self._http_thread = threading.Thread(
            target=self._run_uvicorn,
            args=(app, self.config.http_port, False),
            daemon=True,
        )
        self._https_thread = threading.Thread(
            target=self._run_uvicorn,
            args=(app, self.config.https_port, True),
            daemon=True,
        )
        self._http_thread.start()
        self._https_thread.start()

    def _run_uvicorn(self, app, port: int, use_tls: bool) -> None:
        config = uvicorn.Config(
            app,
            host=self.config.host,
            port=port,
            log_level="info",
            ssl_certfile=str(self.config.cert_file) if use_tls else None,
            ssl_keyfile=str(self.config.key_file) if use_tls else None,
        )
        server = uvicorn.Server(config)
        asyncio.run(server.serve())


def build_tray(runtime: ServerRuntime) -> TrayApp:
    """Create tray integration with callbacks."""

    return TrayApp(
        on_start=runtime.start,
        on_stop=runtime.stop,
        on_restart=runtime.restart,
        on_reconnect=runtime.reconnect_device,
        on_clear_restart=runtime.clear_and_restart,
        list_devices=runtime.list_devices,
        on_device_select=runtime.device_selected,
        on_open_settings=runtime.open_settings,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the HeardDat PC server")
    parser.add_argument("--no-tray", action="store_true", help="Disable tray icon")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ServerConfig.from_env()
    runtime = ServerRuntime(config)
    runtime.start()

    if args.no_tray:
        logger.info("Tray disabled; server running without UI")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            runtime.stop()
        return

    tray = build_tray(runtime)
    tray.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        runtime.stop()


if __name__ == "__main__":
    main()
