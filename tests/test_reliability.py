from io import BytesIO
from types import SimpleNamespace

from pypdf import PdfWriter
import pytest

from app.learner import LearnerProgress
from app.llm import GeminiTutor
from app.retrieval import DocumentIndex
from app.session_store import SessionCapacityError, SessionTutorStore
from app.tutor import StudyTutor
from examples.make_demo import make_demo_pdf


def test_example_pdf_extracts_four_pages():
    index = DocumentIndex()
    assert index.load_pdf(make_demo_pdf()) == 4
    assert index.language == "english"


@pytest.mark.parametrize("bad_data", [b"%PDF-corrupted", b"", b"not PDF"])
def test_failed_upload_preserves_old_document(bad_data):
    tutor = StudyTutor()
    tutor.load_document("good.pdf", make_demo_pdf())
    with pytest.raises(ValueError):
        tutor.load_document("bad.pdf", bad_data)
    assert tutor.document_name == "good.pdf"
    assert tutor.index.search("primary key")[0][0].page == 3


def test_blank_or_scanned_pdf_is_explicitly_rejected():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO(); writer.write(buffer)
    with pytest.raises(ValueError, match="extractable text"):
        DocumentIndex().load_pdf(buffer.getvalue())


def test_encrypted_pdf_rejected():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")
    buffer = BytesIO(); writer.write(buffer)
    with pytest.raises(ValueError, match="Encrypted"):
        DocumentIndex().load_pdf(buffer.getvalue())


def test_page_limit_enforced(monkeypatch):
    monkeypatch.setattr(DocumentIndex, "MAX_PAGES", 2)
    with pytest.raises(ValueError, match="at most"):
        DocumentIndex().load_pdf(make_demo_pdf())


def test_text_limit_enforced(monkeypatch):
    monkeypatch.setattr(DocumentIndex, "MAX_TEXT_CHARS", 20)
    with pytest.raises(ValueError, match="too large"):
        DocumentIndex().load_pdf(make_demo_pdf())


@pytest.mark.parametrize("chunk_size, overlap", [(0, 0), (10, 10), (10, 11), (10, -1)])
def test_invalid_chunk_parameters_fail_instead_of_looping(chunk_size, overlap):
    with pytest.raises(ValueError):
        DocumentIndex._split_text("abc", chunk_size, overlap)


@pytest.mark.parametrize("top_k", [0, -1, 21, True, 2.5])
def test_invalid_top_k(top_k):
    with pytest.raises(ValueError):
        DocumentIndex().search("hello", top_k=top_k)


def test_offline_mode_never_translates_or_generates():
    tutor = StudyTutor()
    tutor.load_document("demo.pdf", make_demo_pdf())
    class ProviderMustNotRun:
        available = True
        def translate_for_retrieval(self, **kwargs):
            pytest.fail("Translation made an external call in offline mode")
        def generate_answer(self, **kwargs):
            pytest.fail("Generation made an external call in offline mode")
    tutor.llm = ProviderMustNotRun()
    _, _, mode = tutor.answer("ما هو المفتاح الأساسي؟", use_llm=False, language="arabic")
    assert mode == "retrieval"


def test_ttl_expiry_does_not_recreate_api_session():
    now = [0.0]
    store = SessionTutorStore(ttl_seconds=10, clock=lambda: now[0])
    token = store.create()
    now[0] = 11.0
    with pytest.raises(KeyError):
        store.get_existing(token)
    assert store.active_sessions == 0


def test_capacity_released_on_remove():
    store = SessionTutorStore(max_sessions=1)
    token = store.create()
    with pytest.raises(SessionCapacityError):
        store.create()
    store.remove(token)
    assert store.create() != token


def test_total_attempts_not_limited_to_moving_average_window():
    tutor = StudyTutor()
    for _ in range(15):
        tutor.progress.add_score(0.8, "keys")
    assert len(tutor.progress.scores) == 10
    assert tutor.get_progress()["attempts"] == 15


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_progress_is_rejected(score):
    with pytest.raises(ValueError):
        LearnerProgress().add_score(score)


def fake_provider(responses):
    model = GeminiTutor()
    pending = iter(responses)
    model.client = SimpleNamespace(models=SimpleNamespace(
        generate_content=lambda **kw: SimpleNamespace(text=next(pending))))
    return model


def test_missing_citation_is_repaired():
    model = fake_provider(["A primary key identifies a row.", "A primary key identifies a row [p. 3]."])
    assert "[p. 3]" in model.generate_answer("What is a primary key?", [{"page": 3, "text": "A primary key identifies a row."}])


def test_uncited_repair_fails_closed():
    model = fake_provider(["Unsupported answer", "Still no citation"])
    with pytest.raises(RuntimeError, match="without source citations"):
        model.generate_answer("What is a primary key?", [{"page": 3, "text": "A primary key identifies a row."}])


def test_refusal_does_not_need_fake_citation():
    refusal = "I cannot answer that reliably from the uploaded material."
    model = fake_provider([refusal])
    assert model.generate_answer("What is missing?", [{"page": 3, "text": "Sample."}]) == refusal


def test_unbracketed_page_mention_is_not_a_citation():
    assert GeminiTutor.cited_pages("See p. 3 in the draft") == []


@pytest.mark.parametrize("response", ['{"score": NaN}', '{"score": 2}', '{"score": -0.5}',
                                      '{"score": true}', '[]', '{"feedback": "hi"}'])
def test_invalid_provider_grade_rejected(response):
    model = fake_provider([response])
    with pytest.raises(RuntimeError):
        model.grade_answer("q", "ref", "student", 1)


def test_provider_failure_falls_back_without_sensitive_error_text():
    tutor = StudyTutor()
    tutor.load_document("demo.pdf", make_demo_pdf())
    class ProviderError(Exception):
        code = 429
    class FailedProvider:
        available = True
        def generate_answer(self, **kwargs):
            raise ProviderError("request contained secret-do-not-log")
    tutor.llm = FailedProvider()
    _, sources, mode = tutor.answer("What does a primary key identify?")
    assert mode == "retrieval" and sources
    assert "429" in tutor.last_generation_error
    assert "secret" not in tutor.last_generation_error


def test_question_numbers_are_not_evidence():
    result = GeminiTutor.unsupported_numeric_values(
        "The salary is 50000 [p. 1].", "Is the salary 50000?",
        [{"page": 1, "text": "The document describes a service desk."}])
    assert "50000" in result


def test_arabic_digits_match_source_values():
    result = GeminiTutor.unsupported_numeric_values(
        "القيمة ١٢٫٥ [p. 1].", "القيمة؟", [{"page": 1, "text": "The value is 12.5."}])
    assert result == []


def test_arabic_lexical_index_without_external_translation(monkeypatch):
    import app.retrieval as retrieval
    class ArabicPage:
        def extract_text(self):
            return "قاعدة البيانات تتكون من جداول والمفتاح الأساسي يميز كل سجل في الجدول"
    monkeypatch.setattr(retrieval, "PdfReader", lambda *args: SimpleNamespace(
        is_encrypted=False, pages=[ArabicPage()]))
    index = DocumentIndex()
    index.load_pdf(b"%PDF-test")
    assert index.language == "arabic"
    assert index.search("ما وظيفة المفتاح الأساسي؟")[0][0].page == 1
