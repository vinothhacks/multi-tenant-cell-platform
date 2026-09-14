from pathlib import Path


def test_narration_has_scene_blocks():
    text = Path("scripts/demo-video/narration.md").read_text(encoding="utf-8")
    assert text.count("## scene-") >= 7


def test_mux_script_is_sequential_not_parallel():
    src = Path("scripts/demo-video/mux.py").read_text(encoding="utf-8")
    assert "parts.extend([narr, action])" in src
    assert "shortest" in src
    assert "-an" in src


def test_learning_guide_exists():
    html = Path("docs/learn/guide.html")
    assert html.exists()
    body = html.read_text(encoding="utf-8")
    assert "DIAGRAM A" in body
    assert "DIAGRAM B" in body
    assert "cell-control-plane.onrender.com" in body
