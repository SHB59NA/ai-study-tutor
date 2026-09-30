# Evaluation: what the results do and do not mean

## Layers

1. **Software regression tests:** validation, isolation, lifecycle, API requests, offline behavior, citation/numeric checks, and mocked quiz/grading flows. Mock provider tests validate our control flow, not Gemini's real answers.
2. **Synthetic retrieval smoke benchmark:** `python -m evaluation.offline_demo`. Four original fictional English PDF pages, ten in-scope questions, four out-of-scope questions, Top-K = 3. Questions were authored for this fixture; it is not held out.
3. **Optional generated-answer evaluation:** existing `evaluation.answer_grounding_eval` and replay tools. These need the relevant source PDF and (for a fresh run) an explicitly configured provider. Regex expected-fact/citation matching is a heuristic, not a human truth judgment.
4. **Browser smoke test:** starts the actual Gradio application, loads the sample, retrieves evidence, and captures the displayed UI without a provider key.

## Recorded synthetic run

See `evaluation/results/synthetic_retrieval_v1.json`. This run found an expected page for 10/10 in-scope cases and rejected 3/4 out-of-scope cases: 13/14 total. The remaining failure (`salary`) retrieves topical service-desk passages although no salary information exists. It is deliberately retained as a known limitation, not hidden or relabeled.

These numbers describe this small developer fixture only. They are **not 92.86% generated-answer accuracy**, a multilingual benchmark, independent validation, or an admissions probability. No live Gemini generation was performed in this run.

The report records source/dataset hashes, interpreter/package versions, configuration, scores, retrieved pages, and every case outcome. The checked-in report is a snapshot; reruns may differ if package versions or the implementation change. CI uploads its own reports and environment.

## Next evaluation protocol

Before a stronger claim, freeze a separate multi-document test set; include paraphrases, Arabic materials, cross-language questions, absent-answer questions with topical overlap, and source instructions that must not override the task. Evaluate retrieval separately from generation. Use blinded human checks for correctness and citation support. Report denominators, every failure, and provider outages separately. Do not tune on the final test set.

Legacy Kuwait BUR result files were inherited from the baseline and were not regenerated here; their original source PDF is not bundled. Do not mix their numbers with the new synthetic run.
