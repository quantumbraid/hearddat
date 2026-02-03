# Build Plan / TODO

## Phase 0 — Project setup
- [x] Create initial README with architecture summary and repository layout.
- [x] Create this build-plan TODO list with checkboxes.
- [x] Create the agent contract to clarify working agreements.
- [x] Add repository snapshot tooling for end-of-job archive (`tools/god_snapshot.py`).

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

## Phase 5 — Integration & testing
- [ ] End-to-end pairing tests (LAN + mobile data).
- [ ] Audio quality/performance tests.
- [ ] Extension compatibility tests on target sites.
- [ ] Security review and regression tests.
