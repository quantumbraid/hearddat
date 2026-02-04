"""Pairing helpers and QR payload creation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
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
    pin: str


@dataclass
class DeviceRecord:
    """A paired device record stored in persistent storage."""

    device_id: str
    paired_at: datetime
    last_seen_ip: str | None = None


def compute_pairing_seed(
    issued_at: datetime,
    *,
    r: int,
    g: int,
    b: int,
) -> int:
    """Compute the long-lived pairing seed from a pairing timestamp + RGB deltas.

    This intentionally follows the project-level seed rules (see README/protocol).
    It is not meant to be cryptographic; it is a deterministic seed that is:
    - unique per pairing attempt (via timestamp differences), and
    - derived partly from scan-time RGB deltas captured by the Android camera.
    """

    # Adjust time components directly (no wraparound).
    h_adj = issued_at.hour + g
    m_adj = issued_at.minute + b
    s_adj = issued_at.second + r

    t = (h_adj * m_adj) * s_adj

    # Sum absolute RGB magnitudes; negatives are flipped before summing.
    d = abs(r) + abs(g) + abs(b)
    if d == 0:
        raise ValueError("Invalid RGB deltas: |R|+|G|+|B| must be > 0")

    year = issued_at.year
    month = issued_at.month
    day = issued_at.day
    yy = year % 100

    base = (month * 100) + (yy + day)
    pack = (month * 1000) + base
    y = year * pack

    # seed = ((t / d) * y), rounded to nearest whole, half away from zero.
    numer = t * y
    sign = -1 if numer < 0 else 1
    q, rem = divmod(abs(numer), d)
    if (2 * rem) >= d:
        q += 1
    return sign * q


class PairingRegistry:
    """Keeps track of active tokens and paired devices."""

    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self._lockout_until: datetime | None = None

    def _load(self) -> Dict[str, Dict]:
        return self.store.load().get("pairing", {})

    def _save(self, payload: Dict[str, Dict]) -> None:
        data = self.store.load()
        data["pairing"] = payload
        self.store.save(data)

    def issue_token(self, ttl_minutes: int = 10) -> PairingToken:
        now = datetime.now(timezone.utc)
        token = secrets.token_urlsafe(32)
        pin = derive_pairing_pin(token, now)
        payload = self._load()
        payload.setdefault("tokens", {})[token] = {
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=ttl_minutes)).isoformat(),
            "pin": pin,
        }
        self._save(payload)
        return PairingToken(
            token=token,
            issued_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
            pin=pin,
        )

    def get_token(self, token: str) -> PairingToken | None:
        payload = self._load()
        record = payload.get("tokens", {}).get(token)
        if not record:
            return None
        issued_at = datetime.fromisoformat(record["issued_at"])
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.now(timezone.utc) >= expires_at:
            return None
        pin = str(record.get("pin", "")).zfill(4)
        return PairingToken(
            token=token,
            issued_at=issued_at,
            expires_at=expires_at,
            pin=pin,
        )

    def confirm_device(
        self,
        device_id: str,
        token: str,
        *,
        pin: str,
        r: int,
        g: int,
        b: int,
        ip: str | None = None,
    ) -> int:
        if self._lockout_until and datetime.now(timezone.utc) < self._lockout_until:
            raise ValueError("Pairing locked due to invalid PIN (try again later)")
        payload = self._load()
        tokens = payload.get("tokens", {})
        if token not in tokens:
            raise ValueError("Invalid pairing token")

        issued_at_raw = tokens[token].get("issued_at")
        if not issued_at_raw:
            raise ValueError("Pairing token missing issued_at")
        expires_at_raw = tokens[token].get("expires_at")
        if expires_at_raw:
            expires_at = datetime.fromisoformat(expires_at_raw)
            if datetime.now(timezone.utc) >= expires_at:
                raise ValueError("Pairing token expired")
        expected_pin = str(tokens[token].get("pin", "")).strip()
        if str(pin).strip() != expected_pin:
            self._lockout_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            raise ValueError("Invalid pairing PIN")
        issued_at = datetime.fromisoformat(issued_at_raw)
        seed = compute_pairing_seed(issued_at, r=r, g=g, b=b)

        payload.setdefault("devices", {})[device_id] = {
            "device_id": device_id,
            "seed": str(seed),
            "paired_at": datetime.now(timezone.utc).isoformat(),
            "last_seen_ip": ip,
        }
        tokens.pop(token, None)
        payload["tokens"] = tokens
        self._save(payload)
        return seed

    def list_devices(self) -> List[DeviceRecord]:
        payload = self._load().get("devices", {})
        records: List[DeviceRecord] = []
        for device_id, record in payload.items():
            records.append(
                DeviceRecord(
                    device_id=device_id,
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
        return bool(record and str(record.get("seed")) == str(token))


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


def derive_pairing_pin(token: str, issued_at: datetime) -> str:
    """Derive a semi-random 4-digit PIN from the token and timestamp."""

    payload = f"{token}:{issued_at.isoformat()}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    value = int.from_bytes(digest[:4], "big") % 10000
    return f"{value:04d}"
