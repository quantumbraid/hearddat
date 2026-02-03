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

## Notes

- This repository currently contains planning artifacts and contracts to guide implementation.
- As we build each component, we will expand the folders listed above.
