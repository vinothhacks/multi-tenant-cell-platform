# Demo video

Voice and motion never overlap:

```text
narration + frozen frame
        ↓
silent Playwright action clip
        ↓
next narration
```

```bash
# terminals: control plane :8000 and frontend :3000
cd scripts/demo-video
npm install
npx playwright install chromium
pip install edge-tts
python generate_audio.py          # Edge neural voice, or OPENROUTER_API_KEY if set
node record_scenes.js             # silent Playwright clips
python mux.py                     # narration still, then silent action clips
python mux_stills.py              # Playwright MCP stills + neural voice (no overlap)
node print_guide.js               # docs/learn/cell-platform-end-to-end.pdf
```

Voice and motion never overlap. Do not commit `audio/` or `output/`. Host the mp4 as a GitHub Release asset. Do not commit API keys.
