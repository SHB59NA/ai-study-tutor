# Architecture

## Version 0.1

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
  +--> Question
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
      Grounded response + page references
```

## Design principle

The first version prioritizes transparency and source grounding. A generative LLM is intentionally not included yet, so the retrieval layer can be tested and evaluated independently before generation is added.

## Planned Version 0.2

The next version will add an LLM after retrieval. The model will receive only the most relevant source passages and will be instructed to explain the answer using those sources, cite pages, and say when the source does not contain enough information.

## Planned Version 0.3

Add learner modeling and adaptive tutoring:

- learner level
- concept mastery
- quiz history
- explanation difficulty
- targeted follow-up questions
- bilingual Arabic/English support
