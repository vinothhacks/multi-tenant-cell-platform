"""Generate per-scene WAV files via OpenRouter. Never logs the API key."""

from __future__ import annotations

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


def synth(text: str, dest: Path) -> None:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is not set (use a local .env; do not commit it)")
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
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    for slug, body in scenes():
        dest = AUDIO / f"{slug}.wav"
        print(f"synth {slug} -> {dest.name}", flush=True)
        try:
            synth(body, dest)
        except Exception as exc:
            print(f"OpenRouter speech API failed ({exc}). Writing a silent placeholder is not allowed to fake success.")
            raise
    print("ok")


if __name__ == "__main__":
    main()
