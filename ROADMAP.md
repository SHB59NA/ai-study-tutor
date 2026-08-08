# Roadmap

## Phase 1 — Grounded Retrieval MVP

- [x] FastAPI backend
- [x] PDF upload
- [x] Text extraction
- [x] Chunking
- [x] TF-IDF retrieval
- [x] Page-aware source passages
- [x] Basic retrieval test

## Phase 2 — Generative Tutor

- [x] Add LLM provider wrapper
- [x] Generate explanations only from retrieved context
- [x] Require page citations in generated answers
- [x] Refuse unsupported questions gracefully
- [x] Add beginner / intermediate / advanced explanation modes
- [x] Keep transparent retrieval fallback when no API key is configured

## Phase 3 — Intelligent Learning Support

- [x] Quiz generation from source material
- [x] Answer checking with educational feedback
- [x] Track a transparent learner mastery score
- [x] Adapt recommended quiz difficulty from recent performance
- [x] Track concept-level performance
- [x] Detect weak concepts
- [x] Recommend specific concepts to review next
- [x] Generate a personalized source-grounded review for the weakest concept
- [ ] Persist learner progress across sessions

## Phase 4 — Human-Centered Educational AI

- [ ] Arabic + English support
- [ ] Student feedback controls
- [ ] Instructor content controls
- [ ] Learning analytics dashboard
- [ ] Evaluate answer faithfulness
- [ ] Evaluate usability and educational usefulness

## Research Questions

1. How can a study assistant remain grounded in instructor-provided learning material while still giving useful explanations?
2. How should explanations adapt to learner knowledge without removing productive struggle?
3. How can citations and uncertainty improve student trust in AI-generated educational guidance?
4. What interaction design best supports educators while keeping them in control of the learning process?
5. Can a simple, transparent mastery model improve the sequencing of AI-generated educational questions?
6. Can concept-level performance signals help an AI tutor recommend useful, targeted review without over-automating the learning process?
