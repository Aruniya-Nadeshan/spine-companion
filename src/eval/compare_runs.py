"""Compare two saved evaluation runs, question by question, and show where their results come from.

    python -m src.eval.compare_runs baseline-v1.1 no-heading
    python -m src.eval.compare_runs no-heading heading-only

Each argument is a run label (the newest run with that label is used) or a path to a run file.
Both runs must use the same dataset and split, otherwise the comparison is not valid.

The source mix shows, for each run, what share of the top-1 and top-3 results came from each
source. If a change moves results from one source to another, this is where it shows.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from src.eval.experiment import compare_rows, format_comparison
from src.eval.retrieval_eval import RUNS_DIR


def load_run(ref, runs_dir=RUNS_DIR):
    """Load a run by path, or by label (newest run whose label matches exactly)."""
    path = Path(ref)
    if path.exists():
        return path, json.loads(path.read_text(encoding="utf-8"))
    matches = []
    for candidate in sorted(Path(runs_dir).glob("*.json")):
        record = json.loads(candidate.read_text(encoding="utf-8"))
        if record["label"] == ref:
            matches.append((candidate, record))
    if not matches:
        raise FileNotFoundError(f"No run labelled '{ref}' in {runs_dir}")
    return matches[-1]


def source_mix(rows):
    """Share of top-1 and top-3 results per source, for in-scope questions."""
    in_scope = [r for r in rows if r["category"] == "in_scope" and r["top_sources"]]
    top1 = Counter(r["top_sources"][0] for r in in_scope)
    top3 = Counter(s for r in in_scope for s in r["top_sources"][:3])
    n1, n3 = sum(top1.values()), sum(top3.values())
    return {source: {"top1": top1[source] / n1 if n1 else 0.0, "top3": top3[source] / n3 if n3 else 0.0}
            for source in sorted(set(top1) | set(top3))}


def format_source_mix(label, mix):
    lines = [f"  {label}"]
    for source, share in mix.items():
        lines.append(f"    {source:40} top-1 {share['top1']:.0%}   top-3 {share['top3']:.0%}")
    return "\n".join(lines)


def check_comparable(a, b):
    problems = []
    if a["dataset"] != b["dataset"]:
        problems.append(f"different datasets ({a['dataset']} vs {b['dataset']})")
    if a["split"] != b["split"]:
        problems.append(f"different splits ({a['split']} vs {b['split']})")
    if a.get("batch") != b.get("batch"):
        problems.append(f"different batches ({a.get('batch')} vs {b.get('batch')})")
    return problems


def main():
    parser = argparse.ArgumentParser(description="Compare two evaluation runs")
    parser.add_argument("first", help="the reference run (label or path)")
    parser.add_argument("second", help="the run to judge (label or path)")
    args = parser.parse_args()

    path_a, run_a = load_run(args.first)
    path_b, run_b = load_run(args.second)
    problems = check_comparable(run_a, run_b)
    if problems:
        raise SystemExit("These runs cannot be compared: " + "; ".join(problems))

    summary, detail = compare_rows(run_a["rows"], run_b["rows"])
    print(f"\n{run_a['label']} ({path_a.name})  vs  {run_b['label']} ({path_b.name})")
    print(format_comparison(summary, detail, run_a["label"], run_b["label"]))
    print("\nWhere the top results come from (in-scope questions):")
    print(format_source_mix(run_a["label"], source_mix(run_a["rows"])))
    print(format_source_mix(run_b["label"], source_mix(run_b["rows"])))


if __name__ == "__main__":
    main()
