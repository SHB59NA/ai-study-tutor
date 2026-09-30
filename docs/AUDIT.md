# Repository audit — 30 September 2026

Baseline main commit: `546c95312a09653dea0ab906fbf7f6b4c26898a4`.

## Findings addressed

- Main README described embeddings/semantic retrieval despite the implementation using TF-IDF. Documentation now describes the actual method.
- `app.py` imported an undeclared `spaces` dependency solely for a no-op GPU probe. Replaced with CPU startup.
- API endpoints shared one global tutor. Added independent server-generated bearer sessions and deletion.
- API language fields were missing although tutor methods supported Arabic. Added typed language forwarding and request validation.
- An offline request could still translate a cross-language query. Disabled all provider calls when `use_llm=False`.
- Substantive generated answers without citations passed the citation-page check. Added required citations, one repair, and fail-closed behavior.
- Numbers supplied only by a question could be treated as evidence. Numeric screening now uses source evidence only and normalizes Arabic digits.
- Nonfinite grading values could be accepted; invalid scores now fail explicitly.
- Failed indexing could mutate a prior index; replacement is now atomic with page/text/chunk limits.
- Session and quiz state were unbounded; added capacity/lifetime and history limits.
- Practice attempt count incorrectly stopped at the ten-score moving window; separated total attempts.
- Review queries included generic instruction text that could defeat the lexical gate; retrieval now searches the selected concept.
- The UI opened a public tunnel by default and exposed raw provider errors; removed implicit sharing and sanitized those failures.
- `.env` was documented but not loaded; added optional, non-overriding dotenv loading.
- No automated pipeline or self-contained example supported repository review; added CI, fixtures, regression tests, a benchmark, and browser capture.

## Verification boundaries

The original 53 tests passed in the initial GitHub Actions baseline. Additional checks are recorded by the final CI run and local test artifacts. The synthetic benchmark is developer-authored and retains its failures. No live model key was used in this update. Live model quality, high-load behavior, hostile-PDF resistance, container hosting, and educational outcomes have not been independently validated.

The default branch remains unchanged until the review branch is merged. Existing code and legacy benchmark fixtures are retained.
