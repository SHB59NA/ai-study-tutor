from app.llm import GeminiTutor


def test_cited_pages_extracts_single_and_multiple_citations():
    text = "Supported here [p. 2] and also here [p. 3, p. 10]."
    assert GeminiTutor.cited_pages(text) == [2, 3, 10]


def test_invalid_citation_pages_rejects_unsupplied_pages():
    text = "Claim one [p. 2]. Claim two [p. 3, p. 10]."
    invalid = GeminiTutor.invalid_citation_pages(text, allowed_pages=[2, 10])
    assert invalid == [3]


def test_invalid_citation_pages_accepts_only_supplied_pages():
    text = "Claim one [p. 68]. Claim two [p. 69]."
    invalid = GeminiTutor.invalid_citation_pages(text, allowed_pages=[68, 69])
    assert invalid == []
