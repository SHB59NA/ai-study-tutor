"""Test UI callbacks without a browser or a paid model."""
from types import SimpleNamespace
from pathlib import Path

import demo
from app.session_store import SessionTutorStore


def test_ui_example_ask_progress_clear(monkeypatch):
    monkeypatch.setattr(demo, "session_store", SessionTutorStore())
    request = SimpleNamespace(session_hash="browser-test")
    assert "Example ready" in demo.load_example("English", request)
    result = list(demo.ask_tutor("What does a primary key identify?", "beginner", "English", False, request))
    assert "Retrieval-only mode selected" in result[-1][0]
    assert "PDF page 3" in result[-1][1]
    assert "Not assessed yet" in demo.show_progress("English", request)
    assert "لم يتم التقييم" in demo.show_progress("العربية", request)
    assert len(demo.clear_session(request)) == 13
    assert demo.session_store.active_sessions == 0


def test_cpu_entrypoint_has_no_spaces_or_public_tunnel():
    entry = Path("app.py").read_text()
    assert "import spaces" not in entry
    assert "share=True" not in Path("demo.py").read_text()
