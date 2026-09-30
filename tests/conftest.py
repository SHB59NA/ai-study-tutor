import pytest


@pytest.fixture(autouse=True)
def offline_provider(monkeypatch):
    """Unit/integration tests must never spend quota or send data to a model."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GRADIO_ANALYTICS_ENABLED", "False")
