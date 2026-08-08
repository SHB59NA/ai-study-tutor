from pathlib import Path

import gradio as gr

from app.tutor import StudyTutor


tutor = StudyTutor()


def upload_pdf(file_path):
    if not file_path:
        return "Please choose a PDF file first."

    path = Path(str(file_path))
    if path.suffix.lower() != ".pdf":
        return "Please upload a PDF file."

    try:
        chunks = tutor.load_document(path.name, path.read_bytes())
    except Exception as exc:
        return f"Unable to process the PDF: {exc}"

    return (
        f"Loaded **{path.name}** successfully.\n\n"
        f"Indexed **{chunks}** source chunks. You can now ask questions or generate a quiz."
    )


def ask_tutor(question, level):
    if tutor.document_name is None:
        return "Upload a PDF first.", ""
    if not question or len(question.strip()) < 3:
        return "Please enter a question.", ""

    try:
        answer, sources, mode = tutor.answer(
            question.strip(),
            top_k=3,
            level=level,
            use_llm=True,
        )
    except Exception as exc:
        return f"Unable to answer: {exc}", ""

    evidence = []
    for source in sources:
        evidence.append(
            f"**PDF page {source['page']}** — retrieval score {source['score']}\n\n"
            f"> {source['text']}"
        )

    source_text = "\n\n---\n\n".join(evidence)
    return f"**Mode:** {mode}\n\n{answer}", source_text


def generate_quiz_question(topic, difficulty):
    if tutor.document_name is None:
        return None, "Upload a PDF first.", ""
    if not topic or len(topic.strip()) < 3:
        return None, "Enter a quiz topic first.", ""

    try:
        questions = tutor.create_quiz(
            topic=topic.strip(),
            difficulty=difficulty,
            count=1,
            top_k=5,
        )
    except Exception as exc:
        return None, f"Unable to generate a quiz: {exc}", ""

    q = questions[0]
    meta = f"Concept: **{q['concept']}**  |  Source: **PDF page {q['page']}**"
    return q["id"], q["question"], meta


def grade_answer(question_id, student_answer):
    if not question_id:
        return "Generate a quiz question first.", {}
    if not student_answer or not student_answer.strip():
        return "Write your answer first.", {}

    try:
        result = tutor.grade_quiz_answer(
            question_id=question_id,
            student_answer=student_answer.strip(),
        )
    except Exception as exc:
        return f"Unable to grade the answer: {exc}", {}

    feedback = (
        f"### Score: {result['score']:.0%}\n\n"
        f"**Concept:** {result['concept']}\n\n"
        f"**Feedback:** {result['feedback']}\n\n"
        f"**Review recommendation:** {result['review_recommendation']}\n\n"
        f"**Next difficulty:** {result['next_difficulty']}"
    )
    return feedback, tutor.get_progress()


def show_progress():
    return tutor.get_progress()


def personalized_review(concept, level):
    if tutor.document_name is None:
        return "Upload a PDF first.", ""

    selected_concept = concept.strip() if concept and concept.strip() else None
    selected_level = None if level == "auto" else level

    try:
        concept_name, answer, sources, mode, final_level = tutor.personalized_review(
            concept=selected_concept,
            level=selected_level,
            top_k=3,
        )
    except Exception as exc:
        return f"Unable to create a review: {exc}", ""

    evidence = []
    for source in sources:
        evidence.append(
            f"**PDF page {source['page']}**\n\n> {source['text']}"
        )

    header = (
        f"### Review: {concept_name}\n\n"
        f"**Level:** {final_level}  |  **Mode:** {mode}\n\n"
        f"{answer}"
    )
    return header, "\n\n---\n\n".join(evidence)


with gr.Blocks(title="AI Study Tutor") as demo:
    gr.Markdown(
        "# AI Study Tutor\n"
        "A source-grounded, adaptive learning assistant for educational PDFs."
    )

    with gr.Tab("1. Upload"):
        pdf_file = gr.File(label="Study PDF", file_types=[".pdf"], type="filepath")
        upload_button = gr.Button("Load study material", variant="primary")
        upload_status = gr.Markdown()
        upload_button.click(upload_pdf, inputs=pdf_file, outputs=upload_status)

    with gr.Tab("2. Ask Tutor"):
        question = gr.Textbox(
            label="Question",
            placeholder="Ask something about the uploaded study material...",
            lines=3,
        )
        level = gr.Radio(
            ["beginner", "intermediate", "advanced"],
            value="intermediate",
            label="Explanation level",
        )
        ask_button = gr.Button("Ask", variant="primary")
        answer_output = gr.Markdown()
        with gr.Accordion("Retrieved source evidence", open=False):
            source_output = gr.Markdown()
        ask_button.click(
            ask_tutor,
            inputs=[question, level],
            outputs=[answer_output, source_output],
        )

    with gr.Tab("3. Adaptive Quiz"):
        quiz_id = gr.State()
        topic = gr.Textbox(
            label="Quiz topic",
            placeholder="Example: climate change in Kuwait",
        )
        difficulty = gr.Radio(
            ["beginner", "intermediate", "advanced"],
            value="beginner",
            label="Difficulty",
        )
        generate_button = gr.Button("Generate question", variant="primary")
        quiz_question = gr.Markdown()
        quiz_meta = gr.Markdown()
        student_answer = gr.Textbox(label="Your answer", lines=4)
        grade_button = gr.Button("Submit answer")
        grade_output = gr.Markdown()
        progress_after_grade = gr.JSON(label="Learning progress")

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

    with gr.Tab("4. Progress"):
        progress_button = gr.Button("Refresh progress")
        progress_output = gr.JSON(label="Current learner model")
        progress_button.click(show_progress, outputs=progress_output)

    with gr.Tab("5. Personalized Review"):
        gr.Markdown(
            "Leave the concept blank to automatically review the weakest detected concept."
        )
        review_concept = gr.Textbox(label="Concept (optional)")
        review_level = gr.Dropdown(
            ["auto", "beginner", "intermediate", "advanced"],
            value="auto",
            label="Review level",
        )
        review_button = gr.Button("Create personalized review", variant="primary")
        review_output = gr.Markdown()
        with gr.Accordion("Review source evidence", open=False):
            review_sources = gr.Markdown()

        review_button.click(
            personalized_review,
            inputs=[review_concept, review_level],
            outputs=[review_output, review_sources],
        )

    gr.Markdown(
        "---\n"
        "**Prototype note:** learner mastery is a transparent research prototype and is not a validated assessment score."
    )


if __name__ == "__main__":
    demo.launch(share=True)
