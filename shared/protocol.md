# HeardDat Protocol Overview

## Pairing protocol (Phase 1)

**Intent:** Pair the Android app to the PC server on the same LAN using a
short-lived QR bootstrap token, then establish a **long-lived, revocable**
pairing relationship used for reconnecting from any network (when the PC is
reachable).

HeardDat's default posture is **no custom key exchange**: pairing establishes an
auth relationship (seed/token), not an app-managed encryption key.

**Re-pairing is LAN-only:** any re-issue of a pairing seed must occur with both
devices on the same local network.

### QR payload format

```json
{
  "v": "1",
  "type": "hearddat_pairing",
  "server": "http://<pc-host>:<http-port>",
  "token": "<short-lived-token>",
  "issued_at": "<ISO-8601 UTC>",
  "expires_at": "<ISO-8601 UTC>"
}
```

### Pairing handshake

1. **PC server** creates a short-lived token (`/v1/pairing/request`) and displays
   it as a QR payload. The response also includes a **4-digit PIN** used for
   manual port fallback flows.
2. **Android app** scans the QR and computes scan-time RGB deltas
   (`r`, `g`, `b`) from the camera sample (see "Pairing seed derivation").
3. **Android app** POSTs `/v1/pairing/confirm` with:
   - `device_id`
   - `token` (bootstrap token from QR)
   - `pin` (4-digit PIN from the server display)
   - `rgb_deltas`: `{ "r": <int>, "g": <int>, "b": <int> }`
4. **PC server** validates the bootstrap token, derives a **pairing seed**,
   persists the paired device record, and invalidates the bootstrap token.
5. **PC server** returns the **pairing seed** to the Android app as part of the
   `/v1/pairing/confirm` response. The seed is not included in the QR payload.
6. **Device sessions** reconnect using `device_id` + `seed` over:
   `/ws/device/{device_id}?token=<seed>`.

### Bootstrap token rules

- Tokens expire after 10 minutes by default.
- Tokens are single-use and removed immediately after successful pairing.
- QR payloads are unique per pairing attempt by virtue of including a fresh
  bootstrap token.
- The 4-digit PIN is derived from the bootstrap token + timestamp. If a PIN is
  entered incorrectly, pairing attempts are blocked for 10 minutes (or until the
  server restarts).

### Manual port fallback (Phase 1)

If UPnP is unavailable, the server will present:
- The active port to reach the PC server, and
- A 4-digit PIN that must be entered on Android during pairing.

This PIN is **not** embedded in the QR payload; it is delivered out-of-band by
the pairing UI and the `/v1/pairing/request` response.

### Pairing seed derivation (Phase 1)

The pairing seed is deterministic and computed by the server during pairing.
It is based on:
- The server's pairing timestamp (from the bootstrap token's `issued_at`)
- The scan-time RGB deltas provided by the Android app
- The date derived from the same pairing timestamp

#### Inputs

- Signed RGB deltas: `R`, `G`, `B` (integers; negatives allowed)
- Pairing timestamp (server): `H:M:S` and `YYYY-MM-DD`

#### Algorithm

1. Apply channel deltas directly to time components:
   - `H' = H + G`
   - `M' = M + B`
   - `S' = S + R`
2. Mix adjusted time:
   - `T = (H' × M') × S'`
3. Compute RGB divisor using absolute magnitudes:
   - `D = |R| + |G| + |B|`
4. Time-derived subtotal:
   - `X = T / D`
5. Compute date pack:
   - `YY = last two digits of year`
   - `base = (month × 100) + (YY + day)`
   - `pack = (month × 1000) + base`
   - `Y = year × pack`
6. Final seed:
   - `seed = round(X × Y)` (rounded to nearest whole; half away from zero)

#### Example

Given:
- RGB deltas: `R = +7`, `G = −1`, `B = +3`
- Pairing timestamp: `10:50:47`
- Date: `2026-02-03`

Result:
- `seed = 10574722103`

## Audio streaming protocol (Phase 1)

**Transport:** WebSocket frames over configurable ports. Earlier 80/81 defaults
were temporary; implementations should allow changing ports freely.

Audio is intended to work over **any network with sufficient bandwidth**, but
only after an initial in-LAN pairing bootstrap.

### Channels

- `mic` — Android microphone audio flowing to the PC.
- `speaker` — Android speaker audio flowing from the PC.

### Endpoints

- **Ingest:** `/ws/audio/<channel>/ingest?device_id=...&token=<seed>`
- **Consume:** `/ws/audio/<channel>?device_id=...&token=<seed>`

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
- Audio streams can optionally use TLS when configured. TLS cert/key material is
  generated per-install and is not committed to the repository.
- UPnP support is planned to improve reachability for remote connections when
  enabled and supported by the user's router.
