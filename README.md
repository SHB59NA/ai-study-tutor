# AI Study Tutor

AI-powered study tutor for **personalized, grounded, and interactive learning**.

This project explores how artificial intelligence can support students without replacing educators. The tutor answers questions from uploaded learning materials, keeps responses grounded in source content, adapts explanations to the learner's level, and can now generate and grade source-grounded quizzes.

## Research Direction

Artificial Intelligence for Education, Human-Centered AI, NLP, Retrieval-Augmented Generation (RAG), intelligent tutoring systems, and adaptive learning.

## Version 0.3 — Adaptive Learning MVP

Current workflow:

1. Upload a PDF study document.
2. Extract and split it into page-aware chunks.
3. Build a TF-IDF retrieval index.
4. Ask grounded questions at beginner, intermediate, or advanced level.
5. Generate quiz questions from retrieved source passages.
6. Grade learner answers against source-grounded reference answers.
7. Track a simple mastery score from recent quiz performance.
8. Recommend the next quiz difficulty: beginner, intermediate, or advanced.

The mastery model is intentionally simple and transparent for this research prototype. It is not intended to represent a validated educational assessment model.

## Tech Stack

- Python
- FastAPI
- PyPDF
- scikit-learn
- TF-IDF / cosine similarity
- Google Gemini API (`google-genai`)
- Pydantic

## Project Structure

```text
ai-study-tutor/
├── app/
│   ├── __init__.py
│   ├── learner.py
│   ├── llm.py
│   ├── main.py
│   ├── models.py
│   ├── retrieval.py
│   └── tutor.py
├── tests/
│   └── test_retrieval.py
├── .env.example
├── ARCHITECTURE.md
├── ROADMAP.md
├── requirements.txt
└── README.md
```

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Set the Gemini API key:

```bash
export GEMINI_API_KEY="your-key"  # Windows PowerShell: $env:GEMINI_API_KEY="your-key"
```

Then run:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Main Endpoints

### `/upload`
Upload and index a PDF.

### `/ask`
Ask a question grounded in the uploaded material.

Example:

```json
{
  "question": "How will climate change affect Kuwait's temperature and rainfall?",
  "top_k": 3,
  "level": "beginner",
  "use_llm": true
}
```

### `/quiz`
Generate a source-grounded quiz.

```json
{
  "topic": "climate change in Kuwait",
  "difficulty": "intermediate",
  "count": 3,
  "top_k": 5
}
```

The public quiz response contains question IDs, questions, and source pages, but does not reveal the reference answers.

### `/quiz/answer`
Submit an answer using the question ID returned by `/quiz`.

```json
{
  "question_id": "example-id",
  "student_answer": "My answer here"
}
```

The response returns a score, educational feedback, source page, current mastery score, and recommended next difficulty.

## Colab

After cloning or pulling the latest repository:

```python
!pip install -q -r requirements.txt httpx
```

Store the Gemini key securely in Colab Secrets as `GEMINI_API_KEY`, then load it before importing the app:

```python
from google.colab import userdata
import os

os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
```

## Next Milestone

- recommend specific weak concepts for review
- persist learner history
- bilingual Arabic + English tutoring
- student feedback controls
- instructor content controls
- learning analytics
- systematic evaluation of faithfulness and educational usefulness

## Educational AI Goal

The long-term goal is to build a human-centered AI tutor that helps learners understand difficult concepts, adapts explanations and practice to individual needs, provides reliable source-grounded guidance, and gives educators useful tools while keeping them in control of the learning process.

## Status

**Version 0.3 — Adaptive learning MVP**

Active development.