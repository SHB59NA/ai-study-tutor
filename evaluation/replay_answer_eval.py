from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evaluation.answer_grounding_eval import (
    AnswerCaseResult,
    evaluate_answer_case,
    load_dataset,
    print_report,
    summarize,
)


def load_saved_report(path: str | Path) -> dict[str, Any]:
    report_path = Path(path)
    if not report_path.exists():
        raise FileNotFoundError(f"Saved report not found: {report_path}")

    with report_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("Saved report must contain a non-empty 'results' list.")
    return data


def replay_saved_report(
    report_path: str | Path,
    dataset_path: str | Path,
) -> tuple[list[AnswerCaseResult], dict[str, Any]]:
    """Re-score previously generated answers without making any model API calls."""
    report = load_saved_report(report_path)
    dataset = load_dataset(dataset_path)
    cases_by_id = {str(case["id"]): case for case in dataset["cases"]}

    replayed: list[AnswerCaseResult] = []
    seen_case_ids: set[str] = set()

    for saved in report["results"]:
        if not isinstance(saved, dict):
            raise ValueError("Each saved result must be a JSON object.")

        case_id = str(saved.get("case_id", "")).strip()
        if not case_id:
            raise ValueError("Each saved result requires case_id.")
        if case_id in seen_case_ids:
            raise ValueError(f"Duplicate saved result for case {case_id!r}.")
        seen_case_ids.add(case_id)

        case = cases_by_id.get(case_id)
        if case is None:
            raise ValueError(
                f"Saved result case {case_id!r} is not present in the evaluation dataset."
            )

        source_pages = saved.get("source_pages", [])
        if not isinstance(source_pages, list):
            raise ValueError(f"Saved result {case_id!r} has invalid source_pages.")

        answer = str(saved.get("answer", ""))
        mode = str(saved.get("mode", ""))
        generation_error = saved.get("generation_error")
        if generation_error is not None:
            generation_error = str(generation_error)

        # Reports created before generation-error tracking can contain an
        # in-scope retrieval fallback with valid evidence but no generated answer.
        # Preserve that as an unscored generation event rather than treating the
        # fallback sentence itself as answer-quality output.
        if (
            case["type"] == "in_scope"
            and mode == "retrieval"
            and source_pages
            and not generation_error
        ):
            generation_error = (
                "LegacyGenerationFallback: saved run contains retrieved evidence "
                "but no generated answer"
            )

        replayed.append(
            evaluate_answer_case(
                case=case,
                answer=answer,
                sources=[{"page": int(page)} for page in source_pages],
                mode=mode,
                generation_error=generation_error,
            )
        )

    expected_case_ids = set(cases_by_id)
    missing = expected_case_ids - seen_case_ids
    if missing:
        raise ValueError(
            "Saved report is missing evaluation case(s): "
            + ", ".join(sorted(missing))
        )

    return replayed, summarize(replayed)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Re-score a saved answer-grounding report with the current deterministic "
            "evaluation logic. No Gemini/API calls are made."
        )
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path to a previously generated answer-grounding JSON report.",
    )
    parser.add_argument(
        "--dataset",
        default="evaluation/kuwait_bur_answer_eval.json",
        help="Path to the answer-grounding evaluation dataset.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path for the re-scored machine-readable report.",
    )
    args = parser.parse_args()

    results, metrics = replay_saved_report(args.report, args.dataset)
    print("\nOffline replay: no model API calls were made.")
    print_report(results, metrics)

    if args.json_out:
        output = {
            "replayed_from": str(args.report),
            "metrics": metrics,
            "results": [asdict(item) for item in results],
        }
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nJSON report written to: {output_path}")


if __name__ == "__main__":
    main()
