"""Reproducible retrieval-only evaluation on an original synthetic PDF."""
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
import json
import platform

from app.retrieval import DocumentIndex
from evaluation.retrieval_eval import evaluate_index, load_dataset, summarize
from examples.make_demo import make_demo_pdf


def run(output: Path | None = None) -> dict:
    root = Path(__file__).resolve().parents[1]
    dataset_path = root / "evaluation/synthetic_retrieval_cases.json"
    data = make_demo_pdf()
    index = DocumentIndex()
    index.load_pdf(data)
    cases = evaluate_index(index, load_dataset(dataset_path), top_k=3)
    report = {
        "benchmark": "Fictional IT Handbook - developer smoke benchmark v1",
        "scope": "Local English PDF extraction/retrieval only. NOT generated-answer accuracy or educational effectiveness.",
        "independent_test_set": False,
        "external_model_calls": 0,
        "source_pdf_sha256": sha256(data).hexdigest(),
        "dataset_sha256": sha256(dataset_path.read_bytes()).hexdigest(),
        "environment": {"python": platform.python_version(), "pypdf": version("pypdf"),
                        "scikit-learn": version("scikit-learn"), "numpy": version("numpy")},
        "retrieval_config": {"top_k": 3, "chunk_size": 900, "overlap": 150,
                             "minimum_score": index.MIN_RELEVANCE_SCORE,
                             "coverage_threshold": index.LOW_COVERAGE_THRESHOLD,
                             "coverage_override": index.LOW_COVERAGE_SCORE_OVERRIDE},
        "metrics": summarize(cases),
        "results": [asdict(case) for case in cases],
    }
    output = output or root / "artifacts/synthetic_retrieval.json"
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["metrics"], indent=2))
    for case in cases:
        print(f"{'PASS' if case.passed else 'FAIL'} {case.case_id}: {case.reason}")
    print(f"Report: {output}")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    run(parser.parse_args().output)
