from pathlib import Path

import gradio as gr

from app.tutor import StudyTutor


tutor = StudyTutor()


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
    max-width: 760px;
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

.section-card {
    border: 1px solid var(--border-color-primary);
    border-radius: 18px;
    padding: 16px;
    background: var(--background-fill-primary);
}

.answer-card {
    border-left: 4px solid var(--color-accent);
    padding-left: 14px;
}

.subtle-note {
    opacity: 0.78;
    font-size: 0.92rem;
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
    A source-grounded adaptive learning assistant that turns educational PDFs into
    explanations, quizzes, progress insights, and personalized review.
  </p>
  <div class="hero-badges">
    <span class="hero-badge">Source-grounded RAG</span>
    <span class="hero-badge">Adaptive quizzes</span>
    <span class="hero-badge">Weak-concept detection</span>
    <span class="hero-badge">Personalized review</span>
  </div>
</div>
"""


def format_progress() -> str:
    progress = tutor.get_progress()
    mastery = float(progress["mastery_score"])
    attempts = int(progress["attempts"])
    next_difficulty = progress["next_difficulty"]
    weak_concepts = progress["weak_concepts"]

    if weak_concepts:
        rows = []
        for item in weak_concepts:
            rows.append(
                f"| {item['concept']} | {item['attempts']} | {float(item['mastery']):.0%} |"
            )
        weak_section = (
            "### Concepts to review\n\n"
            "| Concept | Attempts | Mastery |\n"
            "|---|---:|---:|\n"
            + "\n".join(rows)
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


def upload_pdf(file_path):
    if not file_path:
        return "### No document selected\nChoose a PDF file, then click **Load study material**."

    path = Path(str(file_path))
    if path.suffix.lower() != ".pdf":
        return "### Unsupported file\nPlease upload a PDF document."

    try:
        chunks = tutor.load_document(path.name, path.read_bytes())
    except Exception as exc:
        return f"### Upload failed\n`{exc}`"

    return (
        "### Document ready\n\n"
        f"**File:** {path.name}  \n"
        f"**Indexed source chunks:** {chunks}  \n\n"
        "You can now use **Ask Tutor** or **Adaptive Quiz**. Loading a new PDF resets the current learner progress."
    )


def ask_tutor(question, level):
    if tutor.document_name is None:
        return "### Upload a PDF first\nThe tutor needs a source document before it can answer.", ""
    if not question or len(question.strip()) < 3:
        return "### Enter a question\nAsk something specific about the uploaded material.", ""

    try:
        answer, sources, mode = tutor.answer(
            question.strip(),
            top_k=3,
            level=level,
            use_llm=True,
        )
    except Exception as exc:
        return f"### Unable to answer\n`{exc}`", ""

    evidence = []
    for source in sources:
        evidence.append(
            f"### PDF page {source['page']}\n"
            f"**Retrieval score:** {source['score']}\n\n"
            f"> {source['text']}"
        )

    source_text = "\n\n---\n\n".join(evidence)
    mode_label = "Grounded Gemini" if mode == "gemini" else "Retrieval fallback"
    response = (
        "## Tutor response\n\n"
        f"**Explanation level:** `{level}`  \n"
        f"**Mode:** {mode_label}\n\n"
        f"{answer}"
    )
    return response, source_text


def generate_quiz_question(topic, difficulty):
    if tutor.document_name is None:
        return None, "### Upload a PDF first\nA quiz must be generated from source material.", ""
    if not topic or len(topic.strip()) < 3:
        return None, "### Enter a quiz topic\nExample: *Climate Change Impacts in Kuwait*", ""

    try:
        questions = tutor.create_quiz(
            topic=topic.strip(),
            difficulty=difficulty,
            count=1,
            top_k=5,
        )
    except Exception as exc:
        return None, f"### Unable to generate a quiz\n`{exc}`", ""

    q = questions[0]
    meta = (
        f"**Concept:** {q['concept']}  \n"
        f"**Difficulty:** `{difficulty}`  \n"
        f"**Grounding source:** PDF page {q['page']}"
    )
    return q["id"], f"## {q['question']}", meta


def grade_answer(question_id, student_answer):
    if not question_id:
        return "### Generate a quiz question first.", format_progress()
    if not student_answer or not student_answer.strip():
        return "### Write your answer before submitting.", format_progress()

    try:
        result = tutor.grade_quiz_answer(
            question_id=question_id,
            student_answer=student_answer.strip(),
        )
    except Exception as exc:
        return f"### Unable to grade the answer\n`{exc}`", format_progress()

    verdict = "Correct / strong answer" if result["correct"] else "Needs review"
    feedback = (
        f"## {verdict}\n\n"
        f"**Score:** {result['score']:.0%}  \n"
        f"**Concept:** {result['concept']}  \n"
        f"**Source page:** {result['source_page']}\n\n"
        f"### Tutor feedback\n{result['feedback']}\n\n"
        f"### Recommended next step\n{result['review_recommendation']}"
    )
    return feedback, format_progress()


def show_progress():
    return format_progress()


def personalized_review(concept, level):
    if tutor.document_name is None:
        return "### Upload a PDF first\nPersonalized review must be grounded in a source document.", ""

    selected_concept = concept.strip() if concept and concept.strip() else None
    selected_level = None if level == "auto" else level

    try:
        concept_name, answer, sources, mode, final_level = tutor.personalized_review(
            concept=selected_concept,
            level=selected_level,
            top_k=3,
        )
    except Exception as exc:
        return f"### Unable to create a review\n`{exc}`", ""

    evidence = []
    for source in sources:
        evidence.append(
            f"### PDF page {source['page']}\n\n> {source['text']}"
        )

    mode_label = "Grounded Gemini" if mode == "gemini" else "Retrieval fallback"
    header = (
        f"## Review: {concept_name}\n\n"
        f"**Level:** `{final_level}`  \n"
        f"**Mode:** {mode_label}\n\n"
        f"{answer}"
    )
    return header, "\n\n---\n\n".join(evidence)


with gr.Blocks(
    title="AI Study Tutor | Source-Grounded Adaptive Learning",
    theme=gr.themes.Soft(),
    css=APP_CSS,
) as demo:
    gr.HTML(HERO_HTML)

    gr.Markdown(
        "**Recommended workflow:** Upload a PDF → Ask questions → Practice with a quiz → "
        "Check progress → Review weak concepts."
    )

    with gr.Tab("1 · Upload"):
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("## Start with trusted study material")
                gr.Markdown(
                    "Upload one educational PDF. The tutor indexes the document and uses it as the "
                    "evidence base for answers, quizzes, and personalized review."
                )
                pdf_file = gr.File(
                    label="Study material (PDF)",
                    file_types=[".pdf"],
                    type="filepath",
                )
                upload_button = gr.Button("Load study material", variant="primary")
                upload_status = gr.Markdown()
                upload_button.click(upload_pdf, inputs=pdf_file, outputs=upload_status)

            with gr.Column(scale=2):
                gr.Markdown(
                    "## What happens next?\n\n"
                    "1. Text is extracted page by page.\n"
                    "2. The document is split into searchable chunks.\n"
                    "3. Relevant passages are retrieved for each request.\n"
                    "4. Gemini generates explanations only from retrieved evidence.\n\n"
                    "**Privacy note:** this prototype processes the uploaded document for the active session."
                )

    with gr.Tab("2 · Ask Tutor"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Ask a grounded question")
                question = gr.Textbox(
                    label="Question",
                    placeholder="Example: How is climate change expected to affect Kuwait's temperature and rainfall?",
                    lines=4,
                )
                level = gr.Radio(
                    ["beginner", "intermediate", "advanced"],
                    value="intermediate",
                    label="Explanation level",
                )
                ask_button = gr.Button("Ask tutor", variant="primary")

            with gr.Column(scale=3):
                answer_output = gr.Markdown(elem_classes=["answer-card"])
                with gr.Accordion("View retrieved source evidence", open=False):
                    source_output = gr.Markdown()

        ask_button.click(
            ask_tutor,
            inputs=[question, level],
            outputs=[answer_output, source_output],
        )

    with gr.Tab("3 · Adaptive Quiz"):
        quiz_id = gr.State()

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Practice from the same source")
                topic = gr.Textbox(
                    label="Quiz topic",
                    placeholder="Example: Climate Change Impacts in Kuwait",
                )
                difficulty = gr.Radio(
                    ["beginner", "intermediate", "advanced"],
                    value="beginner",
                    label="Question difficulty",
                )
                generate_button = gr.Button("Generate question", variant="primary")
                quiz_meta = gr.Markdown()

            with gr.Column(scale=3):
                quiz_question = gr.Markdown()
                student_answer = gr.Textbox(
                    label="Your answer",
                    placeholder="Write your answer in your own words...",
                    lines=5,
                )
                grade_button = gr.Button("Submit answer")

        gr.Markdown("---")
        with gr.Row():
            with gr.Column(scale=3):
                grade_output = gr.Markdown(elem_classes=["answer-card"])
            with gr.Column(scale=2):
                progress_after_grade = gr.Markdown()

        generate_button.click(
            generate_quiz_question,
            inputs=[topic, difficulty],
            outputs=[quiz_id, quiz_question, quiz_meta],
        )
        grade_button.click(
            grade_answer,
            inputs=[quiz_id, student_answer],
            outputs=[grade_output, progress_after_grade],
        )

    with gr.Tab("4 · Progress"):
        gr.Markdown(
            "## Transparent learner model\n"
            "The prototype uses recent quiz performance to estimate overall mastery, recommend the "
            "next difficulty, and identify concepts that may need review."
        )
        progress_button = gr.Button("Refresh learning snapshot", variant="primary")
        progress_output = gr.Markdown()
        progress_button.click(show_progress, outputs=progress_output)

    with gr.Tab("5 · Personalized Review"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Review what needs attention")
                gr.Markdown(
                    "Leave the concept blank and the tutor will automatically select the weakest "
                    "detected concept. You can also enter a concept manually."
                )
                review_concept = gr.Textbox(
                    label="Concept (optional)",
                    placeholder="Leave blank for automatic weak-concept review",
                )
                review_level = gr.Dropdown(
                    ["auto", "beginner", "intermediate", "advanced"],
                    value="auto",
                    label="Review level",
                )
                review_button = gr.Button("Create personalized review", variant="primary")

            with gr.Column(scale=3):
                review_output = gr.Markdown(elem_classes=["answer-card"])
                with gr.Accordion("View review source evidence", open=False):
                    review_sources = gr.Markdown()

        review_button.click(
            personalized_review,
            inputs=[review_concept, review_level],
            outputs=[review_output, review_sources],
        )

    with gr.Tab("About"):
        gr.Markdown(
            "## Research motivation\n\n"
            "AI Study Tutor is an educational AI prototype exploring how source-grounded language models "
            "can support learning without replacing educators. The system combines retrieval-augmented "
            "generation, adaptive explanation levels, quiz generation, answer feedback, transparent "
            "mastery tracking, weak-concept detection, and personalized review.\n\n"
            "### Design principles\n\n"
            "- **Ground before generating:** retrieve evidence from the uploaded PDF first.\n"
            "- **Make evidence visible:** expose source pages and retrieved passages.\n"
            "- **Adapt to the learner:** vary explanation and practice difficulty.\n"
            "- **Support productive learning:** use feedback and targeted review instead of only giving answers.\n"
            "- **Keep the model transparent:** the mastery score is intentionally simple and inspectable.\n\n"
            "### Prototype limitation\n\n"
            "The mastery model is a research prototype, not a validated educational assessment instrument. "
            "Generated answers and grading should be checked against the displayed source evidence and, "
            "where appropriate, an instructor."
        )

    gr.HTML(
        "<div class='footer-note'>"
        "AI Study Tutor · Human-Centered AI for Education · Source-grounded adaptive learning prototype"
        "</div>"
    )


if __name__ == "__main__":
    demo.launch(share=True)
