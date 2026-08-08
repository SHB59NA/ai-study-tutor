from evaluation.answer_grounding_eval import (
    evaluate_answer_case,
    print_report,
    summarize,
)


def test_print_report_uses_summary_metric_names(capsys):
    case = {
        "id": "oos",
        "type": "out_of_scope",
        "question": "Unsupported question?",
    }
    result = evaluate_answer_case(
        case=case,
        answer="Unsupported.",
        sources=[],
        mode="retrieval",
    )
    metrics = summarize([result])

    print_report([result], metrics)
    output = capsys.readouterr().out

    assert "Out-of-source refusal rate: 100.0%" in output
    assert "Overall evaluated-case pass rate: 100.0%" in output
