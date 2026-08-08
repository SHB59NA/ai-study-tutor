from app.retrieval import Chunk
from evaluation.retrieval_eval import evaluate_index, load_dataset, summarize


class FakeIndex:
    def __init__(self, responses):
        self.responses = responses

    def search(self, question, top_k=3):
        return self.responses.get(question, [])[:top_k]


def test_load_dataset_accepts_benchmark():
    dataset = load_dataset("evaluation/kuwait_bur_eval.json")
    assert dataset["dataset_name"] == "Kuwait BUR Retrieval Evaluation v1"
    assert len(dataset["cases"]) == 13


def test_evaluation_scores_page_hits_and_rejections():
    dataset = {
        "cases": [
            {
                "id": "supported",
                "type": "in_scope",
                "question": "supported question",
                "expected_pages": [10],
            },
            {
                "id": "unsupported",
                "type": "out_of_scope",
                "question": "unsupported question",
                "expected_pages": [],
            },
        ]
    }
    index = FakeIndex(
        {
            "supported question": [(Chunk(page=10, text="evidence"), 0.42)],
            "unsupported question": [],
        }
    )

    results = evaluate_index(index, dataset, top_k=3)
    metrics = summarize(results)

    assert all(item.passed for item in results)
    assert metrics["top3_page_hit_rate"] == 1.0
    assert metrics["out_of_scope_rejection_rate"] == 1.0
    assert metrics["overall_case_pass_rate"] == 1.0


def test_wrong_page_is_counted_as_failure():
    dataset = {
        "cases": [
            {
                "id": "wrong-page",
                "type": "in_scope",
                "question": "question",
                "expected_pages": [20],
            }
        ]
    }
    index = FakeIndex({"question": [(Chunk(page=7, text="wrong evidence"), 0.3)]})

    results = evaluate_index(index, dataset, top_k=3)
    metrics = summarize(results)

    assert results[0].passed is False
    assert metrics["top3_page_hit_rate"] == 0.0
