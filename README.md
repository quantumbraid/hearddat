# HeardDat

HeardDat is a multi-part system that pairs an Android phone with a PC so they can
share microphone/speaker audio and feed that audio into browser voice workflows.

It includes:

- **PC server (Windows-first)**: Pairs devices, brokers audio, exposes a local service for browser extensions, and serves a local Settings & Diagnostics page.
- **Android app**: Captures mic / plays speaker, pairs via QR on the local network, and reconnects from any network after pairing.
- **Browser extensions (Chrome + Firefox)**: Use the local PC service to map Android audio to supported voice-mode web apps.

See `TODO.md` for the build plan and `sos.txt` for known prototype-vs-intent gaps.

## Core ideas (intent)

- **Pair once on LAN**: The phone and PC must be on the same local network for initial pairing (QR bootstrap).
- **Re-pair on LAN only**: Any re-pair or re-issue of a pairing seed must be done on the same local network.
- **Pairing is long-lived and revocable**: Unpair/revoke should be possible from both the phone and the PC.
- **No custom key exchange**: Pairing establishes an auth token/relationship; encryption is transport-level (optional TLS), not app-managed key exchange.
- **Audio works on any network after pairing**: Once paired, the phone can connect over Wi-Fi/LTE/any network with sufficient bandwidth, as long as the PC is reachable.
- **Ports are configurable**: Earlier 80/81 defaults were temporary and can be changed freely.
- **UPnP preferred for reachability (planned)**: The PC server should prefer UPnP for mapping ports on typical home routers; if UPnP is unavailable, fall back to manual port configuration and a server-displayed 4-digit PIN entry on Android.

## High-level architecture

1. **LAN pairing bootstrap**: Android scans a QR payload created by the PC server while both are on the same LAN.
2. **Long-lived pairing**: The device stores a long-lived pairing credential and can be revoked/unpaired from either side.
3. **Reachability**: After pairing, Android connects to the PC over any network if the PC is reachable (same LAN, VPN, port-forward, or UPnP when enabled).
4. **Audio routing**: Android and the PC negotiate audio streams for mic/speaker sharing (Opus primary, PCM fallback).
5. **Browser integration**: Extensions connect to a local PC service and map Android audio to supported web pages.
6. **Remote launch (planned)**: Android can ask the PC to open a browser window and navigate to supported pages.

## Paired capabilities

Once paired, the Android device is allowed to:

- Create new audio pipelines for mic/speaker sharing (primary function).
- Trigger approved server actions like restart and browser open.
- Send remote hotkeys and trigger supported DOM class buttons through the browser extension bridge.

## Build plan (granular to-do list)

See [`TODO.md`](./TODO.md) for a structured, checkbox-based plan.

## Repository layout

- `server/`: PC server prototype (FastAPI + Uvicorn), plus tray and settings UI scaffolding
- `shared/`: Shared protocol/spec documentation
- `tools/`: Maintenance scripts (snapshot tooling, Windows installer script)
- `android/`: Android application (planned)
- `extensions/`: Chrome/Firefox extensions (planned)

## PC server (Phase 2 prototype)

The desktop server is implemented in `server/` using FastAPI + Uvicorn. It
exposes HTTP + WebSocket endpoints (ports are configurable). The current
prototype defaults to **80** (unsecured) and **81** (TLS). TLS cert/key material
is generated per-install into `server/certs/` (not committed to the repo).

### Installer + tray UX (prototype scaffolding)

- Distribute a Windows installer as an executable file whenever possible.
- The installer should fetch/install dependencies when needed and applicable.
- At install completion, prompt whether to:
  - start the server when Windows starts, and
  - start the server immediately after install.
- The taskbar icon right-click menu will include a **Settings & Diagnostics**
  entry that opens a local web page served by the PC server.
- The local page will surface run statistics and allow the user to increase or
  decrease the audio quality stream; encoding style selection will be added in a
  future update.

### Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r server/requirements.txt
python -m server.main --no-tray
```

### Configuration (current)

Environment variables (see `server/config.py`):

- `HEARDDAT_HOST` (default `0.0.0.0`)
- `HEARDDAT_HTTP_PORT` (default `80`, temporary)
- `HEARDDAT_HTTPS_PORT` (default `81`, temporary)
- `HEARDDAT_DATA_DIR` (default `server/data`)
- `HEARDDAT_CERT_FILE` / `HEARDDAT_KEY_FILE` (dev TLS cert/key paths)
- `HEARDDAT_IP_CHECK_INTERVAL` (seconds; default 3600)

### Key endpoints

- `GET /pair` — LAN-only pairing page.
- `POST /v1/pairing/request` — generate a short-lived pairing bootstrap token + payload for QR.
- `POST /v1/pairing/confirm` — confirm pairing bootstrap, submit scan-time RGB deltas, and receive the long-lived pairing seed.
- `GET /v1/health` — extension health check.
- `GET /v1/devices` — list paired devices.
- `WS /ws/audio/<channel>/ingest` — ingest audio.
- `WS /ws/audio/<channel>` — consume audio.
- `WS /ws/device/<device_id>?token=...` — device notification channel.

See [`shared/protocol.md`](./shared/protocol.md) for baseline protocol details
and `TODO.md` (Phase 1a) for any deltas that still need to be reflected in the
spec.

## Snapshot script

Use `tools/god_snapshot.py` to capture a text-only snapshot of the repo into
`book/<timestamp>/god.txt`. The script excludes `book/`, dotfiles, git-ignored
paths, and common binary formats. It can also restore a repository when run with
the path to a `god.txt` file.

## Notes

- This repository currently contains planning artifacts and contracts to guide implementation.
- As we build each component, we will expand the folders listed above.

## Current project philosophy

We will prioritize getting audio to successfully stream between the phone and
computer (both directions) and between the phone and browser audio before
focusing on individual site integrations. Once audio communication is stable,
we will refine per-site behaviors and UX details for supported web apps.
