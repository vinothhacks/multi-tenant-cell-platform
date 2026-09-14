"""Generate per-scene audio. Prefer OpenRouter when keyed; else Edge neural TTS."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio"
AUDIO.mkdir(exist_ok=True)
MODEL = os.getenv("OPENROUTER_TTS_MODEL", "fish-audio/s2.1-pro-free:free")
EDGE_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-AndrewNeural")


def scenes() -> list[tuple[str, str]]:
    text = (ROOT / "narration.md").read_text(encoding="utf-8")
    parts = re.split(r"^## ", text, flags=re.M)
    out = []
    for part in parts:
        lines = [ln for ln in part.strip().splitlines() if ln.strip()]
        if not lines:
            continue
        slug = lines[0].strip()
        body = " ".join(lines[1:]).strip()
        if slug.startswith("scene-"):
            out.append((slug, body))
    return out


def synth_openrouter(text: str, dest: Path) -> None:
    key = os.getenv("OPENROUTER_API_KEY")
    payload = {
        "model": MODEL,
        "input": text,
        "voice": "alloy",
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/audio/speech",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/vinothhacks/multi-tenant-cell-platform",
            "X-Title": "Cell Platform Demo",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


async def synth_edge(text: str, dest: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, EDGE_VOICE, rate="-8%", pitch="-2Hz")
    await communicate.save(str(dest))


def main() -> None:
    key = os.getenv("OPENROUTER_API_KEY")
    use_or = bool(key and key.strip())
    for slug, body in scenes():
        dest = AUDIO / (f"{slug}.mp3" if not use_or else f"{slug}.wav")
        print(f"synth {slug} via {'openrouter' if use_or else 'edge-tts'} -> {dest.name}", flush=True)
        if use_or:
            synth_openrouter(body, dest)
        else:
            asyncio.run(synth_edge(body, dest))
    print("ok")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"speech failed ({exc}). Refusing silent placeholders.", file=sys.stderr)
        raise
