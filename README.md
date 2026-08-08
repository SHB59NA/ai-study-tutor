# AI Study Tutor

AI-powered study tutor for **personalized, grounded, and interactive learning**.

This project explores how artificial intelligence can support students without replacing educators. The tutor answers questions from uploaded learning materials, keeps responses grounded in source content, and adapts the explanation to the learner's level.

## Why this project?

Large language models can be useful for learning, but educational systems need more than fluent answers. They should:

- stay grounded in trusted course material,
- explain concepts at an appropriate level,
- make the source of an answer visible,
- admit when the material does not support an answer,
- help educators rather than replace them.

**Research direction:** Artificial Intelligence for Education, Human-Centered AI, NLP, Retrieval-Augmented Generation (RAG), and intelligent tutoring systems.

## Version 0.2 — Grounded Generative Tutor

Current workflow:

1. Upload a PDF study document.
2. Extract and split the document into page-aware learning chunks.
3. Build a TF-IDF retrieval index.
4. Ask a question and choose a learner level: `beginner`, `intermediate`, or `advanced`.
5. Retrieve the most relevant passages with cosine similarity.
6. If a Gemini API key is configured, generate an explanation using only the retrieved source context.
7. Return the answer together with page citations and the original retrieved passages.
8. If no LLM is available, fall back to transparent retrieval rather than inventing content.

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

To enable generated tutoring answers, set a Gemini API key:

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

## Example Question Request

```json
{
  "question": "How will climate change affect Kuwait's temperature and rainfall?",
  "top_k": 3,
  "level": "beginner",
  "use_llm": true
}
```

The response reports whether the answer came from the generative tutor (`gemini`) or the retrieval fallback (`retrieval`) and always returns the source passages used for grounding.

## Colab

After cloning the repository, install dependencies:

```python
!pip install -q -r requirements.txt httpx
```

Store the Gemini key securely in Colab Secrets as `GEMINI_API_KEY`, then load it into the environment before importing the app:

```python
from google.colab import userdata
import os

os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
```

Then create the test client and use `/upload` and `/ask` as usual.

## Next Milestone — Version 0.3

- source-grounded quiz generation
- answer checking with explanations
- concept mastery tracking
- adaptive quiz difficulty
- personalized review recommendations
- Arabic + English learning support

## Educational AI Goal

The long-term goal is to build a human-centered AI tutor that can help learners understand difficult concepts, adapt explanations to individual needs, provide reliable source-grounded guidance, and give educators useful tools for creating stronger learning experiences.

## Status

**Version 0.2 — Grounded generative tutor**

Active development.