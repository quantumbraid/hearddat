# Build Plan / TODO

## Phase 0 — Project setup
- [x] Create initial README with architecture summary and repository layout.
- [x] Create this build-plan TODO list with checkboxes.
- [x] Create the agent contract to clarify working agreements.

## Phase 1 — Protocol & security design
- [ ] Define the pairing protocol (QR payload structure, auth handshake, token rotation).
- [ ] Define the audio streaming protocol (transport, codec, buffering, reconnection).
- [ ] Document security model (encryption, threat model, trusted device revocation).

## Phase 2 — PC server (desktop)
- [ ] Choose runtime/stack and create server skeleton (HTTP + WebSocket + discovery).
- [ ] Implement QR pairing endpoint and local LAN discovery.
- [ ] Implement session persistence and mobile-data reconnect support.
- [ ] Implement audio routing pipeline for mic/speaker.
- [ ] Add hourly IP change detection and notification path.
- [ ] Add local service API for browser extensions.

## Phase 3 — Android app
- [ ] Create Android project skeleton with background service permissions.
- [ ] Implement QR scan + pairing flow.
- [ ] Implement audio capture/playback with routing controls.
- [ ] Implement hourly IP scan + server notify.
- [ ] Implement remote browser launch command handler.

## Phase 4 — Browser extensions
- [ ] Chrome extension scaffold with native messaging/local service bridge.
- [ ] Firefox extension scaffold with local service bridge.
- [ ] Implement target-site detection and voice-mode activation hooks.
- [ ] Implement audio device remap to Android stream.

## Phase 5 — Integration & testing
- [ ] End-to-end pairing tests (LAN + mobile data).
- [ ] Audio quality/performance tests.
- [ ] Extension compatibility tests on target sites.
- [ ] Security review and regression tests.
