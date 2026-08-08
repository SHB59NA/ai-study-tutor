from app.retrieval import Chunk
from app.tutor import StudyTutor


class FakeIndex:
    language = "english"

    def __init__(self, responses):
        self.responses = responses
        self.search_calls = []

    def search(self, question, top_k=3):
        self.search_calls.append((question, top_k))
        return self.responses.get(question, [])[:top_k]


class FakeLLM:
    available = True

    def __init__(self):
        self.answer_sources = []

    def generate_answer(self, question, sources, level="intermediate", language="english"):
        self.answer_sources = sources
        return "grounded answer"


def result(page, score=0.2):
    return (Chunk(page=page, text=f"Evidence from page {page}"), score)


def test_multi_part_question_detection():
    assert StudyTutor._is_multi_part_question(
        "How will climate change affect temperature and rainfall, coastal areas, and public health?"
    )
    assert not StudyTutor._is_multi_part_question(
        "How will climate change affect temperature and rainfall?"
    )


def test_multi_part_answer_widens_evidence_candidates():
    question = (
        "How is climate change expected to affect Kuwait's temperature and rainfall, "
        "coastal areas, and public health?"
    )
    responses = {
        question: [
            result(2, 0.32),
            result(29, 0.22),
            result(10, 0.19),
            result(47, 0.18),
            result(69, 0.176),
            result(70, 0.175),
            result(68, 0.165),
            result(28, 0.163),
        ]
    }

    tutor = StudyTutor()
    tutor.index = FakeIndex(responses)
    tutor.llm = FakeLLM()

    answer, sources, mode = tutor.answer(question, top_k=3, use_llm=True)
    pages = [source["page"] for source in sources]

    assert answer == "grounded answer"
    assert mode == "gemini"
    assert tutor.index.search_calls == [(question, 3), (question, 8)]
    assert 68 in pages
    assert 69 in pages
    assert len(pages) == 8


def test_single_part_answer_keeps_requested_top_k():
    question = "What share of Kuwait's emissions came from the energy sector?"
    tutor = StudyTutor()
    tutor.index = FakeIndex({question: [result(52, 0.28), result(50, 0.25)]})
    tutor.llm = FakeLLM()

    answer, sources, mode = tutor.answer(question, top_k=3, use_llm=True)

    assert answer == "grounded answer"
    assert mode == "gemini"
    assert [source["page"] for source in sources] == [52, 50]
    assert tutor.index.search_calls == [(question, 3)]
