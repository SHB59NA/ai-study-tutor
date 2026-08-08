from app.retrieval import DocumentIndex


def test_split_text_creates_overlapping_chunks():
    text = "A" * 2000
    chunks = DocumentIndex._split_text(text, chunk_size=900, overlap=150)
    assert len(chunks) >= 3
    assert chunks[0][-150:] == chunks[1][:150]


def test_detect_language_identifies_english():
    assert DocumentIndex.detect_language("Climate change affects water resources.") == "english"


def test_detect_language_identifies_arabic():
    assert DocumentIndex.detect_language("تغير المناخ يؤثر على الموارد المائية في الكويت") == "arabic"


def test_detect_language_handles_non_text():
    assert DocumentIndex.detect_language("12345 !!!") == "unknown"
