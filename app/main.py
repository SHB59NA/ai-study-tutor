from fastapi import FastAPI, File, HTTPException, UploadFile

from app.models import (
    AnswerResponse,
    ProgressResponse,
    QuestionRequest,
    QuizAnswerRequest,
    QuizGradeResponse,
    QuizRequest,
    QuizResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.tutor import StudyTutor

app = FastAPI(
    title="AI Study Tutor",
    description="A source-grounded AI tutor for educational materials.",
    version="0.4.0",
)

tutor = StudyTutor()


@app.get("/")
def root() -> dict:
    return {
        "name": "AI Study Tutor",
        "version": "0.4.0",
        "status": "ready",
        "document_loaded": tutor.document_name,
        "llm_available": tutor.llm_available,
        "mastery_score": round(tutor.progress.mastery_score, 3),
        "recommended_difficulty": tutor.progress.next_difficulty,
        "weak_concepts": tutor.progress.weak_concepts,
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        chunk_count = tutor.load_document(file.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to process the PDF.") from exc

    return {
        "message": "Document indexed successfully.",
        "filename": file.filename,
        "chunks": chunk_count,
    }


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest) -> AnswerResponse:
    if tutor.document_name is None:
        raise HTTPException(status_code=400, detail="Upload a PDF before asking a question.")

    try:
        answer, sources, mode = tutor.answer(
            request.question,
            top_k=request.top_k,
            level=request.level,
            use_llm=request.use_llm,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AnswerResponse(
        answer=answer,
        level=request.level,
        mode=mode,
        sources=sources,
    )


@app.post("/quiz", response_model=QuizResponse)
def create_quiz(request: QuizRequest) -> QuizResponse:
    if tutor.document_name is None:
        raise HTTPException(status_code=400, detail="Upload a PDF before generating a quiz.")

    try:
        questions = tutor.create_quiz(
            topic=request.topic,
            difficulty=request.difficulty,
            count=request.count,
            top_k=request.top_k,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to generate the quiz.") from exc

    return QuizResponse(
        topic=request.topic,
        difficulty=request.difficulty,
        questions=questions,
    )


@app.post("/quiz/answer", response_model=QuizGradeResponse)
def grade_quiz_answer(request: QuizAnswerRequest) -> QuizGradeResponse:
    try:
        result = tutor.grade_quiz_answer(
            question_id=request.question_id,
            student_answer=request.student_answer,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to grade the answer.") from exc

    return QuizGradeResponse(**result)


@app.get("/progress", response_model=ProgressResponse)
def learner_progress() -> ProgressResponse:
    return ProgressResponse(**tutor.get_progress())


@app.post("/review", response_model=ReviewResponse)
def personalized_review(request: ReviewRequest) -> ReviewResponse:
    if tutor.document_name is None:
        raise HTTPException(status_code=400, detail="Upload a PDF before requesting a review.")

    try:
        concept, answer, sources, mode, level = tutor.personalized_review(
            concept=request.concept,
            level=request.level,
            top_k=request.top_k,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReviewResponse(
        concept=concept,
        answer=answer,
        level=level,
        mode=mode,
        sources=sources,
    )
