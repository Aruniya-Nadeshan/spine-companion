"""Print the per-question results of a saved evaluation run.

    python -m src.eval.show_run              # latest run, every question
    python -m src.eval.show_run --misses     # only in-scope questions with no correct chunk in the top k
    python -m src.eval.show_run --run data/eval/runs/20261121-125221-baseline.json

The summary report tells you how well retrieval did. This view tells you where it failed:
what each question retrieved instead of the passage that answers it.
"""
import argparse
import json
from pathlib import Path

from src.eval.schema import load_questions, DEFAULT_PATH
from src.rag.console import configure_console

RUNS_DIR = "data/eval/runs"


def latest_run(runs_dir=RUNS_DIR):
    runs = sorted(Path(runs_dir).glob("*.json"))
    if not runs:
        raise FileNotFoundError(f"No runs in {runs_dir}. Run: python -m src.eval.retrieval_eval --label baseline")
    return runs[-1]


def format_rows(rows, questions, only_misses=False, only_in_scope=True):
    """Return printable lines: id, rank, top score, question text and the top retrieved headings."""
    text = {q["id"]: q["question"] for q in questions}
    lines = []
    for r in rows:
        if only_in_scope and r["category"] != "in_scope":
            continue
        if only_misses and r["rank"] is not None:
            continue
        rank = r["rank"] if r["rank"] is not None else "MISS"
        score = f"{r['top_score']:.3f}" if r["top_score"] is not None else "-"
        lines.append(f"{r['id']}  rank={rank!s:<4} top={score}  {text.get(r['id'], '')[:90]}")
        for source, heading in zip(r["top_sources"], r["top_headings"]):
            lines.append(f"      - {source} > {heading}")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Show per-question results of an evaluation run")
    parser.add_argument("--run")
    parser.add_argument("--misses", action="store_true")
    parser.add_argument("--all-types", action="store_true", help="include out-of-scope and safety questions")
    parser.add_argument("--questions", default=DEFAULT_PATH)
    args = parser.parse_args()
    configure_console()

    path = Path(args.run) if args.run else latest_run()
    record = json.loads(path.read_text(encoding="utf-8"))
    print(f"Run: {path.name}   label={record['label']}   split={record['split']}   dataset={record['dataset']}")
    print(f"Settings: {record['settings']}\n")
    questions = load_questions(args.questions)
    for line in format_rows(record["rows"], questions, args.misses, not args.all_types):
        print(line)


if __name__ == "__main__":
    main()
