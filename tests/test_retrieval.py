from app.retrieval import DocumentIndex


def test_split_text_creates_overlapping_chunks():
    text = "A" * 2000
    chunks = DocumentIndex._split_text(text, chunk_size=900, overlap=150)
    assert len(chunks) >= 3
    assert chunks[0][-150:] == chunks[1][:150]
