# Build Plan / TODO

## Current project philosophy (as of now)
- Prioritize reliable audio streaming between phone ↔ computer, computer → phone,
  and phone → browser audio before refining individual site integrations.
- Once core audio streaming is stable, focus on per-site voice workflows and UX
  details in the browser extensions.

## Working documents (keep these consistent)
- `README.md` — project overview and how components fit together
- `shared/protocol.md` — intended on-the-wire protocol and pairing/audio rules
- `sos.txt` — known prototype-vs-intent gaps and a punch list for the next build job

## Phase 0 — Project setup
- [x] Create initial README with architecture summary and repository layout.
- [x] Create this build-plan TODO list with checkboxes.
- [x] Create the agent contract to clarify working agreements.
- [x] Add repository snapshot tooling for end-of-job archive (`tools/god_snapshot.py`).

## Phase 1 — Protocol & connectivity design
- [x] Define the pairing protocol (QR payload structure + handshake). Pairing bootstrap requires the same LAN and is done only in-app (QR scan) with no webview/browser usage. The resulting pairing relationship is long-lived and must be revocable from both client and server. Default posture: no custom key exchange (no key transmission as part of pairing beyond opaque tokens). See `shared/protocol.md` for the baseline spec.
- [x] Define the audio streaming protocol (transport, codec, buffering, reconnection). WebSocket transport, binary Opus frames at 16 kHz (optional 24 kHz) with PCM fallback, reconnection by rejoining channel without renegotiation. Audio is intended to work over any network with sufficient bandwidth, but only after an in-network pairing. See `shared/protocol.md` for the baseline spec.
- [x] Document revocation model at the intent level (trusted device revocation/unpair exists; implement later).
- [x] Technical decisions (complete and lock for build plan updates):
  - [x] Audio format: Opus (low-bitrate speech-optimized) as primary for streaming efficiency; fallback to 16-bit PCM for local diagnostics or when Opus is unavailable.
  - [x] Default sample rate: 16 kHz for speech-first STT alignment, with optional 24 kHz for higher-quality voice interaction when bandwidth allows.
  - [x] Bitrate target: start ~16–24 kbps for speech Opus to minimize mobile data usage while keeping latency low; allow adaptive bumps for noisy environments.
  - [x] Packetization/transport: WebSocket frames carrying Opus packets or PCM chunks, keeping payloads small for low-latency voice interaction.
  - [x] Compatibility note: align with common STT/TTS voice pipelines that expect 16 kHz mono PCM or Opus-wrapped speech streams in generalized terms (no vendor-specific assumptions).

### Phase 1a — Protocol updates (from `sos.txt` + latest intent)
- [x] Update `shared/protocol.md` to reflect:
  - Long-lived pairing + explicit revocation/unpair flows
  - "No custom key exchange" posture
  - Audio allowed on any network *after* in-LAN pairing
  - Ports are configurable (80/81 were temporary)
  - UPnP support for reachability (optional)
- [x] Define the connectivity/reachability story post-pairing: same LAN vs VPN vs manual port-forward vs UPnP (and what happens when UPnP fails).
- [x] Define re-pair policy: re-pairing/re-issuing the seed is LAN-only.
- [x] Define manual port fallback UX: when UPnP is unavailable, server displays a 4-digit PIN that must be entered on Android.
- [ ] Define how “paired” is enforced for audio endpoints (policy statement, not implementation): who can publish/consume which channels, and how extensions authenticate to the local service.
- [x] Define the paired command scope: which remote admin actions are allowed (restart, browser open, hotkeys, extension DOM class triggers).

## Phase 2 — PC server (desktop)
- [x] Choose runtime/stack and create server skeleton (HTTP + WebSocket + discovery). FastAPI + Uvicorn with UDP discovery responder.
- [x] Implement QR pairing endpoint and local LAN discovery.
- [x] Implement session persistence and mobile-data reconnect support (device registry + token-based reconnect).
- [x] Implement audio routing pipeline for mic/speaker.
- [x] Implement Opus encode/decode at 16 kHz default with optional 24 kHz, plus PCM fallback for diagnostics.
- [x] Add hourly IP change detection and notification path (device WebSocket notifications).
- [x] Add local service API for browser extensions.
- [x] Serve the local pairing page (AuthPair/index.html boilerplate) and QR payload with local LAN-only assumptions.
- [x] Implement dual-port listener: port 80 (unsecured) and port 81 (secure/encrypted) for audio streams (temporary defaults; ports are intended to be configurable).
- [x] Add taskbar icon with right-click menu: start server, stop server, restart server, reconnect to device, devices submenu, restart service after clearing temp files.
- [x] Implement devices submenu with per-device reauthentication requirement on local LAN when clicked.
- [x] Build a Windows installer (preferably an executable) for the PC server.
- [ ] Ensure the installer fetches/installs dependencies when needed and applicable.
- [x] Add installer completion prompts:
  - [x] Ask whether the server should start when Windows starts.
  - [x] Ask whether to start the server immediately after install.
- [x] Add a right-click menu item to open Settings & Diagnostics.
- [x] Serve a local Settings & Diagnostics web page populated with run statistics.
- [x] Add UI controls to increase/decrease audio quality stream.
- [x] Leave a placeholder for future audio encoding style selection (documented as future update).

### Phase 2a — Prototype alignment & polish (from `sos.txt`)
- [ ] Fix Settings API wiring so `/v1/settings/status` works end-to-end (currently broken due to a name collision/shadowing bug).
- [ ] Make tray Start/Stop/Restart actually control the server lifecycle (no orphaned server threads; stop should stop the listeners).
- [ ] Make device notifications safe from the tray thread (avoid cross-event-loop WebSocket usage).
- [ ] Enforce “paired first” for audio on any network: audio WebSockets must require a paired device credential (policy/implementation alignment).
- [ ] Make ports configurable beyond env vars: decide and document defaults; ensure Settings & Diagnostics surfaces current ports.
- [ ] Add UPnP (optional) to map ports for reachability, and expose mapping status + errors in Settings & Diagnostics.
- [ ] Implement manual port fallback UI: show the active port + 4-digit PIN to enter on Android when UPnP is unavailable.
- [ ] Update the pairing UI to display an actual black/white QR code (and optional calibration swatches) so Android can compute stable `rgb_deltas` from the scan.
- [ ] Make the pairing UI/assets robust to different working directories and packaging (static file paths should be reliable).
- [ ] Ensure discovery + IP monitor can be stopped/started cleanly (restart should actually restart those subsystems).
- [ ] Implement real “Restart service (clear temp)” behavior or rename it to match what it does.
- [ ] Update docs to match reality after the above changes: `README.md`, `shared/protocol.md`, and `sos.txt`.

## Phase 3 — Android app
- [ ] Create Android project skeleton with background service permissions.
- [ ] Implement QR scan + pairing flow.
- [ ] Compute scan-time RGB deltas (black/white diff) during QR scan and submit as `rgb_deltas` during `/v1/pairing/confirm` (see `shared/protocol.md`).
- [ ] Implement audio capture/playback with routing controls.
- [ ] Implement Opus capture/playback path (16 kHz default, optional 24 kHz) with PCM fallback for diagnostics.
- [ ] Implement hourly IP scan + server notify.
- [ ] Implement remote browser launch command handler.
- [ ] Ensure pairing is handled only in-app (camera/QR scan) with no webview/browser usage.
- [ ] Display first-run guidance about using VPN or proxy if security is a concern (LAN trust assumption).
- [ ] Implement configurable-port stream handling (80/81 were temporary defaults).
- [ ] Add a settings menu for secure vs. unsecure communication selection.
- [ ] Add an in-app button to unpair the device from the server.
- [ ] Add a ping button to verify server reachability over Wi-Fi or mobile data.
- [ ] Implement revocation UX: handle “server revoked/unpaired” events and guide the user back through LAN pairing when needed.
- [ ] Implement reachability helpers for post-pairing connectivity (UPnP-aware discovery/status, clear errors when PC is not reachable).
- [ ] Add manual port fallback entry: prompt for the server’s 4-digit PIN when UPnP is unavailable.
- [ ] Add paired command controls: restart server, open browser, send hotkeys, and trigger extension class buttons (gated by paired status).

## Phase 4 — Browser extensions
- [ ] Chrome extension scaffold with native messaging/local service bridge.
- [ ] Firefox extension scaffold with local service bridge.
- [ ] Implement target-site detection and voice-mode activation hooks.
- [ ] Implement audio device remap to Android stream.
- [ ] Hold per-site customizations until audio streaming is stable across phone ↔ PC ↔ browser.
- [ ] Define per-site voice activation flows and accessibility upgrades for target sites.
  - [x] **chatgpt.com** build decisions:
    - [x] Trigger rule: opening `https://chatgpt.com` should open a new conversation.
    - [x] Voice toggle: click `document.querySelector('[aria-label=\"Dictate button\"].composer-btn').click();`.
    - [x] Behavior: first click starts recording, second click stops recording and submits.
    - [x] Accessibility upgrades: add keyboard shortcut for toggle + announce state changes via ARIA live region.
  - [x] **grok.com** build decisions:
    - [x] Trigger rule: open `https://grok.com/?voice=true` to start a new audio interaction.
    - [x] State sync: conversation URL auto-populates once voice session begins.
    - [x] Stop rule: switch to `voice=false` to kill the audio stream.
    - [x] Accessibility upgrades: provide visible start/stop feedback and ensure focus is preserved after toggles.
  - [ ] **kindroid.ai/call** build decisions:
    - [x] Trigger rule: open `https://kindroid.ai/call` as the entry point.
    - [ ] TODO: confirm how call initiation is triggered in DOM and record selectors.
    - [ ] TODO: confirm stop/cleanup sequence and whether URL params control voice state.
    - [ ] Accessibility upgrades: ensure button labels and status messaging are announced to screen readers.
  - [ ] **chatgpt.com** read-aloud replay detail:
    - [ ] TODO: Configure a replay event for the Read Aloud button that triggers after the model finishes responding. This is the stable mode vs. voice mode. GPT supports Read Aloud, Grok does not (Grok is a hot on/off toggle without a dictate button).

## Phase 5 — Integration & testing
- [ ] End-to-end pairing tests: in-LAN pairing bootstrap, then remote reconnect/audio from mobile data.
- [ ] Audio quality/performance tests.
- [ ] Extension compatibility tests on target sites.
- [ ] Security review and regression tests (separate job; do after alignment + basic reliability).
