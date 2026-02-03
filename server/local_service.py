"""Local service endpoints for browser extensions."""
from __future__ import annotations

from typing import Dict

from fastapi import APIRouter

from .pairing import PairingRegistry


def build_router(pairing: PairingRegistry) -> APIRouter:
    """Expose a minimal API for extension integration."""

    router = APIRouter(prefix="/v1")

    @router.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @router.get("/devices")
    async def devices() -> Dict[str, object]:
        return {
            "devices": [device.__dict__ for device in pairing.list_devices()],
        }

    return router
