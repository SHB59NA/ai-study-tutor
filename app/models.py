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
