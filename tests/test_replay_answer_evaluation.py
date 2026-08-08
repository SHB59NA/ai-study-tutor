import json

from evaluation.replay_answer_eval import replay_saved_report


def test_replay_saved_report_rescores_without_api(tmp_path):
    dataset = {
        "dataset_name": "test",
        "cases": [
            {
                "id": "in_scope",
                "type": "in_scope",
                "question": "What is the projection?",
                "expected_facts": [
                    {
                        "id": "projection",
                        "patterns": [r"4\.3", r"4\.5"],
                        "citation_pages": [68],
                    }
                ],
            },
            {
                "id": "oos",
                "type": "out_of_scope",
                "question": "Unsupported?",
            },
        ],
    }
    report = {
        "metrics": {},
        "results": [
            {
                "case_id": "in_scope",
                "mode": "gemini",
                "source_pages": [68],
                "answer": "Temperatures rise by 4.3 to 4.5 C [p. 68].",
            },
            {
                "case_id": "oos",
                "mode": "retrieval",
                "source_pages": [],
                "answer": "Unsupported by the uploaded source.",
            },
        ],
    }

    dataset_path = tmp_path / "dataset.json"
    report_path = tmp_path / "report.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
    report_path.write_text(json.dumps(report), encoding="utf-8")

    results, metrics = replay_saved_report(report_path, dataset_path)

    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is True
    assert metrics["provider_error_cases"] == 0
    assert metrics["expected_fact_coverage"] == 1.0
    assert metrics["expected_citation_support_rate"] == 1.0
    assert metrics["overall_evaluated_case_pass_rate"] == 1.0


def test_replay_saved_report_requires_all_dataset_cases(tmp_path):
    dataset = {
        "dataset_name": "test",
        "cases": [
            {
                "id": "one",
                "type": "out_of_scope",
                "question": "One?",
            },
            {
                "id": "two",
                "type": "out_of_scope",
                "question": "Two?",
            },
        ],
    }
    report = {
        "results": [
            {
                "case_id": "one",
                "mode": "retrieval",
                "source_pages": [],
                "answer": "Unsupported.",
            }
        ]
    }

    dataset_path = tmp_path / "dataset.json"
    report_path = tmp_path / "report.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
    report_path.write_text(json.dumps(report), encoding="utf-8")

    try:
        replay_saved_report(report_path, dataset_path)
    except ValueError as exc:
        assert "missing evaluation case" in str(exc).lower()
    else:
        raise AssertionError("Expected missing-case validation to fail.")
