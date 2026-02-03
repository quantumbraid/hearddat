from datetime import datetime, timezone
from pathlib import Path

from server.pairing import PairingRegistry, build_qr_payload
from server.storage import JsonStore


def test_issue_token(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "pairings.json")
    registry = PairingRegistry(store)
    token = registry.issue_token(ttl_minutes=1)
    assert token.token
    assert token.expires_at > token.issued_at


def test_confirm_device(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "pairings.json")
    registry = PairingRegistry(store)
    token = registry.issue_token(ttl_minutes=1)
    registry.confirm_device("device-123", token.token, ip="192.168.1.10")
    devices = registry.list_devices()
    assert devices[0].device_id == "device-123"
    assert devices[0].last_seen_ip == "192.168.1.10"


def test_build_qr_payload() -> None:
    class FakeToken:
        token = "abc"
        issued_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        expires_at = datetime(2024, 1, 1, 1, tzinfo=timezone.utc)

    payload = build_qr_payload("127.0.0.1", 80, FakeToken())
    assert payload["server"] == "http://127.0.0.1:80"
    assert payload["token"] == "abc"
