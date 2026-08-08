import re
from uuid import uuid4

from app.learner import LearnerProgress
from app.llm import GeminiTutor
from app.retrieval import DocumentIndex
from app.upload_validation import validate_pdf_upload


class StudyTutor:
    MULTI_PART_SOURCE_LIMIT = 8

    def __init__(self) -> None:
        self.index = DocumentIndex()
        self.llm = GeminiTutor()
        self.document_name: str | None = None
        self.quiz_bank: dict[str, dict] = {}
        self.progress = LearnerProgress()

    @property
    def llm_available(self) -> bool:
        return self.llm.available

    @property
    def document_language(self) -> str:
        return self.index.language

    def load_document(self, filename: str, data: bytes) -> int:
        validate_pdf_upload(filename, data)
        chunk_count = self.index.load_pdf(data)
        self.document_name = filename
        self.quiz_bank.clear()
        self.progress = LearnerProgress()
        return chunk_count

    def _retrieval_query(self, text: str) -> str:
        """Translate a cross-language request into the detected PDF language for lexical search."""
        document_language = self.index.language
        query_language = DocumentIndex.detect_language(text)

        if (
            document_language in {"english", "arabic"}
            and query_language in {"english", "arabic"}
            and document_language != query_language
            and self.llm.available
        ):
            try:
                return self.llm.translate_for_retrieval(
                    text=text,
                    target_language=document_language,
                )
            except Exception:
                pass
        return text

    @staticmethod
    def _is_multi_part_question(text: str) -> bool:
        """Conservatively detect questions that contain several information needs."""
        lowered = text.casefold()
        if "," in text or "،" in text or ";" in text or "؛" in text:
            return True
        if lowered.count(" and ") >= 2:
            return True
        if lowered.count(" as well as ") >= 1:
            return True
        return False

    def _expand_multi_part_results(
        self,
        retrieval_query: str,
        base_results: list,
        top_k: int,
    ) -> list:
        """Add balanced focused evidence for distinct parts of a complex question."""
        if not self.llm.available:
            return base_results

        try:
            expanded_queries = self.llm.expand_retrieval_queries(
                text=retrieval_query,
                target_language=self.index.language,
                max_queries=4,
            )
        except Exception:
            return base_results

        max_sources = max(self.MULTI_PART_SOURCE_LIMIT, top_k)
        merged = list(base_results)
        seen_pages = {chunk.page for chunk, _ in merged}
        focused_groups: list[list] = []

        for query in expanded_queries:
            try:
                focused = self.index.search(query, top_k=top_k)
            except Exception:
                continue
            if focused:
                focused_groups.append(focused)

        for rank in range(top_k):
            for focused in focused_groups:
                if rank >= len(focused):
                    continue

                chunk, score = focused[rank]
                if chunk.page in seen_pages:
                    continue

                merged.append((chunk, score))
                seen_pages.add(chunk.page)
                if len(merged) >= max_sources:
                    return merged

        return merged

    def answer(
        self,
        question: str,
        top_k: int = 3,
        level: str = "intermediate",
        use_llm: bool = True,
        language: str = "english",
    ) -> tuple[str, list[dict], str]:
        retrieval_query = self._retrieval_query(question)
        results = self.index.search(retrieval_query, top_k=top_k)
        if not results:
            message = (
                "لم أجد معلومات كافية ومرتبطة بالسؤال في المصدر المرفوع."
                if language == "arabic"
                else "I could not find enough relevant information in the uploaded source to answer that question reliably."
            )
            return message, [], "retrieval"

        if self._is_multi_part_question(question):
            # A single Top-3 ranking can miss one facet of a compound question.
            # After the normal grounding gate passes, widen only the evidence
            # candidate set for multi-part questions. Single-part questions keep
            # the benchmarked Top-K behavior unchanged.
            candidate_k = max(top_k, self.MULTI_PART_SOURCE_LIMIT)
            widened = self.index.search(retrieval_query, top_k=candidate_k)
            if widened:
                results = widened

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
                    language=language,
                )
                return answer, sources, "gemini"
            except Exception:
                pass

        answer = (
            "المولد اللغوي غير متاح لهذا الطلب، لكن المقاطع الأكثر صلة من المصدر معروضة أدناه حتى تتمكن من مراجعتها مباشرة."
            if language == "arabic"
            else (
                "The generative tutor is not available for this request, but the most relevant "
                "source passages are included below so the answer can still be checked directly "
                "against the uploaded material."
            )
        )
        return answer, sources, "retrieval"

    def create_quiz(
        self,
        topic: str,
        difficulty: str = "intermediate",
        count: int = 3,
        top_k: int = 5,
        language: str = "english",
    ) -> list[dict]:
        if not self.llm.available:
            raise RuntimeError("Quiz mode requires GEMINI_API_KEY.")

        retrieval_topic = self._retrieval_query(topic)
        results = self.index.search(retrieval_topic, top_k=top_k)
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
            language=language,
        )

        public_questions: list[dict] = []
        for item in generated:
            question_id = uuid4().hex[:12]
            self.quiz_bank[question_id] = {
                "question": item["question"],
                "answer": item["answer"],
                "concept": item["concept"],
                "page": item["page"],
                "difficulty": difficulty,
                "language": language,
            }
            public_questions.append(
                {
                    "id": question_id,
                    "question": item["question"],
                    "concept": item["concept"],
                    "page": item["page"],
                    "language": language,
                }
            )
        return public_questions

    def grade_quiz_answer(self, question_id: str, student_answer: str) -> dict:
        item = self.quiz_bank.get(question_id)
        if item is None:
            raise RuntimeError("Unknown quiz question ID. Generate a new quiz first.")
        if not self.llm.available:
            raise RuntimeError("Answer grading requires GEMINI_API_KEY.")

        language = item.get("language", "english")
        grade = self.llm.grade_answer(
            question=item["question"],
            expected_answer=item["answer"],
            student_answer=student_answer,
            source_page=item["page"],
            language=language,
        )
        score = float(grade["score"])
        concept = item["concept"]
        self.progress.add_score(score, concept=concept)

        if language == "arabic":
            if score < 0.7:
                recommendation = (
                    f"راجع مفهوم '{concept}' باستخدام المادة حول صفحة PDF {item['page']}، "
                    "ثم جرّب سؤالاً آخر عن نفس المفهوم."
                )
            else:
                recommendation = (
                    f"إجابتك تظهر تقدماً جيداً في '{concept}'. تابع بالمستوى المقترح: "
                    f"{self.progress.next_difficulty}."
                )
        else:
            if score < 0.7:
                recommendation = (
                    f"Review '{concept}' using the material around PDF page {item['page']}, "
                    "then try another question on the same concept."
                )
            else:
                recommendation = (
                    f"Your answer shows good progress on '{concept}'. Continue with the "
                    f"recommended {self.progress.next_difficulty} difficulty."
                )

        return {
            "score": round(score, 3),
            "correct": score >= 0.7,
            "feedback": grade["feedback"],
            "concept": concept,
            "review_recommendation": recommendation,
            "source_page": item["page"],
            "mastery_score": round(self.progress.mastery_score, 3),
            "next_difficulty": self.progress.next_difficulty,
            "weak_concepts": self.progress.weak_concepts,
            "language": language,
        }

    def get_progress(self) -> dict:
        return {
            "mastery_score": round(self.progress.mastery_score, 3),
            "next_difficulty": self.progress.next_difficulty,
            "attempts": len(self.progress.scores),
            "weak_concepts": self.progress.weak_concepts,
        }

    def personalized_review(
        self,
        concept: str | None = None,
        level: str | None = None,
        top_k: int = 3,
        language: str = "english",
    ) -> tuple[str, str, list[dict], str, str]:
        selected_concept = concept or self.progress.weakest_concept
        if not selected_concept:
            raise RuntimeError(
                "No weak concept is available yet. Complete and submit at least one quiz answer first."
            )

        selected_level = level or self.progress.next_difficulty
        if language == "arabic":
            review_question = (
                f"اشرح مفهوم '{selected_concept}' لطالب يحتاج إلى مراجعة. "
                "ركز على الفكرة الأساسية وأهم التفاصيل المدعومة بالمصدر."
            )
        else:
            review_question = (
                f"Explain the concept '{selected_concept}' for a learner who needs review. "
                "Focus on the key idea and the most important details supported by the source."
            )

        answer, sources, mode = self.answer(
            review_question,
            top_k=top_k,
            level=selected_level,
            use_llm=True,
            language=language,
        )
        return selected_concept, answer, sources, mode, selected_level
