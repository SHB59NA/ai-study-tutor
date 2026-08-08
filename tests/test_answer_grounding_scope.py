from evaluation.answer_grounding_eval import (
    evaluate_answer_case,
    evaluate_fact,
    load_dataset,
    summarize,
)


def test_trailing_paragraph_citation_supports_compound_fact():
    fact = {
        "id": "co2_share",
        "patterns": [r"97\.2", r"83\s*,?\s*910\.932|83910\.932"],
        "citation_pages": [52],
    }
    answer = (
        "In 2016, carbon dioxide made up 97.2% of Kuwait's total greenhouse gas emissions. "
        "The reported amount was 83,910.932 Gg [p. 52]."
    )

    result = evaluate_fact(answer, fact)

    assert result.covered is True
    assert result.citation_supported is True


def test_trailing_bullet_citation_supports_earlier_sentence_in_same_item():
    fact = {
        "id": "boubyan_inundation",
        "patterns": [r"boubyan", r"half", r"inundat|underwater"],
        "citation_pages": [69],
    }
    answer = (
        '- **Extensive Inundation:** Boubyan Island is projected to be severely impacted by rising sea levels. '
        'In the highest scenario, about half of the island would be inundated [p. 10, p. 69].'
    )

    result = evaluate_fact(answer, fact)

    assert result.covered is True
    assert result.citation_supported is True


def test_legacy_generation_fallback_is_excluded_from_answer_quality_metrics():
    case = {
        "id": "multi",
        "type": "in_scope",
        "question": "Multi-part question?",
        "expected_facts": [
            {
                "id": "fact",
                "patterns": [r"4\.3", r"4\.5"],
                "citation_pages": [68],
            }
        ],
    }
    result = evaluate_answer_case(
        case=case,
        answer=(
            "The generative tutor is not available for this request, but the most relevant "
            "source passages are included below."
        ),
        sources=[{"page": 68}],
        mode="retrieval",
        generation_error="LegacyGenerationFallback: no generated answer",
    )

    metrics = summarize([result])

    assert metrics["evaluated_cases"] == 0
    assert metrics["generation_unavailable_cases"] == 1
    assert metrics["provider_error_cases"] == 0
    assert metrics["generation_success_rate"] == 0.0
    assert metrics["expected_fact_coverage"] is None
    assert metrics["expected_citation_support_rate"] is None


def test_climate_benchmark_accepts_duplicate_valid_evidence_pages():
    dataset = load_dataset("evaluation/kuwait_bur_answer_eval.json")
    cases = {case["id"]: case for case in dataset["cases"]}

    climate = cases["climate_projection"]
    facts = {fact["id"]: fact for fact in climate["expected_facts"]}

    assert facts["temperature_projection"]["citation_pages"] == [9, 68]
    assert facts["rainfall_projection"]["citation_pages"] == [9, 68]
