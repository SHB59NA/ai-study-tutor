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


def _fit_test_index(chunks: list[Chunk]) -> DocumentIndex:
    index = DocumentIndex()
    index.language = "english"
    index.chunks = chunks
    texts = [chunk.text for chunk in chunks]

    index.vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        lowercase=True,
    )
    index.matrix = index.vectorizer.fit_transform(texts)

    index.char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        lowercase=True,
    )
    index.char_matrix = index.char_vectorizer.fit_transform(texts)
    return index


def _english_test_index() -> DocumentIndex:
    return _fit_test_index(
        [
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
    )


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


def test_character_reranking_tolerates_broken_pdf_words():
    index = _fit_test_index(
        [
            Chunk(
                page=1,
                text=(
                    "The report introduces climate change and public policy in Kuwait. "
                    "Public institutions coordinate national planning."
                ),
            ),
            Chunk(
                page=2,
                text=(
                    "Public health: With climate chan ge, increased heat stress and respiratory diseases "
                    "associated with dust storms represent health threats in Kuwait."
                ),
            ),
            Chunk(
                page=3,
                text="Climate committees and public authorities manage reporting in Kuwait.",
            ),
        ]
    )

    results = index.search("How could climate change affect public health in Kuwait?", top_k=3)
    assert any(chunk.page == 2 for chunk, _ in results)


def test_retrieval_returns_page_diverse_evidence():
    index = _fit_test_index(
        [
            Chunk(page=5, text="Climate change affects water resources in Kuwait."),
            Chunk(page=5, text="Climate change also affects rainfall and water supply in Kuwait."),
            Chunk(page=6, text="Water adaptation in Kuwait includes efficiency and leak reduction."),
        ]
    )

    results = index.search("How does climate change affect water in Kuwait?", top_k=3)
    pages = [chunk.page for chunk, _ in results]
    assert len(pages) == len(set(pages))
