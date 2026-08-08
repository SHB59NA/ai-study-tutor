from app.llm import GeminiTutor
from app.retrieval import DocumentIndex


class StudyTutor:
    def __init__(self) -> None:
        self.index = DocumentIndex()
        self.llm = GeminiTutor()
        self.document_name: str | None = None

    @property
    def llm_available(self) -> bool:
        return self.llm.available

    def load_document(self, filename: str, data: bytes) -> int:
        chunk_count = self.index.load_pdf(data)
        self.document_name = filename
        return chunk_count

    def answer(
        self,
        question: str,
        top_k: int = 3,
        level: str = "intermediate",
        use_llm: bool = True,
    ) -> tuple[str, list[dict], str]:
        results = self.index.search(question, top_k=top_k)
        if not results:
            return (
                "I could not find enough relevant information in the uploaded source to answer that question reliably.",
                [],
                "retrieval",
            )

        sources = [
            {"page": chunk.page, "score": round(score, 4), "text": chunk.text}
            for chunk, score in results
        ]

        if use_llm and self.llm.available:
            try:
                answer = self.llm.generate_answer(
                    question=question,
                    sources=sources,
                    level=level,
                )
                return answer, sources, "gemini"
            except Exception:
                # Preserve a reliable source-grounded fallback if the provider is unavailable.
                pass

        answer = (
            "The generative tutor is not available for this request, but the most relevant "
            "source passages are included below so the answer can still be checked directly "
            "against the uploaded material."
        )
        return answer, sources, "retrieval"
