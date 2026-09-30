"""Single-process demo API with explicit, isolated bearer sessions."""
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.models import (
    AnswerResponse, ProgressResponse, QuestionRequest, QuizAnswerRequest,
    QuizGradeResponse, QuizRequest, QuizResponse, ReviewRequest, ReviewResponse,
)
from app.session_store import SessionCapacityError, SessionTutorStore, TutorSession
from app.upload_validation import MAX_PDF_BYTES

app = FastAPI(title="AI Study Tutor", version="0.9.0",
              description="In-development source-grounded tutor. Create a session first.")
store = SessionTutorStore()


def session_dependency(x_session_id: str | None = Header(default=None)) -> TutorSession:
    try:
        return store.get_existing(x_session_id)
    except KeyError as exc:
        raise HTTPException(401, "Create a session and send its X-Session-ID header.") from exc


@app.get("/")
@app.get("/health")
def root() -> dict:
    return {"name": "AI Study Tutor", "version": "0.9.0", "status": "in_development"}


@app.post("/sessions", status_code=201)
def create_session() -> dict:
    try:
        return {"session_id": store.create(), "idle_ttl_seconds": store.ttl_seconds}
    except SessionCapacityError as exc:
        raise HTTPException(503, str(exc)) from exc


@app.delete("/session", status_code=204)
def delete_session(x_session_id: str | None = Header(default=None),
                   session: TutorSession = Depends(session_dependency)) -> None:
    with session.lock:
        store.remove(x_session_id)


@app.post("/upload")
async def upload_document(file: UploadFile = File(...),
                          session: TutorSession = Depends(session_dependency)) -> dict:
    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Please upload a PDF file.")
        data = bytearray()
        while block := await file.read(min(65536, MAX_PDF_BYTES + 1 - len(data))):
            data.extend(block)
            if len(data) > MAX_PDF_BYTES:
                raise HTTPException(413, "PDF exceeds the 20 MB limit.")
        # Retain the basename only; filenames are never used as server paths.
        filename = file.filename.replace("\\", "/").split("/")[-1]

        def load() -> int:
            with session.lock:
                return session.tutor.load_document(filename, bytes(data))

        chunks = await run_in_threadpool(load)
        return {"message": "Document indexed successfully.", "filename": filename, "chunks": chunks}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "Unable to process this PDF.") from exc
    finally:
        await file.close()


def require_document(session: TutorSession) -> None:
    if session.tutor.document_name is None:
        raise HTTPException(400, "Upload a PDF into this session first.")


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest,
                 session: TutorSession = Depends(session_dependency)) -> AnswerResponse:
    with session.lock:
        require_document(session)
        answer, sources, mode = session.tutor.answer(**request.model_dump())
        return AnswerResponse(answer=answer, sources=sources, mode=mode,
                              level=request.level, language=request.language)


@app.post("/quiz", response_model=QuizResponse)
def create_quiz(request: QuizRequest,
                session: TutorSession = Depends(session_dependency)) -> QuizResponse:
    with session.lock:
        require_document(session)
        if not session.tutor.llm_available:
            raise HTTPException(503, "Quiz generation needs a configured Gemini provider.")
        try:
            questions = session.tutor.create_quiz(**request.model_dump())
        except RuntimeError as exc:
            raise HTTPException(422, "No valid source-grounded quiz could be generated.") from exc
        except Exception as exc:
            raise HTTPException(503, "Quiz provider unavailable. Please try again later.") from exc
        return QuizResponse(topic=request.topic, difficulty=request.difficulty, questions=questions)


@app.post("/quiz/answer", response_model=QuizGradeResponse)
def grade_quiz_answer(request: QuizAnswerRequest,
                      session: TutorSession = Depends(session_dependency)) -> QuizGradeResponse:
    with session.lock:
        if request.question_id not in session.tutor.quiz_bank:
            raise HTTPException(404, "Unknown question in this session.")
        if not session.tutor.llm_available:
            raise HTTPException(503, "Answer grading needs a configured Gemini provider.")
        try:
            return QuizGradeResponse(**session.tutor.grade_quiz_answer(**request.model_dump()))
        except Exception as exc:
            raise HTTPException(503, "Unable to grade this answer. Please try again later.") from exc


@app.get("/progress", response_model=ProgressResponse)
def learner_progress(session: TutorSession = Depends(session_dependency)) -> ProgressResponse:
    with session.lock:
        return ProgressResponse(**session.tutor.get_progress())


@app.post("/review", response_model=ReviewResponse)
def personalized_review(request: ReviewRequest,
                        session: TutorSession = Depends(session_dependency)) -> ReviewResponse:
    with session.lock:
        require_document(session)
        try:
            concept, answer, sources, mode, level = session.tutor.personalized_review(**request.model_dump())
        except RuntimeError as exc:
            raise HTTPException(400, "Choose a concept or complete a quiz before review.") from exc
        return ReviewResponse(concept=concept, answer=answer, sources=sources,
                              mode=mode, level=level, language=request.language)
