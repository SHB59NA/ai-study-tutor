from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExplanationLevel = Literal["beginner", "intermediate", "advanced"]
AnswerMode = Literal["gemini", "retrieval"]
Language = Literal["english", "arabic"]


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class QuestionRequest(InputModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)
    level: ExplanationLevel = "intermediate"
    use_llm: bool = False  # Explicit opt-in before sending excerpts to a provider.
    language: Language = "english"


class SourceChunk(BaseModel):
    page: int
    score: float
    text: str


class AnswerResponse(BaseModel):
    answer: str
    level: ExplanationLevel
    mode: AnswerMode
    language: Language = "english"
    sources: list[SourceChunk]


class QuizRequest(InputModel):
    topic: str = Field(min_length=3, max_length=300)
    difficulty: ExplanationLevel = "intermediate"
    count: int = Field(default=3, ge=1, le=5)
    top_k: int = Field(default=5, ge=1, le=8)
    language: Language = "english"


class QuizQuestion(BaseModel):
    id: str
    question: str
    concept: str
    page: int
    language: Language = "english"


class QuizResponse(BaseModel):
    topic: str
    difficulty: ExplanationLevel
    questions: list[QuizQuestion]


class QuizAnswerRequest(InputModel):
    question_id: str = Field(min_length=1, max_length=64)
    student_answer: str = Field(min_length=1, max_length=3000)


class WeakConcept(BaseModel):
    concept: str
    attempts: int
    mastery: float


class QuizGradeResponse(BaseModel):
    score: float
    correct: bool
    feedback: str
    concept: str
    review_recommendation: str
    source_page: int
    mastery_score: float
    next_difficulty: ExplanationLevel
    weak_concepts: list[WeakConcept]
    language: Language = "english"


class ProgressResponse(BaseModel):
    mastery_score: float
    next_difficulty: ExplanationLevel
    attempts: int
    weak_concepts: list[WeakConcept]


class ReviewRequest(InputModel):
    concept: str | None = Field(default=None, min_length=1, max_length=300)
    level: ExplanationLevel | None = None
    top_k: int = Field(default=3, ge=1, le=5)
    language: Language = "english"
    use_llm: bool = False


class ReviewResponse(AnswerResponse):
    concept: str
