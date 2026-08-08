from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.llm import GeminiTutor
from app.tutor import StudyTutor


@dataclass
class FactResult:
    fact_id: str
    covered: bool
    citation_supported: bool
    expected_citation_pages: list[int]


@dataclass
class AnswerCaseResult:
    case_id: str
    case_type: str
    question: str
    passed: bool
    mode: str
    source_pages: list[int]
    cited_pages: list[int]
    invalid_citation_pages: list[int]
    fact_results: list[FactResult]
    fact_coverage: float
    citation_support_rate: float
    answer: str
    reason: str
    generation_error: str | None = None


def load_dataset(path: str | Path) -> dict[str, Any]:
    dataset_path = Path(path)
    with dataset_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation dataset must contain a non-empty 'cases' list.")

    for case in cases:
        if case.get("type") not in {"in_scope", "out_of_scope"}:
            raise ValueError(f"Invalid case type: {case.get('type')!r}")
        if not case.get("id") or not case.get("question"):
            raise ValueError("Every case requires 'id' and 'question'.")
        if case["type"] == "in_scope":
            facts = case.get("expected_facts")
            if not isinstance(facts, list) or not facts:
                raise ValueError(
                    f"In-scope case {case['id']!r} requires expected_facts."
                )
            for fact in facts:
                if not fact.get("id") or not fact.get("patterns"):
                    raise ValueError(
                        f"Every expected fact in {case['id']!r} requires id and patterns."
                    )
                if not fact.get("citation_pages"):
                    raise ValueError(
                        f"Every expected fact in {case['id']!r} requires citation_pages."
                    )

    return data


def _matches_patterns(text: str, patterns: list[str]) -> bool:
    return all(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _segments(text: str) -> list[str]:
    """Split an answer into citation-bearing units without splitting inside [p. N]."""
    segments: list[str] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue

        parts = re.split(
            r"(?<!p\.)(?<=[.!?])\s+(?=[A-Z0-9])",
            clean,
            flags=re.IGNORECASE,
        )
        segments.extend(part.strip() for part in parts if part.strip())
    return segments or [text]


def _pattern_has_expected_citation(
    answer: str,
    pattern: str,
    expected_pages: list[int],
) -> bool:
    """Check whether one required fact pattern is locally supported by an expected page."""
    expected = set(expected_pages)
    for segment in _segments(answer):
        if not re.search(pattern, segment, flags=re.IGNORECASE):
            continue
        cited = set(GeminiTutor.cited_pages(segment))
        if cited.intersection(expected):
            return True
    return False


def evaluate_fact(answer: str, fact: dict[str, Any]) -> FactResult:
    patterns = [str(item) for item in fact["patterns"]]
    expected_pages = [int(page) for page in fact["citation_pages"]]
    covered = _matches_patterns(answer, patterns)

    # A fact can legitimately be expressed across multiple sentences, e.g.
    # "Energy activities were dominant [p. 50]. They represented 95.6% [p. 50]."
    # Require every fact pattern to be locally backed by an expected page rather
    # than requiring all patterns and the citation to appear in one sentence.
    citation_supported = covered and all(
        _pattern_has_expected_citation(answer, pattern, expected_pages)
        for pattern in patterns
    )

    return FactResult(
        fact_id=str(fact["id"]),
        covered=covered,
        citation_supported=citation_supported,
        expected_citation_pages=expected_pages,
    )


def evaluate_answer_case(
    case: dict[str, Any],
    answer: str,
    sources: list[dict],
    mode: str,
    generation_error: str | None = None,
) -> AnswerCaseResult:
    source_pages = sorted({int(source["page"]) for source in sources})
    cited_pages = sorted(set(GeminiTutor.cited_pages(answer)))
    invalid_pages = GeminiTutor.invalid_citation_pages(answer, source_pages)

    if case["type"] == "out_of_scope":
        passed = mode == "retrieval" and not sources and not cited_pages
        reason = (
            "unsupported question correctly rejected without evidence or citations"
            if passed
            else "unsupported question was not cleanly rejected"
        )
        return AnswerCaseResult(
            case_id=str(case["id"]),
            case_type="out_of_scope",
            question=str(case["question"]),
            passed=passed,
            mode=mode,
            source_pages=source_pages,
            cited_pages=cited_pages,
            invalid_citation_pages=invalid_pages,
            fact_results=[],
            fact_coverage=1.0 if passed else 0.0,
            citation_support_rate=1.0 if passed else 0.0,
            answer=answer,
            reason=reason,
            generation_error=generation_error,
        )

    fact_results = [evaluate_fact(answer, fact) for fact in case["expected_facts"]]
    fact_coverage = sum(item.covered for item in fact_results) / len(fact_results)
    citation_support_rate = (
        sum(item.citation_supported for item in fact_results) / len(fact_results)
    )
    citation_valid = not invalid_pages
    passed = (
        mode == "gemini"
        and fact_coverage == 1.0
        and citation_support_rate == 1.0
        and citation_valid
    )

    reasons: list[str] = []
    if mode != "gemini":
        reasons.append(f"expected grounded Gemini mode, got {mode}")
        if generation_error:
            reasons.append(f"generation error: {generation_error}")
    if fact_coverage < 1.0:
        missing = [item.fact_id for item in fact_results if not item.covered]
        reasons.append(f"missing expected fact(s): {missing}")
    if citation_support_rate < 1.0:
        unsupported = [
            item.fact_id for item in fact_results if not item.citation_supported
        ]
        reasons.append(f"expected fact citation support missing: {unsupported}")
    if invalid_pages:
        reasons.append(f"citation(s) outside visible evidence: {invalid_pages}")

    return AnswerCaseResult(
        case_id=str(case["id"]),
        case_type="in_scope",
        question=str(case["question"]),
        passed=passed,
        mode=mode,
        source_pages=source_pages,
        cited_pages=cited_pages,
        invalid_citation_pages=invalid_pages,
        fact_results=fact_results,
        fact_coverage=round(fact_coverage, 4),
        citation_support_rate=round(citation_support_rate, 4),
        answer=answer,
        reason="; ".join(reasons) if reasons else "all expected facts and citations passed",
        generation_error=generation_error,
    )


def summarize(results: list[AnswerCaseResult]) -> dict[str, Any]:
    in_scope = [item for item in results if item.case_type == "in_scope"]
    out_scope = [item for item in results if item.case_type == "out_of_scope"]
    facts = [fact for item in in_scope for fact in item.fact_results]

    def rate(values: list[bool]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    return {
        "total_cases": len(results),
        "in_scope_cases": len(in_scope),
        "out_of_scope_cases": len(out_scope),
        "expected_fact_coverage": round(rate([fact.covered for fact in facts]), 4),
        "expected_citation_support_rate": round(
            rate([fact.citation_supported for fact in facts]), 4
        ),
        "citation_validity_case_rate": round(
            rate([not item.invalid_citation_pages for item in in_scope]), 4
        ),
        "out_of_scope_refusal_rate": round(rate([item.passed for item in out_scope]), 4),
        "overall_case_pass_rate": round(rate([item.passed for item in results]), 4),
    }


def evaluate_pdf(
    pdf_path: str | Path,
    dataset_path: str | Path,
) -> tuple[list[AnswerCaseResult], dict[str, Any]]:
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    dataset = load_dataset(dataset_path)
    tutor = StudyTutor()
    if not tutor.llm_available:
        raise RuntimeError(
            "GEMINI_API_KEY is required for generated-answer evaluation."
        )

    tutor.load_document(pdf.name, pdf.read_bytes())
    results: list[AnswerCaseResult] = []

    for case in dataset["cases"]:
        answer, sources, mode = tutor.answer(
            question=str(case["question"]),
            level=str(case.get("level", "beginner")),
            use_llm=True,
            language="english",
        )
        results.append(
            evaluate_answer_case(
                case=case,
                answer=answer,
                sources=sources,
                mode=mode,
                generation_error=tutor.last_generation_error,
            )
        )

    return results, summarize(results)


def print_report(results: list[AnswerCaseResult], metrics: dict[str, Any]) -> None:
    print("\nAI Study Tutor - Answer Grounding & Citation Evaluation")
    print("=" * 58)
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        print(f"[{status}] {item.case_id}")
        print(f"  type: {item.case_type}")
        print(f"  mode: {item.mode}")
        print(f"  source pages: {item.source_pages or 'NONE'}")
        print(f"  cited pages: {item.cited_pages or 'NONE'}")
        if item.case_type == "in_scope":
            print(f"  fact coverage: {item.fact_coverage:.1%}")
            print(f"  citation support: {item.citation_support_rate:.1%}")
        if item.invalid_citation_pages:
            print(f"  invalid citations: {item.invalid_citation_pages}")
        if item.generation_error:
            print(f"  generation error: {item.generation_error}")
        print(f"  {item.reason}")

    print("\nMetrics")
    print("-" * 58)
    print(f"Cases: {metrics['total_cases']}")
    print(f"Expected fact coverage: {metrics['expected_fact_coverage']:.1%}")
    print(
        "Expected citation support rate: "
        f"{metrics['expected_citation_support_rate']:.1%}"
    )
    print(
        "Citation validity case rate: "
        f"{metrics['citation_validity_case_rate']:.1%}"
    )
    print(
        "Out-of-source refusal rate: "
        f"{metrics['out_of_scope_refusal_rate']:.1%}"
    )
    print(f"Overall case pass rate: {metrics['overall_case_pass_rate']:.1%}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate generated answer fact coverage, citation validity, expected "
            "citation support, and unsupported-question refusal."
        )
    )
    parser.add_argument("--pdf", required=True, help="Path to the evaluation PDF.")
    parser.add_argument(
        "--dataset",
        default="evaluation/kuwait_bur_answer_eval.json",
        help="Path to the answer-grounding evaluation dataset.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path for a machine-readable JSON report.",
    )
    args = parser.parse_args()

    results, metrics = evaluate_pdf(args.pdf, args.dataset)
    print_report(results, metrics)

    if args.json_out:
        output = {
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
