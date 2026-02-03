# HeardDat Protocol Overview

## Pairing protocol (Phase 1)

**Intent:** Pair the Android app to the PC server on the same LAN with a short-lived
QR token. The QR payload is JSON so it can be inspected while still being
restricted to LAN-only access.

### QR payload format

```json
{
  "v": "1",
  "type": "hearddat_pairing",
  "server": "http://<pc-host>:80",
  "token": "<short-lived-token>",
  "issued_at": "<ISO-8601 UTC>",
  "expires_at": "<ISO-8601 UTC>"
}
```

### Pairing handshake

1. **PC server** creates a short-lived token (`/v1/pairing/request`).
2. **Android app** scans QR, then POSTs `/v1/pairing/confirm` with
   `device_id` and `token`.
3. **PC server** persists the device record and invalidates the token.
4. **Device sessions** reconnect by using the persisted `device_id` + `token`
   over `/ws/device/{device_id}?token=...`.

### Token rotation

- Tokens expire after 10 minutes by default.
- Tokens are single-use and removed immediately after successful pairing.

## Audio streaming protocol (Phase 1)

**Transport:** WebSocket frames over ports 80 (unsecured) and 81 (TLS).

### Channels

- `mic` — Android microphone audio flowing to the PC.
- `speaker` — Android speaker audio flowing from the PC.

### Endpoints

- **Ingest:** `/ws/audio/<channel>/ingest`
- **Consume:** `/ws/audio/<channel>`

### Payloads

- Audio is sent as raw binary frames.
- Clients may optionally send a **JSON metadata frame first** to indicate
  source/target codec and sample rate, for example:

  ```json
  {\"format\": \"pcm\", \"sample_rate\": 16000, \"target_format\": \"opus\"}
  ```
- Preferred codec: **Opus** at 16 kHz mono, with optional 24 kHz for higher
  quality.
- **Fallback:** 16-bit mono PCM when Opus is unavailable or during diagnostics.

### Reconnection

- Clients reconnect to the same channel and resume sending frames.
- The PC server keeps routing stateless; clients may resume without a
  renegotiation handshake.

## Security considerations

- Pairing is LAN-only and assumes trust within the local network.
- Use a VPN or proxy if stronger security is required at first run.
- Audio streams can be encrypted on port 81 using the bundled TLS certificate.
