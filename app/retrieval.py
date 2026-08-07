from dataclasses import dataclass
from io import BytesIO

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
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
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
