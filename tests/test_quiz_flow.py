from fastapi.testclient import TestClient
import app.main as api
from app.session_store import SessionTutorStore
from examples.make_demo import make_demo_pdf


class MockEducationProvider:
    available = True
    def __init__(self):
        self.language = None
    def generate_quiz(self, **kwargs):
        self.language = kwargs["language"]
        return [{"question": "What is a primary key?", "answer": "A unique row identifier.",
                 "concept": "primary keys", "page": 3}]
    def grade_answer(self, **kwargs):
        return {"score": 0.4, "feedback": "Explain how each row is distinguished."}
    def generate_answer(self, **kwargs):
        return "A primary key identifies each row [p. 3]."


def test_quiz_grade_progress_and_review_api(monkeypatch):
    monkeypatch.setattr(api, "store", SessionTutorStore())
    with TestClient(api.app) as client:
        token = client.post("/sessions").json()["session_id"]
        headers = {"X-Session-ID": token}
        client.post("/upload", headers=headers, files={"file": ("demo.pdf", make_demo_pdf())})
        tutor = api.store.get_existing(token).tutor
        provider = MockEducationProvider(); tutor.llm = provider
        quiz = client.post("/quiz", headers=headers, json={"topic": "primary key", "language": "arabic"})
        assert quiz.status_code == 200
        question = quiz.json()["questions"][0]
        assert "answer" not in question
        assert provider.language == "arabic"
        grade = client.post("/quiz/answer", headers=headers,
                            json={"question_id": question["id"], "student_answer": "a column"})
        assert grade.status_code == 200 and grade.json()["score"] == 0.4
        assert grade.json()["language"] == "arabic"
        progress = client.get("/progress", headers=headers).json()
        assert progress["attempts"] == 1 and progress["weak_concepts"][0]["concept"] == "primary keys"
        review = client.post("/review", headers=headers,
                             json={"concept": "primary key", "language": "english", "use_llm": False})
        assert review.status_code == 200
        assert review.json()["mode"] == "retrieval"
        assert review.json()["sources"]


def test_new_upload_resets_quiz_and_progress(monkeypatch):
    from app.tutor import StudyTutor
    tutor = StudyTutor(); tutor.load_document("first.pdf", make_demo_pdf())
    tutor.progress.add_score(0.3, "keys")
    tutor.quiz_bank["old"] = {"question": "old"}
    tutor.load_document("second.pdf", make_demo_pdf())
    assert tutor.quiz_bank == {} and tutor.get_progress()["attempts"] == 0
