from app.retrieval import DocumentIndex


class StudyTutor:
    def __init__(self) -> None:
        self.index = DocumentIndex()
        self.document_name: str | None = None

    def load_document(self, filename: str, data: bytes) -> int:
        chunk_count = self.index.load_pdf(data)
        self.document_name = filename
        return chunk_count

    def answer(self, question: str, top_k: int = 3) -> tuple[str, list[dict]]:
        results = self.index.search(question, top_k=top_k)
        if not results:
            return (
                "I could not find enough relevant information in the uploaded source to answer that question reliably.",
                [],
            )

        sources = [
            {"page": chunk.page, "score": round(score, 4), "text": chunk.text}
            for chunk, score in results
        ]

        answer = (
            "Based on the uploaded study material, the most relevant source passages are listed below. "
            "This first MVP uses transparent retrieval rather than generating unsupported content."
        )
        return answer, sources
