from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)


class SourceChunk(BaseModel):
    page: int
    score: float
    text: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
