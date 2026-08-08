from app.session_store import SessionTutorStore


def test_sessions_are_isolated():
    store = SessionTutorStore()

    first = store.get("session-a")
    second = store.get("session-b")

    assert first is not second
    assert first.tutor is not second.tutor

    first.tutor.progress.add_score(0.2, concept="water resources")

    assert first.tutor.get_progress()["attempts"] == 1
    assert second.tutor.get_progress()["attempts"] == 0


def test_same_session_reuses_same_tutor():
    store = SessionTutorStore()

    first = store.get("session-a")
    again = store.get("session-a")

    assert first is again
    assert first.tutor is again.tutor


def test_session_cleanup_removes_state():
    store = SessionTutorStore()

    original = store.get("session-a")
    original.tutor.progress.add_score(0.2, concept="water resources")

    store.remove("session-a")
    replacement = store.get("session-a")

    assert replacement is not original
    assert replacement.tutor.get_progress()["attempts"] == 0
