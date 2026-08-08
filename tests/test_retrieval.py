from sklearn.feature_extraction.text import TfidfVectorizer

from app.retrieval import Chunk, DocumentIndex


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


def _english_test_index() -> DocumentIndex:
    index = DocumentIndex()
    index.language = "english"
    index.chunks = [
        Chunk(
            page=10,
            text=(
                "Climate change in Kuwait is expected to increase temperatures and affect rainfall. "
                "Water resources, coastal areas, and public health are vulnerable sectors."
            ),
        ),
        Chunk(
            page=20,
            text=(
                "The report discusses greenhouse gas emissions, adaptation planning, and environmental policy "
                "in Kuwait and around the world. Kuwait City is the capital and the document also discusses "
                "sunlight, solar energy, infrastructure, transport, and development planning."
            ),
        ),
    ]
    index.vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        lowercase=True,
    )
    index.matrix = index.vectorizer.fit_transform([chunk.text for chunk in index.chunks])
    return index


def test_retrieval_accepts_supported_question():
    index = _english_test_index()
    results = index.search("How will climate change affect temperature and rainfall in Kuwait?")
    assert results
    assert results[0][0].page == 10


def test_retrieval_rejects_unrelated_fifa_question():
    index = _english_test_index()
    results = index.search("Who won the FIFA World Cup in 2022?")
    assert results == []


def test_retrieval_rejects_partial_capital_overlap():
    index = _english_test_index()
    results = index.search("What is the capital of France?")
    assert results == []


def test_retrieval_rejects_partial_light_overlap():
    index = _english_test_index()
    results = index.search("What is the speed of light in vacuum?")
    assert results == []
