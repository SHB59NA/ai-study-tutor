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

        # No English-only stop-word filter: the same lexical index can support
        # both Arabic and English documents. Cross-language queries are translated
        # into the detected document language by StudyTutor before retrieval.
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in chunks])
        return len(chunks)

    def search(self, question: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        if not self.chunks or self.vectorizer is None or self.matrix is None:
            raise RuntimeError("No document has been indexed yet.")

        query_vector = self.vectorizer.transform([question])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        ranked = np.argsort(scores)[::-1][:top_k]

        results: list[tuple[Chunk, float]] = []
        for index in ranked:
            score = float(scores[index])
            if score <= 0:
                continue
            results.append((self.chunks[int(index)], score))
        return results
