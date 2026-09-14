from pathlib import Path


def test_narration_has_seven_scenes():
    text = Path("scripts/demo-video/narration.md").read_text(encoding="utf-8")
    assert text.count("## scene-") == 7


def test_mux_script_is_sequential_not_parallel():
    src = Path("scripts/demo-video/mux.py").read_text(encoding="utf-8")
    assert "parts.extend([narr, action])" in src
    assert "shortest" in src
    assert "-an" in src
