---
title: AI Study Tutor
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: gradio
python_version: "3.10"
app_file: app.py
pinned: false
short_description: Adaptive AI tutor for source-grounded learning.
tags:
  - education
  - ai
  - rag
  - adaptive-learning
  - gradio
---

# AI Study Tutor

AI-powered study tutor for **personalized, source-grounded, bilingual learning**.

This project explores how artificial intelligence can support students without replacing educators. The tutor answers questions from uploaded learning materials, keeps responses grounded in source content, adapts explanations to learner level, generates and grades quizzes, tracks concept-level performance, detects weak concepts, and recommends targeted review.

## Research Direction

Artificial Intelligence for Education, Human-Centered AI, NLP, Retrieval-Augmented Generation (RAG), intelligent tutoring systems, adaptive learning, bilingual learning support, and personalized educational support.

## Version 0.8 — Arabic + English

Version 0.8 adds bilingual English/Arabic tutoring on top of the session-isolated professional demo.

The interactive experience includes:

1. **Upload** — load an educational PDF and detect whether its dominant language is English or Arabic.
2. **Ask Tutor** — ask in English or Arabic and receive a source-grounded answer in the selected tutor language.
3. **Cross-language retrieval** — when the learner's query language differs from the PDF, translate only the retrieval query into the source language before TF-IDF search.
4. **Adaptive Quiz** — generate source-grounded questions, reference answers, concept labels, and grading feedback in English or Arabic.
5. **Progress** — view mastery, attempts, recommended difficulty, and weak concepts in a readable learning snapshot.
6. **Personalized Review** — review the weakest detected concept automatically or choose one manually.
7. **Session isolation** — each browser session has its own PDF, quiz bank, and learner progress.
8. **Visible evidence** — retrieved passages remain visible in the PDF's original language for verification.

## Bilingual Grounding Pipeline

```text
Educational PDF
      |
      v
Text extraction + page-aware chunking
      |
      v
Dominant source-language detection
      |
      v
Learner question in English or Arabic
      |
      +--> same language as PDF: search directly
      |
      +--> different language: translate retrieval query only
      |
      v
TF-IDF retrieval + cosine similarity
      |
      v
Original source passages + PDF pages
      |
      v
Grounded Gemini generation in selected tutor language
      |
      +--> explanations + page citations
      +--> adaptive quizzes
      +--> answer grading + feedback
      +--> personalized review
      |
      v
Transparent learner model
      +--> mastery score
      +--> adaptive difficulty
      +--> weak concept detection
```

The translation step is used only to improve retrieval. It is not treated as source evidence. Final answers are still constrained to retrieved passages from the uploaded PDF.

## Design Principles

- **Ground before generating** — retrieve evidence from the uploaded PDF before generation.
- **Visible evidence** — expose page references and original retrieved passages to the learner.
- **Cross-language access** — allow Arabic/English interaction without replacing the source with translated evidence.
- **Learner adaptation** — vary explanation depth and quiz difficulty.
- **Targeted support** — detect weak concepts and recommend focused review.
- **Session isolation** — keep each public demo user's study material and learner state separate in memory.
- **Human-centered use** — support educators and learners rather than positioning the system as a replacement for instruction.

## Tech Stack

- Python
- FastAPI
- Gradio
- PyPDF
- scikit-learn
- TF-IDF / cosine similarity
- Google Gemini API (`google-genai`)
- Pydantic

## Main API Endpoints

The FastAPI layer remains available for the core English/default workflow:

- `/upload` — upload and index a PDF.
- `/ask` — ask a source-grounded question with a selected learner level.
- `/quiz` — generate source-grounded quiz questions with concept labels and source pages.
- `/quiz/answer` — grade a learner answer and update learning progress.
- `/progress` — inspect the transparent learner model and weak concepts.
- `/review` — create source-grounded personalized review for a selected or automatically detected weak concept.

The Gradio portfolio interface contains the current bilingual English/Arabic experience.

## Run the Interactive Demo in Google Colab

Pull the latest code and install dependencies:

```python
%cd /content/ai-study-tutor
!git fetch origin
!git reset --hard origin/main
!pip install -q -r requirements.txt
!pytest -q
```

Store the Gemini API key securely in Colab Secrets as `GEMINI_API_KEY`, then load it before running the app locally if needed.

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
│   ├── session_store.py
│   └── tutor.py
├── tests/
│   ├── test_learner.py
│   ├── test_retrieval.py
│   └── test_session_store.py
├── app.py
├── demo.py
├── pytest.ini
├── ARCHITECTURE.md
├── ROADMAP.md
├── requirements.txt
└── README.md
```

## Current Limitations

- The mastery model is intentionally simple and transparent; it is **not a validated educational assessment instrument**.
- Session state is in server memory and resets when the browser session or Space runtime ends.
- Cross-language retrieval currently uses query translation plus lexical TF-IDF retrieval rather than multilingual embeddings.
- PDF text extraction depends on extractable text; scanned image-only PDFs are not yet OCR-enabled.
- Generated answers and grading should be checked against the displayed source evidence and, where appropriate, an instructor.

## Next Milestones

- systematic bilingual retrieval evaluation
- grounding / citation evaluation dataset
- multilingual embedding comparison against TF-IDF + query translation
- instructor content controls
- learning analytics dashboard
- optional persistent learner history with privacy safeguards

## Educational AI Goal

The long-term goal is to build a human-centered AI tutor that helps learners understand difficult concepts, adapts explanations and practice to individual needs, identifies where a learner needs more support, provides reliable source-grounded guidance, and gives educators useful tools while keeping them in control of the learning process.

## Status

**Version 0.8 — Bilingual Arabic + English portfolio demo**

Active development.
