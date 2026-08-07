from fastapi import FastAPI, File, HTTPException, UploadFile

from app.models import AnswerResponse, QuestionRequest
from app.tutor import StudyTutor

app = FastAPI(
    title="AI Study Tutor",
    description="A source-grounded study assistant for educational materials.",
    version="0.1.0",
)

tutor = StudyTutor()


@app.get("/")
def root() -> dict:
    return {
        "name": "AI Study Tutor",
        "version": "0.1.0",
        "status": "ready",
        "document_loaded": tutor.document_name,
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
        answer, sources = tutor.answer(request.question, top_k=request.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AnswerResponse(answer=answer, sources=sources)
