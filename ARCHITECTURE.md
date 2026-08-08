# Architecture

## Version 0.2 — Grounded Generative Tutor

```text
Student
  |
  v
FastAPI
  |
  +--> PDF Upload
  |      |
  |      v
  |   PyPDF text extraction
  |      |
  |      v
  |   Chunking
  |      |
  |      v
  |   TF-IDF index
  |
  +--> Question + learner level
         |
         v
      Query vector
         |
         v
      Cosine similarity
         |
         v
      Top source passages
         |
         v
      Grounded prompt
         |
         +----------------------+
         |                      |
   GEMINI_API_KEY set?          No
         |                      |
        Yes                     v
         |                Retrieval fallback
         v
   Gemini generation
         |
         v
   Answer constrained to source
   + PDF page citations
```

## Design Principles

1. **Retrieval before generation** — the model receives only passages selected from the uploaded document.
2. **Source grounding** — the prompt instructs the model not to use outside facts.
3. **Visible evidence** — generated answers cite PDF page numbers and the API also returns the retrieved source chunks.
4. **Graceful uncertainty** — if the source does not contain enough information, the tutor is instructed to say so rather than inventing an answer.
5. **Learner adaptation** — the same evidence can be explained at beginner, intermediate, or advanced level.
6. **Safe fallback** — if no LLM API key is configured or generation fails, the system still returns the retrieved passages rather than hiding the failure.

## Next: Version 0.3

Add intelligent learning support:

- quiz generation from uploaded sources
- answer checking with explanations
- concept mastery tracking
- adaptive difficulty
- review recommendations
- Arabic + English learning support
