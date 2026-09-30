# AI Study Tutor

**Status: In development — educational prototype, not a production service.**

An English/Arabic study assistant for **one text-based PDF per session**. It retrieves page-linked passages, optionally uses Gemini to explain them, and supports source-based quizzes and practice feedback.

**ابدئي بالعربي:** [دليل التشغيل والتجربة والنتائج الموثقة](docs/START_HERE_AR.md).

**Implemented retrieval is word + character TF-IDF, not neural embeddings, LangChain, or a vector database.** Cross-language retrieval uses optional Gemini query translation. Source passages remain in the document's original language.

## Try it without an API key

Python 3.11–3.13 is the intended environment; use a virtual environment. The linked GitHub Actions run below was verified on Python 3.11.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

For Windows commands that do not require activating a PowerShell script, see the [Arabic quick start](docs/START_HERE_AR.md).

Open **http://127.0.0.1:7860**, press **Use fictional sample**, select **Ask Tutor**, and ask:

> What does a primary key identify?

Leave **Enable Gemini** unchecked. The application displays retrieved passages and PDF pages; **it does not pretend to generate an answer**. Try a clearly unrelated question to see the no-evidence response. The included handbook is original fictional teaching material, not a real institution's policy.

### Optional Gemini

Copy `.env.example` to `.env`, set `GEMINI_API_KEY` locally, and restart. Existing environment variables take precedence. The model name is configurable with `GEMINI_MODEL`; the template uses `gemini-2.5-flash`, whose availability depends on the provider/account.

Checking **Enable Gemini** sends the question and retrieved excerpts to Google. Cross-language query translation, quiz generation, grading, and generated review also need the provider. Never paste keys into source code, GitHub, or screenshots. Provider failure leaves a clearly labeled retrieval fallback; it does not count as a successful generated answer.

## What is implemented

| Capability | Behavior / boundary |
|---|---|
| PDF ingestion | PDF signature/size validation; page-aware extraction; rejects encrypted and image-only PDFs |
| Retrieval | 900-character chunks with 150-character overlap; lexical relevance gate; character reranking; page diversity |
| Arabic support | Basic text normalization and stop words; Arabic responses; optional cross-language query translation |
| Grounding guards | Source-page allowlist, citation-presence check, and conservative numeric checks with one repair attempt |
| Quizzes | Optional Gemini questions/reference answers; reference answers are not returned in the public question payload |
| Practice progress | Recent-score average and concept-level feedback; not a validated assessment instrument |
| Session isolation | Separate Gradio sessions; API bearer sessions; bounded memory and lazy inactivity expiry |
| Privacy controls | Retrieval-only default; explicit session clearing; no public sharing tunnel by default |
| Evaluation | Offline regression tests, a reproducible synthetic retrieval benchmark, and optional live-answer evaluation tools |

A citation or matching number **does not prove semantic correctness**. Check generated answers against the source. Same-language retrieval works without a provider; cross-language understanding does not.

## Validation and reproducible evidence

[Verified CI run: 36764903878](https://github.com/SHB59NA/ai-study-tutor/actions/runs/36764903878) tested the runtime implementation at `8b2e963` against the then-current base on 30 September 2026:

- **115 software tests passed; 81% line coverage of `app`.** One dependency deprecation warning was reported.
- **Browser smoke passed:** sample PDF loaded, offline retrieval performed, source page displayed, and screenshots captured.
- The developer-authored retrieval fixture found the expected page in **10/10** in-scope cases and rejected **3/4** out-of-scope cases. The salary question remains a documented failure.

These are software/fixture checks, **not** live Gemini answer accuracy, educational effectiveness, or independently validated performance. No live provider key was used. See the run's `validation-results` artifact for reports and screenshots; artifact retention is temporary.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q --cov=app --cov-report=term-missing
python -m evaluation.offline_demo
python scripts/secret_scan.py
# Browser smoke test and screenshots:
python -m playwright install chromium
python scripts/capture_demo.py
```

The benchmark writes **all cases, including failures**, source/dataset hashes, runtime versions, and retrieval settings to `artifacts/synthetic_retrieval.json`. It uses 14 developer-authored questions over a four-page fictional PDF. This is a **smoke test, not an independent test set or a measure of answer accuracy**. See [evaluation methodology](docs/EVALUATION.md) and the [checked-in run](evaluation/results/synthetic_retrieval_v1.json).

GitHub Actions runs tests without a provider key and publishes test reports, environment versions, source snapshots, and browser screenshots as workflow artifacts. A passing CI run means the software checks passed; it does not mean every benchmark question succeeds.

The older Kuwait BUR benchmark files remain for reproducibility. Their source PDF is not bundled. Legacy result files are not a new validation of this version.

## API

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Visit **http://127.0.0.1:8000/docs**. First call `POST /sessions`, then supply the returned token as the `X-Session-ID` header. Keep that token private; it is a bearer capability, not a user-account login.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Non-sensitive application metadata |
| `POST /sessions` | Create a session |
| `POST /upload` | Load one PDF into that session |
| `POST /ask` | Ask; `use_llm` defaults to false; `language` is `english` or `arabic` |
| `POST /quiz` | Generate practice questions using Gemini |
| `POST /quiz/answer` | Submit an answer for provider-assisted practice feedback |
| `GET /progress` | Session-specific practice progress |
| `POST /review` | Review a selected/weak concept; provider use is opt-in |
| `DELETE /session` | Remove the session and invalidate its token |

**API change in 0.9:** stateful endpoints no longer share a global tutor. They require a session token. Run a single worker; in-memory sessions are not shared across processes.

## Project guide

- [ابدئي من هنا: تشغيل Windows وتجربة المشروع](docs/START_HERE_AR.md)
- [Architecture and engineering decisions](ARCHITECTURE.md)
- [Evaluation methodology and limitations](docs/EVALUATION.md)
- [Deployment and configuration](docs/DEPLOYMENT.md)
- [Security and data handling](docs/SECURITY.md)
- [شرح المشروع والتحضير للمقابلة بالعربي](docs/OWNER_GUIDE_AR.md)
- [Portfolio wording and contribution transparency](docs/PORTFOLIO.md)
- [Audit and changes](docs/AUDIT.md) · [Roadmap](ROADMAP.md)

## Ownership and development

Maintained by **Sherifah Hisham AlBalool**. Development includes AI-assisted implementation and documentation. Describe personal contributions accurately and distinguish implemented functionality from tests, mock-provider behavior, and future plans. No independent authorship or production deployment is implied.

No software license has been selected by the owner; do not assume reuse permissions. Third-party dependencies retain their respective licenses.
