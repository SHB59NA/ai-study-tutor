# AI Study Tutor

AI-powered study tutor for **personalized, grounded, and interactive learning**.

This project explores how artificial intelligence can support students without replacing educators. The tutor answers questions from uploaded learning materials, keeps responses grounded in source content, adapts explanations to learner level, generates and grades quizzes, tracks concept-level performance, and recommends targeted review.

## Research Direction

Artificial Intelligence for Education, Human-Centered AI, NLP, Retrieval-Augmented Generation (RAG), intelligent tutoring systems, adaptive learning, and personalized educational support.

## Version 0.4 — Personalized Review MVP

Current workflow:

1. Upload a PDF study document.
2. Extract and split it into page-aware chunks.
3. Build a TF-IDF retrieval index.
4. Ask grounded questions at beginner, intermediate, or advanced level.
5. Generate source-grounded quiz questions, each tagged with the concept being tested.
6. Grade learner answers against source-grounded reference answers.
7. Track overall mastery and recent concept-level performance.
8. Detect concepts with low mastery.
9. Recommend the next difficulty level.
10. Generate a personalized review for the weakest concept using the uploaded source.

The mastery model is intentionally simple and transparent for this research prototype. It is not a validated educational assessment model.

## Tech Stack

- Python
- FastAPI
- PyPDF
- scikit-learn
- TF-IDF / cosine similarity
- Google Gemini API (`google-genai`)
- Pydantic

## Main Endpoints

### `/upload`
Upload and index a PDF.

### `/ask`
Ask a source-grounded question with a selected learner level.

### `/quiz`
Generate a source-grounded quiz. Each question includes a concept label and source page.

### `/quiz/answer`
Grade a learner answer. The response includes:

- score
- educational feedback
- concept tested
- review recommendation
- source page
- overall mastery score
- next recommended difficulty
- current weak concepts

### `/progress`
Return the learner's current transparent progress model:

- overall mastery
- number of attempts
- next recommended difficulty
- weak concepts with concept-level mastery

### `/review`
Generate a source-grounded explanation for a selected concept. If no concept is supplied, the tutor automatically chooses the learner's weakest detected concept.

Example:

```json
{
  "concept": null,
  "level": null,
  "top_k": 3
}
```

## Colab

After pulling the latest repository:

```python
%cd /content/ai-study-tutor
!git pull
!pip install -q -r requirements.txt httpx
```

Store the Gemini key securely in Colab Secrets as `GEMINI_API_KEY`, then load it before importing the app:

```python
from google.colab import userdata
import os

os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
```

## Next Milestones

- persist learner history across sessions
- bilingual Arabic + English tutoring
- student feedback controls
- instructor content controls
- learning analytics dashboard
- systematic evaluation of faithfulness and educational usefulness

## Educational AI Goal

The long-term goal is to build a human-centered AI tutor that helps learners understand difficult concepts, adapts explanations and practice to individual needs, identifies where a learner needs more support, provides reliable source-grounded guidance, and gives educators useful tools while keeping them in control of the learning process.

## Status

**Version 0.4 — Personalized review MVP**

Active development.
