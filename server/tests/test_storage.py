from pathlib import Path

from server.storage import JsonStore


def test_json_store_round_trip(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / "data.json")
    store.save({"hello": "world"})
    assert store.load() == {"hello": "world"}
