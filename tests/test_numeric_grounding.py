from app.llm import GeminiTutor


def test_unsupported_numeric_value_is_detected():
    question = "How will temperature change by 2071-2100 under RCP8.5?"
    sources = [
        {
            "page": 68,
            "text": (
                "Annual average temperatures show the greatest rise under RCP8.5, "
                "between 4.3 to 4.5 C by the 2071-2100 period."
            ),
        }
    ]
    answer = "Temperature is projected to rise by 4.5 to 5.5 C [p. 68]."

    unsupported = GeminiTutor.unsupported_numeric_values(answer, question, sources)

    assert unsupported == ["5.5"]


def test_supported_numeric_values_and_page_citations_pass():
    question = "How will temperature and rainfall change by 2071-2100 under RCP8.5?"
    sources = [
        {
            "page": 68,
            "text": (
                "Annual average temperatures rise between 4.3 to 4.5 C by 2071-2100. "
                "Rainfall decreases between 15% and 18%."
            ),
        }
    ]
    answer = (
        "Temperature rises by 4.3 to 4.5 C and rainfall falls by 15% to 18% "
        "by 2071-2100 under RCP8.5 [p. 68]."
    )

    unsupported = GeminiTutor.unsupported_numeric_values(answer, question, sources)

    assert unsupported == []


def test_numeric_normalization_handles_thousands_separators():
    question = "What was the reported amount?"
    sources = [{"page": 52, "text": "Net CO2 emissions were 83910.932 Gg."}]
    answer = "The reported amount was 83,910.932 Gg [p. 52]."

    unsupported = GeminiTutor.unsupported_numeric_values(answer, question, sources)

    assert unsupported == []


def test_page_number_is_not_treated_as_answer_fact():
    question = "What happened?"
    sources = [{"page": 69, "text": "About half of Boubyan Island may be inundated."}]
    answer = "About half of Boubyan Island may be inundated [p. 69]."

    unsupported = GeminiTutor.unsupported_numeric_values(answer, question, sources)

    assert unsupported == []


def test_derived_numeric_claim_is_rejected_when_not_in_source():
    question = "What is the coastal risk?"
    sources = [{"page": 69, "text": "About half of Boubyan Island may be inundated."}]
    answer = "About 50% of Boubyan Island may be inundated [p. 69]."

    unsupported = GeminiTutor.unsupported_numeric_values(answer, question, sources)

    assert unsupported == ["50"]
