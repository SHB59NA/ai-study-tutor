from dataclasses import dataclass
from io import BytesIO
import re

import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    page: int
    text: str


class DocumentIndex:
    """Page-aware lexical index with conservative grounding and robust reranking."""

    MIN_RELEVANCE_SCORE = 0.08
    LOW_COVERAGE_THRESHOLD = 0.60
    LOW_COVERAGE_SCORE_OVERRIDE = 0.35

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.char_vectorizer: TfidfVectorizer | None = None
        self.char_matrix = None
        self.language: str = "unknown"

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect whether text is primarily Arabic or English/Latin script."""
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        latin_chars = len(re.findall(r"[A-Za-z]", text))

        if arabic_chars == 0 and latin_chars == 0:
            return "unknown"
        return "arabic" if arabic_chars > latin_chars else "english"

    @staticmethod
    def _split_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
        clean = " ".join(text.split())
        if not clean:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(clean):
            end = min(len(clean), start + chunk_size)
            chunks.append(clean[start:end])
            if end == len(clean):
                break
            start = max(0, end - overlap)
        return chunks

    def load_pdf(self, data: bytes) -> int:
        reader = PdfReader(BytesIO(data))
        chunks: list[Chunk] = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            for chunk_text in self._split_text(text):
                chunks.append(Chunk(page=page_number, text=chunk_text))

        if not chunks:
            raise ValueError("No extractable text was found in the PDF.")

        self.chunks = chunks
        sample = " ".join(chunk.text for chunk in chunks[:50])
        self.language = self.detect_language(sample)

        # Word TF-IDF is used for the conservative evidence gate and query
        # vocabulary coverage. English stop words reduce generic overlap.
        stop_words = "english" if self.language == "english" else None
        self.vectorizer = TfidfVectorizer(
            stop_words=stop_words,
            ngram_range=(1, 2),
            lowercase=True,
        )
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in chunks])

        # Character n-grams are more tolerant of PDF extraction artifacts such
        # as split words (for example "chan ge" or "desalinat ed"). They are
        # used only to rank evidence after the word-level grounding gate passes.
        self.char_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            lowercase=True,
        )
        self.char_matrix = self.char_vectorizer.fit_transform(
            [chunk.text for chunk in chunks]
        )
        return len(chunks)

    def _query_coverage(self, question: str) -> float:
        """Estimate how much of the informative query vocabulary exists in the PDF index."""
        if self.vectorizer is None:
            return 0.0

        tokens = re.findall(r"(?u)\b\w\w+\b", question.lower())
        stop_words = self.vectorizer.get_stop_words() or set()
        informative = {token for token in tokens if token not in stop_words}
        if not informative:
            return 0.0

        vocabulary = self.vectorizer.vocabulary_
        known = sum(1 for token in informative if token in vocabulary)
        return known / len(informative)

    def search(
        self,
        question: str,
        top_k: int = 3,
        min_score: float | None = None,
    ) -> list[tuple[Chunk, float]]:
        if (
            not self.chunks
            or self.vectorizer is None
            or self.matrix is None
            or self.char_vectorizer is None
            or self.char_matrix is None
        ):
            raise RuntimeError("No document has been indexed yet.")

        word_query_vector = self.vectorizer.transform([question])
        if word_query_vector.nnz == 0:
            return []

        word_scores = cosine_similarity(word_query_vector, self.matrix).flatten()
        max_word_score = float(np.max(word_scores)) if word_scores.size else 0.0
        threshold = self.MIN_RELEVANCE_SCORE if min_score is None else float(min_score)

        if max_word_score < threshold:
            return []

        # Require most informative query terms to exist somewhere in the source.
        # This rejects questions that overlap on only one generic word while
        # retaining an override for an unusually strong lexical match.
        coverage = self._query_coverage(question)
        if (
            coverage < self.LOW_COVERAGE_THRESHOLD
            and max_word_score < self.LOW_COVERAGE_SCORE_OVERRIDE
        ):
            return []

        char_query_vector = self.char_vectorizer.transform([question])
        if char_query_vector.nnz == 0:
            ranking_scores = word_scores
        else:
            ranking_scores = cosine_similarity(
                char_query_vector,
                self.char_matrix,
            ).flatten()

        # Rank with extraction-tolerant character similarity, then diversify by
        # PDF page so Top-K evidence is not consumed by near-duplicate chunks
        # from the same page.
        ranked = np.argsort(ranking_scores)[::-1]
        results: list[tuple[Chunk, float]] = []
        seen_pages: set[int] = set()

        for index in ranked:
            score = float(ranking_scores[index])
            if score < threshold:
                continue

            chunk = self.chunks[int(index)]
            if chunk.page in seen_pages:
                continue

            results.append((chunk, score))
            seen_pages.add(chunk.page)
            if len(results) >= top_k:
                break

        return results
