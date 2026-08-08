from app.retrieval import Chunk
from app.tutor import StudyTutor


class FakeIndex:
    language = "english"

    def __init__(self, responses):
        self.responses = responses

    def search(self, question, top_k=3):
        return self.responses.get(question, [])[:top_k]


class FakeLLM:
    available = True

    def __init__(self, expanded_queries):
        self.expanded_queries = expanded_queries
        self.expand_calls = 0
        self.answer_sources = []

    def expand_retrieval_queries(self, text, target_language, max_queries=4):
        self.expand_calls += 1
        return self.expanded_queries[:max_queries]

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


def test_multi_part_answer_adds_missing_evidence_pages():
    question = (
        "How is climate change expected to affect Kuwait's temperature and rainfall, "
        "coastal areas, and public health?"
    )
    expanded = [
        "future temperature rainfall Kuwait",
        "coastal impacts Kuwait",
        "public health climate change Kuwait",
    ]
    responses = {
        question: [result(2, 0.32), result(29, 0.22), result(10, 0.19)],
        expanded[0]: [result(2, 0.31), result(68, 0.26)],
        expanded[1]: [result(47, 0.24), result(69, 0.23)],
        expanded[2]: [result(69, 0.29), result(10, 0.25)],
    }

    tutor = StudyTutor()
    tutor.index = FakeIndex(responses)
    tutor.llm = FakeLLM(expanded)

    answer, sources, mode = tutor.answer(question, top_k=3, use_llm=True)
    pages = [source["page"] for source in sources]

    assert answer == "grounded answer"
    assert mode == "gemini"
    assert tutor.llm.expand_calls == 1
    assert 68 in pages
    assert 69 in pages
    assert len(pages) <= 6


def test_single_part_answer_does_not_expand_queries():
    question = "What share of Kuwait's emissions came from the energy sector?"
    tutor = StudyTutor()
    tutor.index = FakeIndex({question: [result(52, 0.28)]})
    tutor.llm = FakeLLM(["unused expansion"])

    answer, sources, mode = tutor.answer(question, top_k=3, use_llm=True)

    assert answer == "grounded answer"
    assert mode == "gemini"
    assert [source["page"] for source in sources] == [52]
    assert tutor.llm.expand_calls == 0
