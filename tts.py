"""
tts.py — Fish Audio synthesis, one request per sentence chunk.

The response is streamed so time-to-first-byte can be measured; the chunk is
returned whole because the browser decodes one complete MP3 per chunk.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx

log = logging.getLogger("jarvis.tts")

FISH_TTS_URL = "https://api.fish.audio/v1/tts"


@dataclass
class SynthResult:
    audio: bytes
    first_byte_sec: float
    total_sec: float


async def synthesize_chunk(text: str, *, api_key: str, voice_id: str,
                           client: Optional[httpx.AsyncClient] = None,
                           latency: str = "balanced", timeout: float = 15.0) -> Optional[SynthResult]:
    text = (text or "").strip()
    if not text:
        return None
    engine = os.getenv("TTS_ENGINE", "auto").lower()   # auto | fish | edge
    if engine != "edge" and api_key:
        r = await _fish_chunk(text, api_key=api_key, voice_id=voice_id,
                              client=client, latency=latency, timeout=timeout)
        if r is not None or engine == "fish":
            return r
    return await _edge_chunk(text, timeout=timeout)


async def _edge_chunk(text: str, *, timeout: float = 15.0) -> Optional[SynthResult]:
    """Free fallback voice: Microsoft Edge neural TTS (pip install edge-tts).
    Voice set by EDGE_VOICE, default en-GB-RyanNeural (British male)."""
    try:
        import edge_tts
    except ImportError:
        log.error("edge-tts not installed; run: pip install edge-tts")
        return None
    voice = os.getenv("EDGE_VOICE", "en-GB-RyanNeural")
    t0 = time.monotonic()
    first: Optional[float] = None
    buf = bytearray()
    try:
        async def run():
            nonlocal first
            async for part in edge_tts.Communicate(text, voice).stream():
                if part.get("type") == "audio":
                    if first is None:
                        first = time.monotonic() - t0
                    buf.extend(part["data"])
        await asyncio.wait_for(run(), timeout=timeout)
    except Exception as e:
        log.error(f"edge TTS error: {e}")
        return None
    if not buf:
        return None
    return SynthResult(bytes(buf), first or 0.0, time.monotonic() - t0)


async def _fish_chunk(text: str, *, api_key: str, voice_id: str,
                      client: Optional[httpx.AsyncClient] = None,
                      latency: str = "balanced", timeout: float = 15.0) -> Optional[SynthResult]:
    own = client is None
    client = client or httpx.AsyncClient(timeout=timeout)
    t0 = time.monotonic()
    first: Optional[float] = None
    buf = bytearray()
    try:
        async with client.stream(
            "POST", FISH_TTS_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"text": text, "reference_id": voice_id, "format": "mp3", "mp3_bitrate": 128, "latency": latency},
            timeout=timeout,
        ) as resp:
            if resp.status_code != 200:
                log.error(f"TTS {resp.status_code} for {text[:40]!r}")
                return None
            async for part in resp.aiter_bytes():
                if first is None:
                    first = time.monotonic() - t0
                buf.extend(part)
    except (httpx.HTTPError, OSError) as e:
        log.error(f"TTS error: {e}")
        return None
    finally:
        if own:
            try:
                await client.aclose()
            except Exception as e:      # never turn a clean None into an exception
                log.debug(f"TTS client close failed: {e}")
    if not buf:
        return None
    return SynthResult(bytes(buf), first if first is not None else 0.0, time.monotonic() - t0)
