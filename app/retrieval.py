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
    """Page-aware lexical index with a conservative relevance gate."""

    MIN_RELEVANCE_SCORE = 0.08
    LOW_COVERAGE_THRESHOLD = 0.60
    LOW_COVERAGE_SCORE_OVERRIDE = 0.35

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
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

        # English stop words reduce false matches on generic words. Arabic keeps
        # the full lexical vocabulary. Cross-language requests are translated to
        # the detected source language by StudyTutor before retrieval.
        stop_words = "english" if self.language == "english" else None
        self.vectorizer = TfidfVectorizer(
            stop_words=stop_words,
            ngram_range=(1, 2),
            lowercase=True,
        )
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in chunks])
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
        if not self.chunks or self.vectorizer is None or self.matrix is None:
            raise RuntimeError("No document has been indexed yet.")

        query_vector = self.vectorizer.transform([question])
        if query_vector.nnz == 0:
            return []

        scores = cosine_similarity(query_vector, self.matrix).flatten()
        max_score = float(np.max(scores)) if scores.size else 0.0
        threshold = self.MIN_RELEVANCE_SCORE if min_score is None else float(min_score)

        if max_score < threshold:
            return []

        # Require most informative query terms to exist somewhere in the source.
        # This rejects questions that overlap on only one generic word (for
        # example "capital" or "light") while retaining an override for an
        # unusually strong lexical match.
        coverage = self._query_coverage(question)
        if (
            coverage < self.LOW_COVERAGE_THRESHOLD
            and max_score < self.LOW_COVERAGE_SCORE_OVERRIDE
        ):
            return []

        ranked = np.argsort(scores)[::-1][:top_k]
        results: list[tuple[Chunk, float]] = []
        for index in ranked:
            score = float(scores[index])
            if score < threshold:
                continue
            results.append((self.chunks[int(index)], score))
        return results
