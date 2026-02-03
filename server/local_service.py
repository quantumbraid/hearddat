"""Local service endpoints for browser extensions."""
from __future__ import annotations

from typing import Dict

from fastapi import APIRouter

from .audio import AudioRouter
from .devices import DeviceHub
from .pairing import PairingRegistry
from .quality import AudioQualityState
from .stats import RuntimeStats


def build_router(
    pairing: PairingRegistry,
    stats: RuntimeStats,
    quality: AudioQualityState,
    device_hub: DeviceHub,
    router: AudioRouter,
) -> APIRouter:
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

    @router.get("/settings/status")
    async def settings_status() -> Dict[str, object]:
        """Return live stats and configuration for the settings UI."""

        snapshot = stats.snapshot()
        return {
            "stats": snapshot.as_dict(),
            "audio_quality": quality.snapshot(),
            "connected_devices": await device_hub.count(),
            "active_channels": await router.active_channels(),
        }

    @router.post("/settings/audio-quality/increase")
    async def increase_quality() -> Dict[str, object]:
        """Increase audio quality preference and notify devices."""

        preset = quality.increase()
        await device_hub.notify_all(
            {"type": "audio_quality_update", "preset": preset.as_dict()}
        )
        return {"audio_quality": preset.as_dict()}

    @router.post("/settings/audio-quality/decrease")
    async def decrease_quality() -> Dict[str, object]:
        """Decrease audio quality preference and notify devices."""

        preset = quality.decrease()
        await device_hub.notify_all(
            {"type": "audio_quality_update", "preset": preset.as_dict()}
        )
        return {"audio_quality": preset.as_dict()}

    return router
