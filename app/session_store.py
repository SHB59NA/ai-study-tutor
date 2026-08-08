from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from app.tutor import StudyTutor


@dataclass
class TutorSession:
    """State owned by exactly one Gradio browser session."""

    tutor: StudyTutor = field(default_factory=StudyTutor)
    lock: RLock = field(default_factory=RLock)


class SessionTutorStore:
    """Thread-safe in-memory registry of per-session StudyTutor instances."""

    def __init__(self) -> None:
        self._sessions: dict[str, TutorSession] = {}
        self._lock = RLock()

    def get(self, session_hash: str | None) -> TutorSession:
        if not session_hash:
            raise RuntimeError("A valid Gradio session is required.")

        with self._lock:
            session = self._sessions.get(session_hash)
            if session is None:
                session = TutorSession()
                self._sessions[session_hash] = session
            return session

    def remove(self, session_hash: str | None) -> None:
        if not session_hash:
            return

        with self._lock:
            self._sessions.pop(session_hash, None)

    @property
    def active_sessions(self) -> int:
        with self._lock:
            return len(self._sessions)
