from evaluation.answer_grounding_eval import (
    evaluate_answer_case,
    evaluate_fact,
    load_dataset,
    summarize,
)


def test_answer_dataset_loads_expected_cases():
    dataset = load_dataset("evaluation/kuwait_bur_answer_eval.json")
    assert dataset["dataset_name"] == "Kuwait BUR Answer Grounding Evaluation v1"
    assert len(dataset["cases"]) == 7


def test_fact_coverage_and_expected_citation_support_pass():
    fact = {
        "id": "temperature_projection",
        "patterns": [r"4\.3", r"4\.5"],
        "citation_pages": [68],
    }
    answer = "Temperatures are projected to rise by 4.3 to 4.5 C [p. 68]."
    result = evaluate_fact(answer, fact)
    assert result.covered is True
    assert result.citation_supported is True


def test_fact_support_can_span_multiple_cited_sentences():
    fact = {
        "id": "energy_dominant",
        "patterns": [r"energy(?:-related activities| sector)", r"95\.6"],
        "citation_pages": [50, 52],
    }
    answer = (
        "Energy-related activities produced the dominant share [p. 50]. "
        "They represented approximately 95.6% of emissions [p. 50]."
    )
    result = evaluate_fact(answer, fact)
    assert result.covered is True
    assert result.citation_supported is True


def test_each_fact_pattern_needs_local_expected_citation():
    fact = {
        "id": "energy_dominant",
        "patterns": [r"energy(?:-related activities| sector)", r"95\.6"],
        "citation_pages": [50, 52],
    }
    answer = (
        "Energy-related activities produced the dominant share [p. 50]. "
        "They represented approximately 95.6% of emissions [p. 62]."
    )
    result = evaluate_fact(answer, fact)
    assert result.covered is True
    assert result.citation_supported is False


def test_fact_coverage_without_expected_citation_support_fails_support():
    fact = {
        "id": "temperature_projection",
        "patterns": [r"4\.3", r"4\.5"],
        "citation_pages": [68],
    }
    answer = "Temperatures are projected to rise by 4.3 to 4.5 C [p. 10]."
    result = evaluate_fact(answer, fact)
    assert result.covered is True
    assert result.citation_supported is False


def test_invalid_citation_page_fails_in_scope_case():
    case = {
        "id": "sample",
        "type": "in_scope",
        "question": "Sample?",
        "expected_facts": [
            {
                "id": "temperature_projection",
                "patterns": [r"4\.3", r"4\.5"],
                "citation_pages": [68],
            }
        ],
    }
    result = evaluate_answer_case(
        case=case,
        answer="Temperatures rise by 4.3 to 4.5 C [p. 68, p. 99].",
        sources=[{"page": 68, "text": "source", "score": 0.2}],
        mode="gemini",
    )
    assert result.passed is False
    assert result.invalid_citation_pages == [99]


def test_generation_error_is_reported_for_grounded_fallback():
    case = {
        "id": "sample",
        "type": "in_scope",
        "question": "Sample?",
        "expected_facts": [
            {
                "id": "temperature_projection",
                "patterns": [r"4\.3", r"4\.5"],
                "citation_pages": [68],
            }
        ],
    }
    result = evaluate_answer_case(
        case=case,
        answer="Fallback.",
        sources=[{"page": 68, "text": "source", "score": 0.2}],
        mode="retrieval",
        generation_error="RuntimeError: example failure",
    )
    assert result.passed is False
    assert result.generation_error == "RuntimeError: example failure"
    assert "generation error" in result.reason


def test_out_of_scope_clean_rejection_passes():
    case = {
        "id": "oos",
        "type": "out_of_scope",
        "question": "Who won the World Cup?",
    }
    result = evaluate_answer_case(
        case=case,
        answer="I could not find enough relevant information in the uploaded source to answer that question reliably.",
        sources=[],
        mode="retrieval",
    )
    assert result.passed is True


def test_summary_aggregates_fact_and_case_metrics():
    in_scope_case = {
        "id": "sample",
        "type": "in_scope",
        "question": "Sample?",
        "expected_facts": [
            {
                "id": "temperature_projection",
                "patterns": [r"4\.3", r"4\.5"],
                "citation_pages": [68],
            }
        ],
    }
    oos_case = {"id": "oos", "type": "out_of_scope", "question": "OOS?"}

    in_scope = evaluate_answer_case(
        case=in_scope_case,
        answer="Temperatures rise by 4.3 to 4.5 C [p. 68].",
        sources=[{"page": 68, "text": "source", "score": 0.2}],
        mode="gemini",
    )
    out_scope = evaluate_answer_case(
        case=oos_case,
        answer="Unsupported.",
        sources=[],
        mode="retrieval",
    )

    metrics = summarize([in_scope, out_scope])
    assert metrics["total_cases"] == 2
    assert metrics["evaluated_cases"] == 2
    assert metrics["provider_error_cases"] == 0
    assert metrics["expected_fact_coverage"] == 1.0
    assert metrics["expected_citation_support_rate"] == 1.0
    assert metrics["citation_validity_case_rate"] == 1.0
    assert metrics["out_of_scope_refusal_rate"] == 1.0
    assert metrics["overall_evaluated_case_pass_rate"] == 1.0


def test_provider_quota_error_is_excluded_from_quality_metrics():
    in_scope_case = {
        "id": "sample",
        "type": "in_scope",
        "question": "Sample?",
        "expected_facts": [
            {
                "id": "temperature_projection",
                "patterns": [r"4\.3", r"4\.5"],
                "citation_pages": [68],
            }
        ],
    }
    oos_case = {"id": "oos", "type": "out_of_scope", "question": "OOS?"}

    provider_error = evaluate_answer_case(
        case=in_scope_case,
        answer="Fallback.",
        sources=[{"page": 68, "text": "source", "score": 0.2}],
        mode="retrieval",
        generation_error="ClientError: 429 RESOURCE_EXHAUSTED: quota exceeded",
    )
    out_scope = evaluate_answer_case(
        case=oos_case,
        answer="Unsupported.",
        sources=[],
        mode="retrieval",
    )

    metrics = summarize([provider_error, out_scope])
    assert metrics["total_cases"] == 2
    assert metrics["evaluated_cases"] == 1
    assert metrics["provider_error_cases"] == 1
    assert metrics["evaluated_in_scope_cases"] == 0
    assert metrics["expected_fact_coverage"] is None
    assert metrics["expected_citation_support_rate"] is None
    assert metrics["citation_validity_case_rate"] is None
    assert metrics["out_of_scope_refusal_rate"] == 1.0
    assert metrics["overall_evaluated_case_pass_rate"] == 1.0
