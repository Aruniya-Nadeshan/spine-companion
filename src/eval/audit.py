"""Label audit: read what retrieval actually returned and check the evidence labels.

    python -m src.eval.audit                    # every dev in-scope question
    python -m src.eval.audit --ids q005,q017    # chosen questions
    python -m src.eval.audit --batch 2          # one batch of the dataset
    python -m src.eval.audit --split dev --k 5

For each question it prints the top-k chunks with their text. A chunk marked HIT contains
an evidence phrase. For a chunk that is NOT a hit, ask: does it clearly answer the question?
If yes, the label is incomplete: add that passage as extra evidence (and say why in "notes").
If no, retrieval really missed.

This is how retrieval evaluations avoid a bias: judge everything the system returned for
every question in the split, not only the failures, and write down the change. A label
change is not a retrieval improvement, so re-run the baseline after an audit and compare
later experiments against that new baseline.
"""
import argparse
import textwrap

from src.eval.retrieval_eval import is_hit, select_batch, select_split
from src.eval.schema import DEFAULT_PATH, load_questions


def audit_question(question, hits, preview_chars=420):
    """Printable lines for one question and its retrieved chunks."""
    lines = [f"\n{question['id']}  {question['question']}",
             "  evidence: " + "; ".join(f"[{e['source_id']}] {e['contains']!r}" for e in question["evidence"])]
    for rank, hit in enumerate(hits, start=1):
        meta = hit["metadata"]
        mark = "HIT " if is_hit(hit, question["evidence"]) else "    "
        text = " ".join(hit["text"].split())
        if len(text) > preview_chars:
            text = text[:preview_chars].rstrip() + "..."
        lines.append(f"  {mark}[{rank}] {hit['score']:.3f}  {meta['source_id']} > {meta['heading'][:70]}")
        lines.append(textwrap.fill(text, width=100, initial_indent="        ", subsequent_indent="        "))
    return lines


def main():
    parser = argparse.ArgumentParser(description="Audit evidence labels against retrieved chunks")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--ids", help="comma-separated question ids")
    parser.add_argument("--batch", type=int, help="only questions from this batch")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--questions", default=DEFAULT_PATH)
    args = parser.parse_args()

    from src.rag.embed import Embedder
    from src.rag.search import search

    questions = [q for q in load_questions(args.questions) if q["category"] == "in_scope"]
    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",")}
        questions = [q for q in questions if q["id"] in wanted]
    else:
        questions = select_batch(select_split(questions, args.split), args.batch)
    if args.split == "test" and not args.ids:
        print("Auditing the TEST split from retrieval results leaks information into it. "
              "Audit test labels by reading the sources, not the results.")
    embedder = Embedder()
    for q in questions:
        for line in audit_question(q, search(q["question"], embedder, k=args.k)):
            print(line)


if __name__ == "__main__":
    main()
