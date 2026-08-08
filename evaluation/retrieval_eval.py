from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from app.retrieval import DocumentIndex


@dataclass
class CaseResult:
    case_id: str
    case_type: str
    question: str
    passed: bool
    expected_pages: list[int]
    retrieved_pages: list[int]
    retrieved_scores: list[float]
    reason: str


def load_dataset(path: str | Path) -> dict[str, Any]:
    dataset_path = Path(path)
    with dataset_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation dataset must contain a non-empty 'cases' list.")

    valid_types = {"in_scope", "out_of_scope"}
    for item in cases:
        if item.get("type") not in valid_types:
            raise ValueError(f"Invalid evaluation case type: {item.get('type')!r}")
        if not item.get("id") or not item.get("question"):
            raise ValueError("Every evaluation case requires 'id' and 'question'.")
        if item["type"] == "in_scope" and not item.get("expected_pages"):
            raise ValueError(f"In-scope case {item['id']!r} requires expected_pages.")

    return data


def evaluate_index(index: DocumentIndex, dataset: dict[str, Any], top_k: int = 3) -> list[CaseResult]:
    results: list[CaseResult] = []

    for case in dataset["cases"]:
        retrieved = index.search(case["question"], top_k=top_k)
        pages = [chunk.page for chunk, _ in retrieved]
        scores = [round(float(score), 4) for _, score in retrieved]
        expected_pages = [int(page) for page in case.get("expected_pages", [])]

        if case["type"] == "out_of_scope":
            passed = len(retrieved) == 0
            reason = (
                "correctly rejected as unsupported"
                if passed
                else f"unexpectedly retrieved page(s) {pages}"
            )
        else:
            page_hit = any(page in expected_pages for page in pages)
            passed = bool(retrieved) and page_hit
            if not retrieved:
                reason = "retrieval returned no evidence"
            elif page_hit:
                reason = "expected source page found in retrieved evidence"
            else:
                reason = f"expected page(s) {expected_pages}, got {pages}"

        results.append(
            CaseResult(
                case_id=case["id"],
                case_type=case["type"],
                question=case["question"],
                passed=passed,
                expected_pages=expected_pages,
                retrieved_pages=pages,
                retrieved_scores=scores,
                reason=reason,
            )
        )

    return results


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    in_scope = [item for item in results if item.case_type == "in_scope"]
    out_scope = [item for item in results if item.case_type == "out_of_scope"]

    def rate(items: list[CaseResult]) -> float:
        if not items:
            return 0.0
        return sum(1 for item in items if item.passed) / len(items)

    return {
        "total_cases": len(results),
        "in_scope_cases": len(in_scope),
        "out_of_scope_cases": len(out_scope),
        "top3_page_hit_rate": round(rate(in_scope), 4),
        "out_of_scope_rejection_rate": round(rate(out_scope), 4),
        "overall_case_pass_rate": round(rate(results), 4),
    }


def evaluate_pdf(
    pdf_path: str | Path,
    dataset_path: str | Path,
    top_k: int = 3,
) -> tuple[list[CaseResult], dict[str, Any]]:
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    dataset = load_dataset(dataset_path)
    index = DocumentIndex()
    index.load_pdf(pdf.read_bytes())
    results = evaluate_index(index=index, dataset=dataset, top_k=top_k)
    return results, summarize(results)


def print_report(results: list[CaseResult], metrics: dict[str, Any], top_k: int) -> None:
    print("\nAI Study Tutor - Retrieval Evaluation")
    print("=" * 44)
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        pages = item.retrieved_pages if item.retrieved_pages else "REJECTED"
        print(f"[{status}] {item.case_id}")
        print(f"  type: {item.case_type}")
        print(f"  retrieved: {pages}")
        if item.retrieved_scores:
            print(f"  scores: {item.retrieved_scores}")
        print(f"  {item.reason}")

    print("\nMetrics")
    print("-" * 44)
    print(f"Cases: {metrics['total_cases']}")
    print(f"Top-{top_k} expected-page hit rate: {metrics['top3_page_hit_rate']:.1%}")
    print(f"Out-of-source rejection rate: {metrics['out_of_scope_rejection_rate']:.1%}")
    print(f"Overall case pass rate: {metrics['overall_case_pass_rate']:.1%}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate page-aware TF-IDF retrieval and out-of-source rejection."
    )
    parser.add_argument("--pdf", required=True, help="Path to the evaluation PDF.")
    parser.add_argument(
        "--dataset",
        default="evaluation/kuwait_bur_eval.json",
        help="Path to the evaluation dataset JSON.",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of passages to retrieve.")
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path for a machine-readable JSON report.",
    )
    args = parser.parse_args()

    results, metrics = evaluate_pdf(args.pdf, args.dataset, top_k=args.top_k)
    print_report(results, metrics, top_k=args.top_k)

    if args.json_out:
        output = {
            "metrics": metrics,
            "results": [asdict(item) for item in results],
        }
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON report written to: {output_path}")


if __name__ == "__main__":
    main()
