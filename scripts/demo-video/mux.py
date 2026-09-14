"""Mux silent action clips with preceding narration. No overlapping tracks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio"
CLIPS = ROOT / "output" / "clips"
OUT = ROOT / "output" / "cell-platform-demo.mp4"
OUT.parent.mkdir(exist_ok=True)

SCENES = [
    "scene-01-problem",
    "scene-02-target",
    "scene-03-create",
    "scene-04-scale",
    "scene-05-move",
    "scene-06-release",
    "scene-07-break",
]


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def main() -> None:
    parts = []
    work = ROOT / "output" / "parts"
    work.mkdir(parents=True, exist_ok=True)
    for i, slug in enumerate(SCENES):
        wav = AUDIO / f"{slug}.wav"
        clip = CLIPS / f"{slug}.webm"
        if not wav.exists() or not clip.exists():
            print(f"missing {wav.name} or {clip.name}", file=sys.stderr)
            sys.exit(2)
        still = work / f"{slug}-still.png"
        narr = work / f"{i:02d}-narr.mp4"
        action = work / f"{i:02d}-action.mp4"
        run(["ffmpeg", "-y", "-ss", "0", "-i", str(clip), "-frames:v", "1", str(still)])
        run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(still),
                "-i",
                str(wav),
                "-c:v",
                "libx264",
                "-tune",
                "stillimage",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
                "-shortest",
                str(narr),
            ]
        )
        run(["ffmpeg", "-y", "-i", str(clip), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(action)])
        parts.extend([narr, action])
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(OUT)])
    print(OUT)


if __name__ == "__main__":
    main()
