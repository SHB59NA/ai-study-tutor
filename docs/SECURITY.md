# Security and privacy boundaries

This is a local/controlled-demo prototype, not a reviewed public multi-user service.

- **Secrets:** `.env` is ignored; `.env.example` contains no key. Environment variables take precedence. Do not commit keys or put them in query strings. The secret scan is a limited pattern scan of working-tree files, not proof that Git history is clean.
- **Provider disclosure:** retrieval-only requests do not use the model, including translation. Enabling Gemini sends questions and retrieved excerpts externally. Quizzes, grading, and generated review also send content. Use authorized, non-sensitive materials only.
- **Sessions:** state is separate by browser session or random API bearer token. A token grants access to that session: keep it private and use HTTPS when deployed. This is not account authentication. State is process-local, expires lazily, and is lost on restart. Use one worker.
- **Uploads:** basic file signature/size checks, page/text/chunk limits, and atomic indexing. The API bounds reads into memory; the multipart parser/server may buffer uploads before route handling. Configure a reverse-proxy request-body limit. pypdf is not a hostile-file sandbox.
- **Browser cache:** Gradio may create temporary upload files; its cache cleanup is configured hourly. Manual session clearing removes application state, not a promise of immediate erasure of every hosting log/cache. Avoid personal documents.
- **Errors:** raw provider exception strings are not exposed in the interface or stored by `StudyTutor.answer`; only exception class/status is retained. Legacy evaluation tools can capture raw exceptions and should be used only with non-sensitive fixtures.
- **Public serving:** the launcher does not automatically create a public tunnel. Before internet hosting add real authentication, per-user rate limits, provider spending caps, HTTPS, dependency scanning, parser isolation, and a privacy/retention policy.

Citation and numeric guards reduce some errors; they cannot make model output trustworthy by themselves. Prompts and source text remain untrusted input.
