"""FastAPI application wiring for HeardDat server."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .audio import AudioRouter, pump_audio, recv_audio
from .devices import DeviceHub
from .local_service import build_router
from .pairing import PairingRegistry, build_qr_payload


def build_app(
    pairing: PairingRegistry,
    router: AudioRouter,
    device_hub: DeviceHub,
    host: str,
    http_port: int,
) -> FastAPI:
    app = FastAPI(title="HeardDat PC Server")
    app.include_router(build_router(pairing))

    @app.get("/pair", response_class=HTMLResponse)
    async def pairing_page() -> HTMLResponse:
        html = Path("server/AuthPair/index.html").read_text(encoding="utf-8")
        return HTMLResponse(html)

    @app.post("/v1/pairing/request")
    async def request_pairing() -> Dict[str, object]:
        token = pairing.issue_token()
        payload = build_qr_payload(host, http_port, token)
        return {"token": token.token, "payload": payload}

    @app.post("/v1/pairing/confirm")
    async def confirm_pairing(request: Request) -> Dict[str, str]:
        body = await request.json()
        device_id = body.get("device_id")
        token = body.get("token")
        if not device_id or not token:
            raise HTTPException(status_code=400, detail="device_id and token required")
        pairing.confirm_device(device_id=device_id, token=token, ip=request.client.host)
        return {"status": "paired"}

    @app.websocket("/ws/device/{device_id}")
    async def device_ws(websocket: WebSocket, device_id: str) -> None:
        token = websocket.query_params.get("token")
        if not token or not pairing.validate_device(device_id, token):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        await device_hub.register(device_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await device_hub.unregister(device_id)

    @app.websocket("/ws/audio/{channel}")
    async def audio_ws(websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        queue = await router.register(channel)
        try:
            await pump_audio(queue, websocket)
        except WebSocketDisconnect:
            return
        finally:
            await router.unregister(channel, queue)

    @app.websocket("/ws/audio/{channel}/ingest")
    async def audio_ingest(websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        try:
            await recv_audio(websocket, router, channel)
        except WebSocketDisconnect:
            return

    return app
