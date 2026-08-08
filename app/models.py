from typing import Literal

from pydantic import BaseModel, Field


ExplanationLevel = Literal["beginner", "intermediate", "advanced"]
AnswerMode = Literal["gemini", "retrieval"]


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)
    level: ExplanationLevel = "intermediate"
    use_llm: bool = True


class SourceChunk(BaseModel):
    page: int
    score: float
    text: str


class AnswerResponse(BaseModel):
    answer: str
    level: ExplanationLevel
    mode: AnswerMode
    sources: list[SourceChunk]


class QuizRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    difficulty: ExplanationLevel = "intermediate"
    count: int = Field(default=3, ge=1, le=5)
    top_k: int = Field(default=5, ge=1, le=8)


class QuizQuestion(BaseModel):
    id: str
    question: str
    page: int


class QuizResponse(BaseModel):
    topic: str
    difficulty: ExplanationLevel
    questions: list[QuizQuestion]


class QuizAnswerRequest(BaseModel):
    question_id: str
    student_answer: str = Field(min_length=1, max_length=3000)


class QuizGradeResponse(BaseModel):
    score: float
    correct: bool
    feedback: str
    source_page: int
    mastery_score: float
    next_difficulty: ExplanationLevel
