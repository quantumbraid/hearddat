# Build Plan / TODO

## Phase 0 — Project setup
- [x] Create initial README with architecture summary and repository layout.
- [x] Create this build-plan TODO list with checkboxes.
- [x] Create the agent contract to clarify working agreements.
- [x] Add repository snapshot tooling for end-of-job archive (`tools/god_snapshot.py`).

## Phase 1 — Protocol & security design
- [x] Define the pairing protocol (QR payload structure, auth handshake, token rotation). QR directs to a local .html page that is largely boilerplate from AuthPair/index.html. Because this requires the same network to pair, trust is assumed. The first time the user opens the Android app, they will be told to use VPN or proxy if security is a concern. The app will be the only way to connect to the QR code, so it will need camera and QR scan. Once the phone is paired to the PC with a token that is only ever established in same local network they do not exchange keys, but instead under secure mode will transmit encrypted over 81 and unsecured on port 80. This is not through webview or Android browser. This is a tool that simply transmits audio streams and triggers record functions of websites for voice interactions. The PC server will run with a taskbar icon, right click will have a menu: start server, stop server, restart server, reconnect to device, devices, restart service after clearing temp files. If the user hovers on devices there is a submenu that shows all connected devices, clicking any device requires it to reauthenticate on local LAN. See shared/protocol.md for payload shape and handshake steps.
- [x] Define the audio streaming protocol (transport, codec, buffering, reconnection). WebSocket transport on ports 80/81, binary Opus frames at 16 kHz (optional 24 kHz) with PCM fallback, reconnection by rejoining channel without renegotiation. Documented in shared/protocol.md.
- [x] Document security model (encryption, threat model, trusted device revocation). covered above.
- [x] Technical decisions (complete and lock for build plan updates):
  - [x] Audio format: Opus (low-bitrate speech-optimized) as primary for streaming efficiency; fallback to 16-bit PCM for local diagnostics or when Opus is unavailable.
  - [x] Default sample rate: 16 kHz for speech-first STT alignment, with optional 24 kHz for higher-quality voice interaction when bandwidth allows.
  - [x] Bitrate target: start ~16–24 kbps for speech Opus to minimize mobile data usage while keeping latency low; allow adaptive bumps for noisy environments.
  - [x] Packetization/transport: WebSocket frames carrying Opus packets or PCM chunks, keeping payloads small for low-latency voice interaction.
  - [x] Compatibility note: align with common STT/TTS voice pipelines that expect 16 kHz mono PCM or Opus-wrapped speech streams in generalized terms (no vendor-specific assumptions).

## Phase 2 — PC server (desktop)
- [x] Choose runtime/stack and create server skeleton (HTTP + WebSocket + discovery). FastAPI + Uvicorn with UDP discovery responder.
- [x] Implement QR pairing endpoint and local LAN discovery.
- [x] Implement session persistence and mobile-data reconnect support (device registry + token-based reconnect).
- [x] Implement audio routing pipeline for mic/speaker.
- [x] Implement Opus encode/decode at 16 kHz default with optional 24 kHz, plus PCM fallback for diagnostics.
- [x] Add hourly IP change detection and notification path (device WebSocket notifications).
- [x] Add local service API for browser extensions.
- [x] Serve the local pairing page (AuthPair/index.html boilerplate) and QR payload with local LAN-only assumptions.
- [x] Implement dual-port listener: port 80 (unsecured) and port 81 (secure/encrypted) for audio streams.
- [x] Add taskbar icon with right-click menu: start server, stop server, restart server, reconnect to device, devices submenu, restart service after clearing temp files.
- [x] Implement devices submenu with per-device reauthentication requirement on local LAN when clicked.

## Phase 3 — Android app
- [ ] Create Android project skeleton with background service permissions.
- [ ] Implement QR scan + pairing flow.
- [ ] Implement audio capture/playback with routing controls.
- [ ] Implement Opus capture/playback path (16 kHz default, optional 24 kHz) with PCM fallback for diagnostics.
- [ ] Implement hourly IP scan + server notify.
- [ ] Implement remote browser launch command handler.
- [ ] Ensure pairing is handled only in-app (camera/QR scan) with no webview/browser usage.
- [ ] Display first-run guidance about using VPN or proxy if security is a concern (LAN trust assumption).
- [ ] Implement dual-port stream handling: unsecured port 80 and secure/encrypted port 81.

## Phase 4 — Browser extensions
- [ ] Chrome extension scaffold with native messaging/local service bridge.
- [ ] Firefox extension scaffold with local service bridge.
- [ ] Implement target-site detection and voice-mode activation hooks.
- [ ] Implement audio device remap to Android stream.
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
- [ ] End-to-end pairing tests (LAN + mobile data).
- [ ] Audio quality/performance tests.
- [ ] Extension compatibility tests on target sites.
- [ ] Security review and regression tests.
