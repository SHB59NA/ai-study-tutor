from fastapi.testclient import TestClient
import pytest

import app.main as api
from app.session_store import SessionTutorStore
from examples.make_demo import make_demo_pdf


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "store", SessionTutorStore())
    with TestClient(api.app) as client:
        yield client


def session(client):
    response = client.post("/sessions")
    assert response.status_code == 201
    return {"X-Session-ID": response.json()["session_id"]}


def upload(client, headers):
    return client.post("/upload", headers=headers,
                       files={"file": ("sample.pdf", make_demo_pdf(), "application/pdf")})


def test_root_does_not_leak_document_or_progress(client):
    assert client.get("/health").status_code == 200
    assert "document_loaded" not in client.get("/").json()
    assert "mastery_score" not in client.get("/").json()


@pytest.mark.parametrize("endpoint", ["/progress", "/ask", "/review", "/quiz"])
def test_document_endpoints_require_session(client, endpoint):
    response = client.get(endpoint) if endpoint == "/progress" else client.post(endpoint, json={})
    assert response.status_code == 401


def test_invalid_token_does_not_allocate_state(client):
    assert client.get("/progress", headers={"X-Session-ID": "forged"}).status_code == 401
    assert api.store.active_sessions == 0


def test_upload_and_ask_with_visible_pdf_page(client):
    headers = session(client)
    assert upload(client, headers).status_code == 200
    answer = client.post("/ask", headers=headers, json={"question": "What does a primary key identify?"})
    assert answer.status_code == 200
    assert answer.json()["mode"] == "retrieval"
    assert answer.json()["sources"][0]["page"] == 3
    assert "uniquely identifies" in answer.json()["sources"][0]["text"]


def test_isolated_uploads_and_progress(client):
    first, second = session(client), session(client)
    assert first != second
    upload(client, first)
    response = client.post("/ask", headers=second, json={"question": "What does a primary key identify?"})
    assert response.status_code == 400
    assert client.get("/progress", headers=second).json()["attempts"] == 0


def test_arabic_language_is_forwarded(client):
    headers = session(client)
    upload(client, headers)
    result = client.post("/ask", headers=headers, json={
        "question": "Who won the lunar football tournament?", "language": "arabic"})
    assert result.status_code == 200
    assert result.json()["language"] == "arabic"
    assert "لم أجد" in result.json()["answer"]


@pytest.mark.parametrize("body", [
    {"question": "   "}, {"question": "x" * 1001},
    {"question": "valid question", "language": "xx"},
    {"question": "valid question", "top_k": 100},
    {"question": "valid question", "other_setting": True},
])
def test_reject_invalid_input(client, body):
    assert client.post("/ask", headers=session(client), json=body).status_code == 422


def test_bad_pdf_and_oversized_upload(client, monkeypatch):
    headers = session(client)
    assert client.post("/upload", headers=headers, files={"file": ("fake.pdf", b"hello")}).status_code == 400
    assert client.post("/upload", headers=headers, files={"file": ("x.txt", b"hello")}).status_code == 400
    monkeypatch.setattr(api, "MAX_PDF_BYTES", 256)
    assert client.post("/upload", headers=headers, files={"file": ("large.pdf", b"%PDF-" + b"0" * 256)}).status_code == 413


def test_deleting_session_invalidates_token(client):
    headers = session(client)
    upload(client, headers)
    assert client.delete("/session", headers=headers).status_code == 204
    assert client.get("/progress", headers=headers).status_code == 401


def test_no_provider_quiz_has_honest_status(client):
    headers = session(client)
    upload(client, headers)
    result = client.post("/quiz", headers=headers, json={"topic": "relational data"})
    assert result.status_code == 503
    assert "Gemini" in result.json()["detail"]


def test_quiz_question_cannot_be_read_across_sessions(client):
    headers = session(client)
    response = client.post("/quiz/answer", headers=headers,
                           json={"question_id": "another-users-question", "student_answer": "answer"})
    assert response.status_code == 404


def test_server_is_bounded(client, monkeypatch):
    monkeypatch.setattr(api, "store", SessionTutorStore(max_sessions=1))
    session(client)
    assert client.post("/sessions").status_code == 503


def test_provider_errors_do_not_expose_secrets(client):
    headers = session(client)
    upload(client, headers)
    tutor = api.store.get_existing(headers["X-Session-ID"]).tutor
    class UnavailableProvider:
        available = True
        def generate_quiz(self, **kwargs):
            raise Exception("confidential request credential: do-not-show")
    tutor.llm = UnavailableProvider()
    response = client.post("/quiz", headers=headers, json={"topic": "primary key"})
    assert response.status_code == 503
    assert "do-not-show" not in response.text
