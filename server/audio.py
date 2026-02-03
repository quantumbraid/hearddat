"""Audio routing and codec helpers.

This module handles routing between device audio producers/consumers and
browser-extension listeners. It's intentionally simple for phase-one build
verification and can be swapped with a lower-level audio engine later.
"""
from __future__ import annotations

import asyncio
import logging
import json
from typing import Dict, Set

import opuslib

logger = logging.getLogger(__name__)


class OpusCodec:
    """Optional Opus encode/decode wrapper.

    We keep this optional so the server can still run in PCM-only mode.
    """

    def __init__(
        self, sample_rate: int = 16000, channels: int = 1, enabled: bool = True
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._enabled = enabled
        self._encoder = None
        self._decoder = None
        if enabled:
            self._encoder = opuslib.Encoder(sample_rate, channels, opuslib.APPLICATION_AUDIO)
            self._decoder = opuslib.Decoder(sample_rate, channels)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def encode(self, pcm: bytes, frame_size: int = 320) -> bytes:
        if not self._enabled:
            return pcm
        return self._encoder.encode(pcm, frame_size)

    def decode(self, payload: bytes, frame_size: int = 320) -> bytes:
        if not self._enabled:
            return payload
        return self._decoder.decode(payload, frame_size)


class AudioRouter:
    """Routes audio frames between connected WebSocket clients."""

    def __init__(self) -> None:
        self._sources: Dict[str, Set[asyncio.Queue[bytes]]] = {}
        self._lock = asyncio.Lock()

    async def register(self, channel: str) -> asyncio.Queue[bytes]:
        """Register a consumer queue for a channel."""

        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=32)
        async with self._lock:
            self._sources.setdefault(channel, set()).add(queue)
        return queue

    async def unregister(self, channel: str, queue: asyncio.Queue[bytes]) -> None:
        """Remove a consumer from a channel."""

        async with self._lock:
            consumers = self._sources.get(channel, set())
            consumers.discard(queue)
            if not consumers:
                self._sources.pop(channel, None)

    async def broadcast(self, channel: str, payload: bytes) -> None:
        """Broadcast audio payload to all consumers of a channel."""

        async with self._lock:
            consumers = list(self._sources.get(channel, set()))
        for queue in consumers:
            if queue.full():
                try:
                    _ = queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await queue.put(payload)


async def pump_audio(queue: asyncio.Queue[bytes], websocket) -> None:
    """Forward queued audio packets to a WebSocket client."""

    while True:
        payload = await queue.get()
        await websocket.send_bytes(payload)


async def recv_audio(websocket, router: AudioRouter, channel: str) -> None:
    """Receive audio packets and broadcast them to listeners.

    The client can optionally send a JSON metadata frame first:
    {"format": "pcm", "sample_rate": 16000, "target_format": "opus"}.
    This lets the server transcode PCM -> Opus or Opus -> PCM when needed
    and provides the PCM fallback path for diagnostics.
    """

    codec: OpusCodec | None = None
    source_format = "pcm"
    target_format = "pcm"
    sample_rate = 16000

    first_message = await websocket.receive()
    if "text" in first_message:
        metadata = json.loads(first_message["text"])
        source_format = metadata.get("format", "pcm")
        target_format = metadata.get("target_format", source_format)
        sample_rate = int(metadata.get("sample_rate", 16000))
        if source_format != target_format:
            codec = OpusCodec(sample_rate=sample_rate, enabled=True)
    elif "bytes" in first_message:
        await router.broadcast(channel, first_message["bytes"])

    while True:
        payload = await websocket.receive_bytes()
        if codec and source_format == "pcm" and target_format == "opus":
            payload = codec.encode(payload)
        elif codec and source_format == "opus" and target_format == "pcm":
            payload = codec.decode(payload)
        await router.broadcast(channel, payload)
