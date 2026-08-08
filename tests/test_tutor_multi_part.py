from app.retrieval import Chunk
from app.tutor import StudyTutor


class FakeIndex:
    language = "english"

    def __init__(self):
        self.calls = []

    def search(self, question, top_k=3):
        self.calls.append(top_k)
        return [
            (Chunk(page=page, text=f"evidence page {page}"), 0.5)
            for page in range(1, top_k + 1)
        ]


class FakeLLM:
    available = False


def test_multi_part_answer_widens_evidence_candidates():
    tutor = StudyTutor()
    tutor.index = FakeIndex()
    tutor.llm = FakeLLM()

    _, sources, mode = tutor.answer(
        "How are temperature and rainfall, coastal areas, and public health affected?",
        top_k=3,
        use_llm=False,
    )

    assert tutor.index.calls == [3, StudyTutor.MULTI_PART_SOURCE_LIMIT]
    assert len(sources) == StudyTutor.MULTI_PART_SOURCE_LIMIT
    assert mode == "retrieval"


def test_single_part_answer_keeps_requested_top_k():
    tutor = StudyTutor()
    tutor.index = FakeIndex()
    tutor.llm = FakeLLM()

    _, sources, mode = tutor.answer(
        "What is the energy sector share?",
        top_k=3,
        use_llm=False,
    )

    assert tutor.index.calls == [3]
    assert len(sources) == 3
    assert mode == "retrieval"
