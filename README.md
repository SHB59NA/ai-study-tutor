---
title: AI Study Tutor
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: gradio
python_version: "3.10"
app_file: app.py
pinned: false
short_description: AI-powered study tutor for personalized, source-grounded learning.
tags:
  - education
  - ai
  - rag
  - adaptive-learning
  - gradio
---

# AI Study Tutor

AI-powered study tutor for **personalized, grounded, and interactive learning**.

This project explores how artificial intelligence can support students without replacing educators. The tutor answers questions from uploaded learning materials, keeps responses grounded in source content, adapts explanations to learner level, generates and grades quizzes, tracks concept-level performance, detects weak concepts, and recommends targeted review.

## Research Direction

Artificial Intelligence for Education, Human-Centered AI, NLP, Retrieval-Augmented Generation (RAG), intelligent tutoring systems, adaptive learning, and personalized educational support.

## Version 0.5 — Interactive Student Demo

The project now includes an interactive Gradio interface in `demo.py`, so the complete learning workflow can be tested without manually calling API endpoints.

The demo includes five learning areas:

1. **Upload** — load and index an educational PDF.
2. **Ask Tutor** — ask grounded questions at beginner, intermediate, or advanced level and inspect retrieved evidence.
3. **Adaptive Quiz** — generate a source-grounded question, submit an answer, receive feedback, and update learner mastery.
4. **Progress** — inspect overall mastery, attempts, recommended difficulty, and weak concepts.
5. **Personalized Review** — automatically review the weakest detected concept or choose a concept manually.

## Learning Pipeline

```text
Educational PDF
      |
      v
Text extraction + page-aware chunking
      |
      v
TF-IDF retrieval + cosine similarity
      |
      v
Grounded Gemini generation
      |
      +--> Question answering + page citations
      |
      +--> Quiz generation + concept labels
      |
      +--> Answer grading + educational feedback
      |
      v
Transparent learner model
      |
      +--> mastery score
      +--> adaptive difficulty
      +--> weak concept detection
      +--> personalized review
```

The mastery model is intentionally simple and transparent for this research prototype. It is not a validated educational assessment model.

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

- `/upload` — upload and index a PDF.
- `/ask` — ask a source-grounded question with a selected learner level.
- `/quiz` — generate source-grounded quiz questions with concept labels and source pages.
- `/quiz/answer` — grade a learner answer and update learning progress.
- `/progress` — inspect the transparent learner model and weak concepts.
- `/review` — create source-grounded personalized review for a selected or automatically detected weak concept.

## Run the Interactive Demo in Google Colab

Pull the latest code and install dependencies:

```python
%cd /content/ai-study-tutor
!git pull
!pip install -q -r requirements.txt
```

Store the Gemini API key securely in Colab Secrets as `GEMINI_API_KEY`, then load it before running the app:

```python
from google.colab import userdata
import os

os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
```

Launch the interface:

```python
!python demo.py
```

Gradio will provide a temporary public demo link. Open that link to use the tutor through the graphical interface.

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
│   ├── test_learner.py
│   └── test_retrieval.py
├── app.py
├── demo.py
├── ARCHITECTURE.md
├── ROADMAP.md
├── requirements.txt
└── README.md
```

## Next Milestones

- bilingual Arabic + English tutoring
- persistent learner history across sessions
- student feedback controls
- instructor content controls
- learning analytics dashboard
- systematic evaluation of faithfulness and educational usefulness

## Educational AI Goal

The long-term goal is to build a human-centered AI tutor that helps learners understand difficult concepts, adapts explanations and practice to individual needs, identifies where a learner needs more support, provides reliable source-grounded guidance, and gives educators useful tools while keeping them in control of the learning process.

## Status

**Version 0.5 — Interactive student demo**

Active development.
