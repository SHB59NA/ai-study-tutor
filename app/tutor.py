from uuid import uuid4

from app.learner import LearnerProgress
from app.llm import GeminiTutor
from app.retrieval import DocumentIndex


class StudyTutor:
    def __init__(self) -> None:
        self.index = DocumentIndex()
        self.llm = GeminiTutor()
        self.document_name: str | None = None
        self.quiz_bank: dict[str, dict] = {}
        self.progress = LearnerProgress()

    @property
    def llm_available(self) -> bool:
        return self.llm.available

    def load_document(self, filename: str, data: bytes) -> int:
        chunk_count = self.index.load_pdf(data)
        self.document_name = filename
        self.quiz_bank.clear()
        self.progress = LearnerProgress()
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
                pass

        answer = (
            "The generative tutor is not available for this request, but the most relevant "
            "source passages are included below so the answer can still be checked directly "
            "against the uploaded material."
        )
        return answer, sources, "retrieval"

    def create_quiz(
        self,
        topic: str,
        difficulty: str = "intermediate",
        count: int = 3,
        top_k: int = 5,
    ) -> list[dict]:
        if not self.llm.available:
            raise RuntimeError("Quiz mode requires GEMINI_API_KEY.")

        results = self.index.search(topic, top_k=top_k)
        if not results:
            raise RuntimeError("I could not find enough material for that quiz topic.")

        sources = [
            {"page": chunk.page, "score": round(score, 4), "text": chunk.text}
            for chunk, score in results
        ]
        generated = self.llm.generate_quiz(
            topic=topic,
            sources=sources,
            difficulty=difficulty,
            count=count,
        )

        public_questions: list[dict] = []
        for item in generated:
            question_id = uuid4().hex[:12]
            self.quiz_bank[question_id] = {
                "question": item["question"],
                "answer": item["answer"],
                "page": item["page"],
                "difficulty": difficulty,
            }
            public_questions.append(
                {
                    "id": question_id,
                    "question": item["question"],
                    "page": item["page"],
                }
            )
        return public_questions

    def grade_quiz_answer(self, question_id: str, student_answer: str) -> dict:
        item = self.quiz_bank.get(question_id)
        if item is None:
            raise RuntimeError("Unknown quiz question ID. Generate a new quiz first.")
        if not self.llm.available:
            raise RuntimeError("Answer grading requires GEMINI_API_KEY.")

        grade = self.llm.grade_answer(
            question=item["question"],
            expected_answer=item["answer"],
            student_answer=student_answer,
            source_page=item["page"],
        )
        score = float(grade["score"])
        self.progress.add_score(score)

        return {
            "score": round(score, 3),
            "correct": score >= 0.7,
            "feedback": grade["feedback"],
            "source_page": item["page"],
            "mastery_score": round(self.progress.mastery_score, 3),
            "next_difficulty": self.progress.next_difficulty,
        }
