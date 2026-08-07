# AI Study Tutor

AI-powered study tutor for **personalized, grounded, and interactive learning**.

This project explores how artificial intelligence can support students without replacing educators. The tutor is designed to answer questions from uploaded learning materials, keep responses grounded in source content, and evolve toward adaptive explanations, quizzes, and learner-specific support.

## Why this project?

Large language models can be useful for learning, but educational systems need more than fluent answers. They should:

- stay grounded in trusted course material,
- explain concepts at an appropriate level,
- make the source of an answer visible,
- adapt to different learners,
- help educators rather than replace them.

**Research direction:** Artificial Intelligence for Education, Human-Centered AI, NLP, Retrieval-Augmented Generation (RAG), and intelligent tutoring systems.

## Current MVP

The first version provides a local, source-grounded learning workflow:

1. Upload a PDF study document.
2. Extract and split the document into learning chunks.
3. Build a TF-IDF retrieval index.
4. Ask a question about the uploaded material.
5. Retrieve the most relevant passages and return an extractive grounded answer with source references.

This version intentionally starts with transparent retrieval before adding a generative LLM layer.

## Planned Features

- LLM-powered explanations constrained to retrieved sources
- Page-level citations
- Beginner / intermediate / advanced explanation modes
- Automatic quiz generation
- Adaptive difficulty based on learner performance
- Learning progress model
- Instructor dashboard
- Arabic + English learning support
- Evaluation for faithfulness, usefulness, and learning outcomes

## Tech Stack

- Python
- FastAPI
- PyPDF
- scikit-learn
- TF-IDF / cosine similarity
- Pydantic

## Project Structure

```text
ai-study-tutor/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── retrieval.py
│   └── tutor.py
├── tests/
│   └── test_retrieval.py
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
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Educational AI Goal

The long-term goal is to build a human-centered AI tutor that can help learners understand difficult concepts, adapt explanations to individual needs, provide reliable source-grounded guidance, and give educators useful tools for creating stronger learning experiences.

## Status

**Version 0.1 — Grounded retrieval MVP**

Active development.