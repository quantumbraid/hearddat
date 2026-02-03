"""Pairing helpers and QR payload creation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
from typing import Dict, List

from .storage import JsonStore

PAIRING_VERSION = 1


@dataclass
class PairingToken:
    """A single-use pairing token minted by the PC server."""

    token: str
    issued_at: datetime
    expires_at: datetime


@dataclass
class DeviceRecord:
    """A paired device record stored in persistent storage."""

    device_id: str
    token: str
    paired_at: datetime
    last_seen_ip: str | None = None


class PairingRegistry:
    """Keeps track of active tokens and paired devices."""

    def __init__(self, store: JsonStore) -> None:
        self.store = store

    def _load(self) -> Dict[str, Dict]:
        return self.store.load().get("pairing", {})

    def _save(self, payload: Dict[str, Dict]) -> None:
        data = self.store.load()
        data["pairing"] = payload
        self.store.save(data)

    def issue_token(self, ttl_minutes: int = 10) -> PairingToken:
        now = datetime.now(timezone.utc)
        token = secrets.token_urlsafe(32)
        payload = self._load()
        payload.setdefault("tokens", {})[token] = {
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=ttl_minutes)).isoformat(),
        }
        self._save(payload)
        return PairingToken(
            token=token,
            issued_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
        )

    def confirm_device(self, device_id: str, token: str, ip: str | None = None) -> None:
        payload = self._load()
        tokens = payload.get("tokens", {})
        if token not in tokens:
            raise ValueError("Invalid pairing token")
        payload.setdefault("devices", {})[device_id] = {
            "device_id": device_id,
            "token": token,
            "paired_at": datetime.now(timezone.utc).isoformat(),
            "last_seen_ip": ip,
        }
        tokens.pop(token, None)
        payload["tokens"] = tokens
        self._save(payload)

    def list_devices(self) -> List[DeviceRecord]:
        payload = self._load().get("devices", {})
        records: List[DeviceRecord] = []
        for device_id, record in payload.items():
            records.append(
                DeviceRecord(
                    device_id=device_id,
                    token=record["token"],
                    paired_at=datetime.fromisoformat(record["paired_at"]),
                    last_seen_ip=record.get("last_seen_ip"),
                )
            )
        return records

    def update_device_ip(self, device_id: str, ip: str) -> None:
        payload = self._load()
        devices = payload.get("devices", {})
        if device_id in devices:
            devices[device_id]["last_seen_ip"] = ip
            payload["devices"] = devices
            self._save(payload)

    def validate_device(self, device_id: str, token: str) -> bool:
        devices = self._load().get("devices", {})
        record = devices.get(device_id)
        return bool(record and record.get("token") == token)


def build_qr_payload(host: str, http_port: int, token: PairingToken) -> Dict[str, str]:
    """Build the QR payload shared with the Android device.

    The payload is intentionally human-readable JSON so that we can inspect
    it quickly during LAN-only pairing. Sensitive data is still short-lived.
    """

    return {
        "v": str(PAIRING_VERSION),
        "type": "hearddat_pairing",
        "server": f"http://{host}:{http_port}",
        "token": token.token,
        "issued_at": token.issued_at.isoformat(),
        "expires_at": token.expires_at.isoformat(),
    }
