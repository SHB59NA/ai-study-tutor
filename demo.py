from pathlib import Path

import gradio as gr

from app.session_store import SessionTutorStore, TutorSession


session_store = SessionTutorStore()


APP_CSS = """
.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
}

.hero {
    padding: 30px 32px;
    border: 1px solid var(--border-color-primary);
    border-radius: 22px;
    margin-bottom: 18px;
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.10), rgba(14, 165, 233, 0.08));
}

.hero h1 {
    margin: 0 0 10px 0;
    font-size: 2.35rem;
    line-height: 1.05;
}

.hero p {
    margin: 0;
    max-width: 800px;
    font-size: 1.05rem;
    opacity: 0.86;
}

.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
}

.hero-badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    border: 1px solid var(--border-color-primary);
    font-size: 0.82rem;
    font-weight: 600;
    background: var(--background-fill-primary);
}

.answer-card {
    border-left: 4px solid var(--color-accent);
    padding-left: 14px;
}

.thinking-box {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    border: 1px solid var(--border-color-primary);
    border-radius: 14px;
    background: var(--background-fill-secondary);
    font-weight: 600;
}

.thinking-dot {
    display: inline-block;
    font-size: 1.2rem;
    animation: thinking-pulse 0.9s ease-in-out infinite;
}

@keyframes thinking-pulse {
    0%, 100% { opacity: 0.35; transform: scale(0.85); }
    50% { opacity: 1; transform: scale(1.15); }
}

.footer-note {
    text-align: center;
    opacity: 0.72;
    font-size: 0.84rem;
    padding: 18px 0 6px 0;
}
"""


HERO_HTML = """
<div class="hero">
  <h1>AI Study Tutor</h1>
  <p>
    A bilingual, source-grounded adaptive learning assistant that turns educational PDFs into
    explanations, quizzes, progress insights, and personalized review.
  </p>
  <div class="hero-badges">
    <span class="hero-badge">English + العربية</span>
    <span class="hero-badge">Cross-language retrieval</span>
    <span class="hero-badge">Source-grounded RAG</span>
    <span class="hero-badge">Adaptive quizzes</span>
    <span class="hero-badge">Weak-concept detection</span>
    <span class="hero-badge">Private session state</span>
  </div>
</div>
"""


def _session(request: gr.Request) -> TutorSession:
    return session_store.get(request.session_hash if request else None)


def _language(choice: str) -> str:
    return "arabic" if choice == "العربية" else "english"


def _difficulty_label(value: str, language: str) -> str:
    if language != "arabic":
        return value
    return {
        "beginner": "مبتدئ",
        "intermediate": "متوسط",
        "advanced": "متقدم",
    }.get(value, value)


def _thinking(language: str, task: str = "answer") -> str:
    messages = {
        "answer": {
            "english": "Thinking… Searching the uploaded source and preparing a grounded answer.",
            "arabic": "جاري التفكير… أبحث في المصدر المرفوع وأجهز إجابة موثقة.",
        },
        "quiz": {
            "english": "Generating… Finding relevant evidence and creating a grounded quiz question.",
            "arabic": "جاري إنشاء السؤال… أبحث عن الدليل المناسب وأجهز سؤالا من المصدر.",
        },
        "grade": {
            "english": "Checking your answer… Comparing it with the source-grounded reference.",
            "arabic": "جاري تصحيح إجابتك… أقارنها بالإجابة الموثقة من المصدر.",
        },
        "review": {
            "english": "Preparing your review… Finding the most relevant source evidence.",
            "arabic": "جاري تجهيز المراجعة… أبحث عن أكثر الأدلة ارتباطا بالمفهوم.",
        },
        "upload": {
            "english": "Reading the PDF… Extracting text and building the searchable index.",
            "arabic": "جاري قراءة ملف PDF… أستخرج النص وأبني فهرس البحث.",
        },
    }
    message = messages.get(task, messages["answer"]).get(language, messages["answer"]["english"])
    return (
        "<div class='thinking-box'>"
        "<span class='thinking-dot'>●</span>"
        f"<span>{message}</span>"
        "</div>"
    )


def cleanup_session(request: gr.Request) -> None:
    session_store.remove(request.session_hash if request else None)


def format_progress(tutor, language: str = "english") -> str:
    progress = tutor.get_progress()
    mastery = float(progress["mastery_score"])
    attempts = int(progress["attempts"])
    next_difficulty = progress["next_difficulty"]
    weak_concepts = progress["weak_concepts"]

    if language == "arabic":
        if weak_concepts:
            rows = [
                f"| {item['concept']} | {item['attempts']} | {float(item['mastery']):.0%} |"
                for item in weak_concepts
            ]
            weak_section = (
                "### مفاهيم تحتاج مراجعة\n\n"
                "| المفهوم | المحاولات | الإتقان |\n"
                "|---|---:|---:|\n" + "\n".join(rows)
            )
        else:
            weak_section = (
                "### مفاهيم تحتاج مراجعة\n\n"
                "لم يتم اكتشاف مفهوم ضعيف حتى الآن. أجب عن عدة أسئلة لبناء ملف تعلم."
            )
        return (
            "## ملخص التعلم\n\n"
            f"**الإتقان العام:** {mastery:.0%}  \n"
            f"**عدد محاولات الاختبار:** {attempts}  \n"
            f"**المستوى المقترح التالي:** `{_difficulty_label(next_difficulty, language)}`\n\n"
            f"{weak_section}"
        )

    if weak_concepts:
        rows = [
            f"| {item['concept']} | {item['attempts']} | {float(item['mastery']):.0%} |"
            for item in weak_concepts
        ]
        weak_section = (
            "### Concepts to review\n\n"
            "| Concept | Attempts | Mastery |\n"
            "|---|---:|---:|\n" + "\n".join(rows)
        )
    else:
        weak_section = (
            "### Concepts to review\n\n"
            "No weak concept has been detected yet. Complete a few quiz questions to build a learning profile."
        )

    return (
        "## Learning snapshot\n\n"
        f"**Overall mastery:** {mastery:.0%}  \n"
        f"**Quiz attempts:** {attempts}  \n"
        f"**Recommended next difficulty:** `{next_difficulty}`\n\n"
        f"{weak_section}"
    )


def upload_pdf(file_path, language_choice, request: gr.Request):
    language = _language(language_choice)
    if not file_path:
        yield (
            "### لم يتم اختيار ملف\nاختر ملف PDF أولاً."
            if language == "arabic"
            else "### No document selected\nChoose a PDF file first."
        )
        return

    path = Path(str(file_path))
    if path.suffix.lower() != ".pdf":
        yield (
            "### ملف غير مدعوم\nيرجى رفع ملف PDF."
            if language == "arabic"
            else "### Unsupported file\nPlease upload a PDF document."
        )
        return

    yield _thinking(language, "upload")

    session = _session(request)
    try:
        with session.lock:
            chunks = session.tutor.load_document(path.name, path.read_bytes())
            document_language = session.tutor.document_language
    except Exception as exc:
        yield (
            f"### تعذر رفع الملف\n`{exc}`"
            if language == "arabic"
            else f"### Upload failed\n`{exc}`"
        )
        return

    detected = (
        "العربية"
        if document_language == "arabic"
        else "English"
        if document_language == "english"
        else "Unknown"
    )
    if language == "arabic":
        yield (
            "### المستند جاهز\n\n"
            f"**الملف:** {path.name}  \n"
            f"**لغة المصدر المكتشفة:** {detected}  \n"
            f"**عدد مقاطع المصدر المفهرسة:** {chunks}  \n\n"
            "يمكنك الآن السؤال بالعربية أو الإنجليزية. سيبقى المستند وتقدم التعلم خاصين بجلسة المتصفح الحالية."
        )
        return

    yield (
        "### Document ready\n\n"
        f"**File:** {path.name}  \n"
        f"**Detected source language:** {detected}  \n"
        f"**Indexed source chunks:** {chunks}  \n\n"
        "You can now ask in English or Arabic. The document and learner progress belong only to your current browser session."
    )


def ask_tutor(question, level, language_choice, request: gr.Request):
    language = _language(language_choice)
    session = _session(request)

    with session.lock:
        tutor = session.tutor
        if tutor.document_name is None:
            yield (
                "### ارفع ملف PDF أولاً\nيحتاج المدرس الذكي إلى مصدر قبل أن يجيب."
                if language == "arabic"
                else "### Upload a PDF first\nThe tutor needs a source document before it can answer."
            ), ""
            return
        if not question or len(question.strip()) < 3:
            yield (
                "### اكتب سؤالاً\nاكتب سؤالاً محدداً عن المادة المرفوعة."
                if language == "arabic"
                else "### Enter a question\nAsk something specific about the uploaded material."
            ), ""
            return

    yield _thinking(language, "answer"), ""

    try:
        with session.lock:
            answer, sources, mode = session.tutor.answer(
                question.strip(),
                top_k=3,
                level=level,
                use_llm=True,
                language=language,
            )
    except Exception as exc:
        yield (
            f"### تعذر إنشاء الإجابة\n`{exc}`"
            if language == "arabic"
            else f"### Unable to answer\n`{exc}`"
        ), ""
        return

    evidence = []
    for source in sources:
        heading = (
            f"### صفحة PDF {source['page']}"
            if language == "arabic"
            else f"### PDF page {source['page']}"
        )
        score_label = "درجة الاسترجاع" if language == "arabic" else "Retrieval score"
        evidence.append(
            f"{heading}\n**{score_label}:** {source['score']}\n\n> {source['text']}"
        )

    source_text = "\n\n---\n\n".join(evidence)
    if language == "arabic":
        mode_label = "Gemini موثّق بالمصدر" if mode == "gemini" else "استرجاع من المصدر"
        response = (
            "## إجابة المدرس الذكي\n\n"
            f"**مستوى الشرح:** `{_difficulty_label(level, language)}`  \n"
            f"**النمط:** {mode_label}\n\n"
            f"{answer}"
        )
    else:
        mode_label = "Grounded Gemini" if mode == "gemini" else "Retrieval fallback"
        response = (
            "## Tutor response\n\n"
            f"**Explanation level:** `{level}`  \n"
            f"**Mode:** {mode_label}\n\n"
            f"{answer}"
        )
    yield response, source_text


def generate_quiz_question(topic, difficulty, language_choice, request: gr.Request):
    language = _language(language_choice)
    session = _session(request)

    with session.lock:
        tutor = session.tutor
        if tutor.document_name is None:
            message = (
                "### ارفع ملف PDF أولاً\nيجب إنشاء الاختبار من مادة مصدرية."
                if language == "arabic"
                else "### Upload a PDF first\nA quiz must be generated from source material."
            )
            yield None, message, ""
            return
        if not topic or len(topic.strip()) < 3:
            message = (
                "### اكتب موضوع الاختبار\nمثال: تأثيرات تغير المناخ في الكويت"
                if language == "arabic"
                else "### Enter a quiz topic\nExample: *Climate Change Impacts in Kuwait*"
            )
            yield None, message, ""
            return

    yield None, _thinking(language, "quiz"), ""

    try:
        with session.lock:
            questions = session.tutor.create_quiz(
                topic=topic.strip(),
                difficulty=difficulty,
                count=1,
                top_k=5,
                language=language,
            )
    except Exception as exc:
        message = (
            f"### تعذر إنشاء الاختبار\n`{exc}`"
            if language == "arabic"
            else f"### Unable to generate a quiz\n`{exc}`"
        )
        yield None, message, ""
        return

    q = questions[0]
    if language == "arabic":
        meta = (
            f"**المفهوم:** {q['concept']}  \n"
            f"**الصعوبة:** `{_difficulty_label(difficulty, language)}`  \n"
            f"**المصدر:** صفحة PDF {q['page']}"
        )
    else:
        meta = (
            f"**Concept:** {q['concept']}  \n"
            f"**Difficulty:** `{difficulty}`  \n"
            f"**Grounding source:** PDF page {q['page']}"
        )
    yield q["id"], f"## {q['question']}", meta


def grade_answer(question_id, student_answer, language_choice, request: gr.Request):
    language = _language(language_choice)
    session = _session(request)

    with session.lock:
        tutor = session.tutor
        if not question_id:
            message = (
                "### أنشئ سؤال اختبار أولاً."
                if language == "arabic"
                else "### Generate a quiz question first."
            )
            yield message, format_progress(tutor, language)
            return
        if not student_answer or not student_answer.strip():
            message = (
                "### اكتب إجابتك قبل التصحيح."
                if language == "arabic"
                else "### Write your answer before submitting."
            )
            yield message, format_progress(tutor, language)
            return
        current_progress = format_progress(tutor, language)

    yield _thinking(language, "grade"), current_progress

    try:
        with session.lock:
            result = session.tutor.grade_quiz_answer(
                question_id=question_id,
                student_answer=student_answer.strip(),
            )
            result_language = result.get("language", language)
            progress_text = format_progress(session.tutor, result_language)
    except Exception as exc:
        yield (
            f"### تعذر تصحيح الإجابة\n`{exc}`"
            if language == "arabic"
            else f"### Unable to grade the answer\n`{exc}`"
        ), current_progress
        return

    if result_language == "arabic":
        verdict = "إجابة قوية / صحيحة" if result["correct"] else "تحتاج إلى مراجعة"
        feedback = (
            f"## {verdict}\n\n"
            f"**الدرجة:** {result['score']:.0%}  \n"
            f"**المفهوم:** {result['concept']}  \n"
            f"**صفحة المصدر:** {result['source_page']}\n\n"
            f"### ملاحظات المدرس\n{result['feedback']}\n\n"
            f"### الخطوة المقترحة التالية\n{result['review_recommendation']}"
        )
    else:
        verdict = "Correct / strong answer" if result["correct"] else "Needs review"
        feedback = (
            f"## {verdict}\n\n"
            f"**Score:** {result['score']:.0%}  \n"
            f"**Concept:** {result['concept']}  \n"
            f"**Source page:** {result['source_page']}\n\n"
            f"### Tutor feedback\n{result['feedback']}\n\n"
            f"### Recommended next step\n{result['review_recommendation']}"
        )
    yield feedback, progress_text


def show_progress(language_choice, request: gr.Request):
    language = _language(language_choice)
    session = _session(request)
    with session.lock:
        return format_progress(session.tutor, language)


def personalized_review(concept, level, language_choice, request: gr.Request):
    language = _language(language_choice)
    session = _session(request)

    with session.lock:
        tutor = session.tutor
        if tutor.document_name is None:
            message = (
                "### ارفع ملف PDF أولاً\nيجب أن تكون المراجعة مرتبطة بمصدر."
                if language == "arabic"
                else "### Upload a PDF first\nPersonalized review must be grounded in a source document."
            )
            yield message, ""
            return

        selected_concept = concept.strip() if concept and concept.strip() else None
        selected_level = None if level == "auto" else level

    yield _thinking(language, "review"), ""

    try:
        with session.lock:
            concept_name, answer, sources, mode, final_level = session.tutor.personalized_review(
                concept=selected_concept,
                level=selected_level,
                top_k=3,
                language=language,
            )
    except Exception as exc:
        message = (
            f"### تعذر إنشاء المراجعة\n`{exc}`"
            if language == "arabic"
            else f"### Unable to create a review\n`{exc}`"
        )
        yield message, ""
        return

    evidence = []
    for source in sources:
        heading = (
            f"### صفحة PDF {source['page']}"
            if language == "arabic"
            else f"### PDF page {source['page']}"
        )
        evidence.append(f"{heading}\n\n> {source['text']}")

    if language == "arabic":
        mode_label = "Gemini موثّق بالمصدر" if mode == "gemini" else "استرجاع من المصدر"
        header = (
            f"## مراجعة: {concept_name}\n\n"
            f"**المستوى:** `{_difficulty_label(final_level, language)}`  \n"
            f"**النمط:** {mode_label}\n\n"
            f"{answer}"
        )
    else:
        mode_label = "Grounded Gemini" if mode == "gemini" else "Retrieval fallback"
        header = (
            f"## Review: {concept_name}\n\n"
            f"**Level:** `{final_level}`  \n"
            f"**Mode:** {mode_label}\n\n"
            f"{answer}"
        )
    yield header, "\n\n---\n\n".join(evidence)


with gr.Blocks(
    title="AI Study Tutor | Bilingual Source-Grounded Learning",
    theme=gr.themes.Soft(),
    css=APP_CSS,
    delete_cache=(3600, 3600),
) as demo:
    gr.HTML(HERO_HTML)

    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown(
                "**Recommended workflow:** Upload a PDF → choose English or العربية → Ask questions → "
                "Practice with a quiz → Check progress → Review weak concepts."
            )
        with gr.Column(scale=2):
            language_choice = gr.Radio(
                ["English", "العربية"],
                value="English",
                label="Tutor language / لغة المدرس",
            )

    with gr.Tab("1 · Upload"):
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("## Start with trusted study material")
                gr.Markdown(
                    "Upload one educational PDF. The tutor detects its main language and uses it as the evidence base. "
                    "You may then ask in English or Arabic, even when the PDF is in the other language."
                )
                pdf_file = gr.File(
                    label="Study material (PDF)",
                    file_types=[".pdf"],
                    type="filepath",
                )
                upload_button = gr.Button("Load study material", variant="primary")
                upload_status = gr.Markdown()
                upload_button.click(
                    upload_pdf,
                    inputs=[pdf_file, language_choice],
                    outputs=upload_status,
                    show_progress="full",
                )

            with gr.Column(scale=2):
                gr.Markdown(
                    "## What happens next?\n\n"
                    "1. Text is extracted page by page.\n"
                    "2. The PDF's dominant language is detected.\n"
                    "3. Cross-language questions are translated only for retrieval.\n"
                    "4. Relevant passages are retrieved with TF-IDF.\n"
                    "5. Gemini answers only from retrieved evidence in your selected language.\n\n"
                    "**Session privacy:** each browser session gets its own isolated PDF, quiz bank, and learner progress."
                )

    with gr.Tab("2 · Ask Tutor"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Ask a grounded question / اسأل من المصدر")
                question = gr.Textbox(
                    label="Question / السؤال",
                    placeholder="How will climate change affect Kuwait?  |  شلون راح يأثر تغير المناخ على الكويت؟",
                    lines=4,
                )
                level = gr.Radio(
                    ["beginner", "intermediate", "advanced"],
                    value="intermediate",
                    label="Explanation level / مستوى الشرح",
                )
                ask_button = gr.Button("Ask tutor / اسأل", variant="primary")

            with gr.Column(scale=3):
                answer_output = gr.Markdown(elem_classes=["answer-card"])
                with gr.Accordion("View source evidence / عرض المصدر", open=False):
                    source_output = gr.Markdown()

        ask_button.click(
            ask_tutor,
            inputs=[question, level, language_choice],
            outputs=[answer_output, source_output],
            show_progress="full",
        )

    with gr.Tab("3 · Adaptive Quiz"):
        quiz_id = gr.State()

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Practice from the same source / اختبر نفسك")
                topic = gr.Textbox(
                    label="Quiz topic / موضوع الاختبار",
                    placeholder="Climate Change Impacts in Kuwait | تأثيرات تغير المناخ في الكويت",
                )
                difficulty = gr.Radio(
                    ["beginner", "intermediate", "advanced"],
                    value="beginner",
                    label="Question difficulty / صعوبة السؤال",
                )
                generate_button = gr.Button("Generate question / أنشئ سؤال", variant="primary")
                quiz_meta = gr.Markdown()

            with gr.Column(scale=3):
                quiz_question = gr.Markdown()
                student_answer = gr.Textbox(
                    label="Your answer / إجابتك",
                    placeholder="Write your answer in your own words... / اكتب إجابتك بأسلوبك",
                    lines=5,
                )
                grade_button = gr.Button("Submit answer / صحح الإجابة")

        gr.Markdown("---")
        with gr.Row():
            with gr.Column(scale=3):
                grade_output = gr.Markdown(elem_classes=["answer-card"])
            with gr.Column(scale=2):
                progress_after_grade = gr.Markdown()

        generate_button.click(
            generate_quiz_question,
            inputs=[topic, difficulty, language_choice],
            outputs=[quiz_id, quiz_question, quiz_meta],
            show_progress="full",
        )
        grade_button.click(
            grade_answer,
            inputs=[quiz_id, student_answer, language_choice],
            outputs=[grade_output, progress_after_grade],
            show_progress="full",
        )

    with gr.Tab("4 · Progress"):
        gr.Markdown(
            "## Learning progress / تقدم التعلم\n"
            "The learner model uses recent quiz performance to estimate mastery, recommend difficulty, "
            "and identify concepts for review."
        )
        progress_button = gr.Button("Refresh progress / تحديث التقدم", variant="primary")
        progress_output = gr.Markdown()
        progress_button.click(
            show_progress,
            inputs=language_choice,
            outputs=progress_output,
        )

    with gr.Tab("5 · Personalized Review"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Personalized review / مراجعة مخصصة")
                gr.Markdown(
                    "Leave the concept blank to review the weakest detected concept automatically, "
                    "or enter a concept manually."
                )
                review_concept = gr.Textbox(
                    label="Concept (optional) / المفهوم (اختياري)",
                    placeholder="Leave blank for automatic review / اتركه فارغاً للمراجعة التلقائية",
                )
                review_level = gr.Dropdown(
                    ["auto", "beginner", "intermediate", "advanced"],
                    value="auto",
                    label="Review level / مستوى المراجعة",
                )
                review_button = gr.Button("Create review / أنشئ مراجعة", variant="primary")

            with gr.Column(scale=3):
                review_output = gr.Markdown(elem_classes=["answer-card"])
                with gr.Accordion("View review source / عرض مصدر المراجعة", open=False):
                    review_sources = gr.Markdown()

        review_button.click(
            personalized_review,
            inputs=[review_concept, review_level, language_choice],
            outputs=[review_output, review_sources],
            show_progress="full",
        )

    with gr.Tab("About"):
        gr.Markdown(
            "## Research motivation\n\n"
            "AI Study Tutor explores human-centered, source-grounded AI for education. Version 0.8 adds "
            "bilingual English/Arabic tutoring and cross-language retrieval while preserving visible source evidence.\n\n"
            "### Bilingual retrieval design\n\n"
            "- The uploaded PDF's dominant script is detected as English or Arabic.\n"
            "- If the learner asks in the other language, Gemini translates **only the retrieval query** into the source language.\n"
            "- TF-IDF retrieves passages from the original PDF.\n"
            "- The final explanation, quiz, grading feedback, or review is generated in the learner's selected language using only retrieved evidence.\n"
            "- Retrieved source passages remain visible in their original language for verification.\n\n"
            "### Design principles\n\n"
            "- **Ground before generating:** retrieve evidence from the uploaded PDF first.\n"
            "- **Make evidence visible:** expose source pages and retrieved passages.\n"
            "- **Adapt to the learner:** vary explanation and practice difficulty.\n"
            "- **Isolate learner state:** each browser session has an independent tutor instance.\n"
            "- **Support productive learning:** use feedback and targeted review instead of only giving answers.\n"
            "- **Keep the model transparent:** the mastery score is intentionally simple and inspectable.\n\n"
            "### Prototype limitation\n\n"
            "The mastery model is a research prototype, not a validated educational assessment instrument. "
            "Cross-language retrieval currently uses query translation plus lexical TF-IDF retrieval rather than multilingual embeddings. "
            "Generated answers and grading should be checked against the displayed source evidence."
        )

    gr.HTML(
        "<div class='footer-note'>"
        "AI Study Tutor · Human-Centered AI for Education · English + العربية · Source-grounded adaptive learning"
        "</div>"
    )

    demo.unload(cleanup_session)


if __name__ == "__main__":
    demo.launch(share=True)
