"""Bounded, process-local state; not a persistent user-account database."""
from __future__ import annotations

from dataclasses import dataclass, field
from secrets import token_urlsafe
from threading import RLock
from time import monotonic
from typing import Callable

from app.tutor import StudyTutor


class SessionCapacityError(RuntimeError):
    """The bounded store is full; retry when another session expires."""


@dataclass
class TutorSession:
    tutor: StudyTutor = field(default_factory=StudyTutor)
    lock: RLock = field(default_factory=RLock)
    last_access: float = field(default_factory=monotonic)


class SessionTutorStore:
    """Each session owns one tutor; inactive sessions expire on store access."""

    def __init__(self, max_sessions: int = 32, ttl_seconds: float = 3600,
                 clock: Callable[[], float] = monotonic) -> None:
        if max_sessions < 1 or ttl_seconds <= 0:
            raise ValueError("Session capacity and lifetime must be positive.")
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._sessions: dict[str, TutorSession] = {}
        self._lock = RLock()

    def _prune(self) -> None:
        now = self._clock()
        for key, session in list(self._sessions.items()):
            if now - session.last_access <= self.ttl_seconds:
                continue
            if session.lock.acquire(blocking=False):
                try:
                    self._sessions.pop(key, None)
                finally:
                    session.lock.release()

    def get(self, session_hash: str | None) -> TutorSession:
        """Gradio-only: allocate on first trusted browser-session callback."""
        if not session_hash or len(session_hash) > 200:
            raise RuntimeError("A valid browser session is required.")
        with self._lock:
            self._prune()
            if session_hash not in self._sessions:
                if len(self._sessions) >= self.max_sessions:
                    raise SessionCapacityError("Session capacity reached. Please try again later.")
                self._sessions[session_hash] = TutorSession(last_access=self._clock())
            session = self._sessions[session_hash]
            session.last_access = self._clock()
            return session

    def create(self) -> str:
        """API: create an unguessable bearer session, never accept a client ID."""
        with self._lock:
            self._prune()
            if len(self._sessions) >= self.max_sessions:
                raise SessionCapacityError("Session capacity reached. Please try again later.")
            token = token_urlsafe(32)
            self._sessions[token] = TutorSession(last_access=self._clock())
            return token

    def get_existing(self, token: str | None) -> TutorSession:
        """API lookup never creates state for arbitrary or expired tokens."""
        with self._lock:
            self._prune()
            if not token or token not in self._sessions:
                raise KeyError("Unknown or expired session.")
            session = self._sessions[token]
            session.last_access = self._clock()
            return session

    def remove(self, session_hash: str | None) -> None:
        with self._lock:
            self._sessions.pop(session_hash, None)

    @property
    def active_sessions(self) -> int:
        with self._lock:
            self._prune()
            return len(self._sessions)
