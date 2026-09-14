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
python scripts/demo-video/generate_audio.py   # needs OPENROUTER_API_KEY in env, not git
node scripts/demo-video/record_scenes.js
python scripts/demo-video/mux.py
```

Do not commit `audio/` or `output/`. Host the mp4 as a GitHub Release asset.
