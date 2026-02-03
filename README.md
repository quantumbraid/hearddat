# hearddat

HeardDat is a multi-part system that lets a PC and Android device securely share microphone and speaker audio. It includes:

- **PC server**: The hub that pairs with mobile clients, brokers audio, and exposes a local service for browser extensions.
- **Android app**: Shares mic/speaker with the PC, supports QR pairing on LAN, and reconnects on mobile data.
- **Browser extensions (Chrome + Firefox)**: Use the local service to supply Android mic/speaker audio to specific voice-mode web apps.

## High-level architecture

1. **Pairing**: Android scans a QR code emitted by the PC server over the local network.
2. **Session persistence**: After pairing, the devices can connect even on mobile data.
3. **IP monitoring**: Android scans in the background hourly for IP changes and notifies the paired device when it changes.
4. **Audio routing**: The PC server and Android client negotiate audio streams for mic/speaker sharing.
5. **Browser integration**: Extensions connect to the local PC server and map Android audio to supported web pages.
6. **Remote launch**: Android can trigger the PC to open a browser window and navigate to supported pages.

## Build plan (granular to-do list)

See [`TODO.md`](./TODO.md) for a structured, checkbox-based plan.

## Repository layout (planned)

- `server/`: PC server implementation
- `android/`: Android application
- `extensions/chrome/`: Chrome extension
- `extensions/firefox/`: Firefox extension
- `shared/`: Shared protocol specs, utilities, and test fixtures
- `tools/`: Maintenance scripts (including repository snapshot tooling)

## PC server (Phase 2 prototype)

The desktop server is implemented in `server/` using FastAPI + Uvicorn. It
exposes HTTP + WebSocket endpoints on ports **80** (unsecured) and **81**
(TLS). The TLS certificate is a local dev certificate stored in
`server/certs/`.

### Installer + tray UX (planned)

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

### Key endpoints

- `GET /pair` — LAN-only pairing page.
- `POST /v1/pairing/request` — generate a short-lived pairing token.
- `POST /v1/pairing/confirm` — confirm a pairing token.
- `GET /v1/health` — extension health check.
- `GET /v1/devices` — list paired devices.
- `WS /ws/audio/<channel>/ingest` — ingest audio.
- `WS /ws/audio/<channel>` — consume audio.
- `WS /ws/device/<device_id>?token=...` — device notification channel.

See [`shared/protocol.md`](./shared/protocol.md) for the full Phase 1 protocol
details.

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
