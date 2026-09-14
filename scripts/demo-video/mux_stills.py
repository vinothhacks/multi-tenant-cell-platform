"""Build the explaining video from Playwright stills + neural voice. Voice never overlaps motion (there is no motion track)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio"
STILLS = ROOT / "output" / "stills"
OUT = ROOT / "output" / "cell-platform-demo.mp4"
WORK = ROOT / "output" / "parts"
WORK.mkdir(parents=True, exist_ok=True)

SCENES = [
    "scene-01-problem",
    "scene-02-hosting",
    "scene-03-target",
    "scene-04-create",
    "scene-05-scale",
    "scene-06-move",
    "scene-07-release",
    "scene-08-break",
]


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def audio_path(slug: str) -> Path:
    for ext in (".mp3", ".wav", ".m4a"):
        p = AUDIO / f"{slug}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(slug)


def main() -> None:
    parts = []
    for i, slug in enumerate(SCENES):
        png = STILLS / f"{slug}.png"
        wav = audio_path(slug)
        if not png.exists():
            print(f"missing {png}", file=sys.stderr)
            sys.exit(2)
        narr = WORK / f"{i:02d}-narr.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(png),
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
                "-vf",
                "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                "-shortest",
                str(narr),
            ]
        )
        parts.append(narr)
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(OUT)])
    print(OUT)


if __name__ == "__main__":
    main()
