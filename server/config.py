"""Configuration for the HeardDat PC server."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class ServerConfig:
    """Runtime configuration for the desktop server.

    Keep this centralized so we can pass it across components and keep
    defaults consistent between HTTP and WebSocket services.
    """

    host: str = "0.0.0.0"
    http_port: int = 80
    https_port: int = 81
    data_dir: Path = Path("server/data")
    cert_file: Path = Path("server/certs/hearddat_cert.pem")
    key_file: Path = Path("server/certs/hearddat_key.pem")
    ip_check_interval_s: int = 60 * 60

    @staticmethod
    def from_env() -> "ServerConfig":
        """Load configuration overrides from environment variables."""

        return ServerConfig(
            host=os.getenv("HEARDDAT_HOST", "0.0.0.0"),
            http_port=int(os.getenv("HEARDDAT_HTTP_PORT", "80")),
            https_port=int(os.getenv("HEARDDAT_HTTPS_PORT", "81")),
            data_dir=Path(os.getenv("HEARDDAT_DATA_DIR", "server/data")),
            cert_file=Path(
                os.getenv("HEARDDAT_CERT_FILE", "server/certs/hearddat_cert.pem")
            ),
            key_file=Path(
                os.getenv("HEARDDAT_KEY_FILE", "server/certs/hearddat_key.pem")
            ),
            ip_check_interval_s=int(
                os.getenv("HEARDDAT_IP_CHECK_INTERVAL", str(60 * 60))
            ),
        )
