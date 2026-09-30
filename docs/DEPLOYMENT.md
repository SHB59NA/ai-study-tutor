# Run and deploy

## Local CPU demo

Install `requirements.txt` in a virtual environment and run `python app.py`. The default address is `127.0.0.1:7860`; no GPU or `spaces` package is required. `.env.example` documents optional settings. Restart after changing provider configuration.

The demo works without an API key for same-language retrieval and source display. Quizzes and generated answers require Gemini. Do not treat a successful offline run as a live-provider test.

## Local API

`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

Create a session using `POST /sessions`; pass the token in `X-Session-ID` on every stateful request. Sessions are in memory: **one worker**, with no multi-instance sharing. `DELETE /session` invalidates the token. Restarting invalidates all tokens.

## CPU container

```bash
docker build -t ai-study-tutor .
docker run --rm -p 127.0.0.1:7860:7860 ai-study-tutor
# Optional provider configuration from a local file:
# docker run --rm --env-file .env -e GRADIO_SERVER_NAME=0.0.0.0 \
#   -p 127.0.0.1:7860:7860 ai-study-tutor
```

The Dockerfile is provided for reproducible packaging. Unless accompanied by a successful build log, do not claim that a container deployment was tested.

## Hosted demo

A CPU host is sufficient. A Gradio/Hugging Face Space can use `app.py`; select compatible runtime dependencies and set `GRADIO_SERVER_NAME=0.0.0.0`. Store any API key in the hosting service's secret settings, not in GitHub. See the security checklist before opening access. No live hosting URL is claimed by this repository update.

## Troubleshooting

- **No extractable text:** the PDF is scanned/image-only. Obtain a text-based copy or run OCR separately.
- **No evidence:** ask using the source's language and vocabulary, or opt into query translation with Gemini.
- **Retrieval fallback:** Gemini is disabled/unconfigured, failed, or produced an answer rejected by guards. Inspect passages; don't report this as generation success.
- **Session expired / 401:** create a new API session and re-upload the PDF.
- **503 session capacity:** wait for inactive sessions to expire; don't remove the limits to open an unbounded public service.
