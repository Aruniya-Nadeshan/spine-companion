"""Run one retrieval experiment in its own temporary index and compare it with a baseline.

    python -m src.eval.experiment --name no-heading --embed-text none
    python -m src.eval.experiment --name small-chunks --chunk-target 120 --chunk-overlap 20
    python -m src.eval.experiment --name bge-base --model BAAI/bge-base-en-v1.5
    python -m src.eval.experiment --name hybrid --hybrid
    python -m src.eval.experiment --name rerank --rerank

The main index (data/index) is never touched. Each experiment builds data/index_exp/<name>,
evaluates it on the dev split, saves a run file, and prints a question-by-question comparison
with the baseline run (default: the newest run labelled baseline-*). Change ONE thing per
experiment, so any difference can be attributed to it.

Why question by question? With ~20 questions a change in the average is mostly noise, but
"these 3 questions got better, these 0 got worse" is evidence. The sign test below turns
that into a probability.
"""
import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path

from src.eval.retrieval_eval import (KS, RUNS_DIR, dataset_fingerprint, evaluate_retrieval, format_report,
                                     git_commit, save_run, select_batch, select_split)
from src.eval.schema import DEFAULT_PATH, load_questions, summarise, validate_questions

EXPERIMENT_INDEX_DIR = "data/index_exp"
EMBED_TEXT_MODES = ("title_heading", "heading", "none")


def index_name(name):
    """A safe folder and collection name (ChromaDB accepts only letters, digits, dots, dashes, underscores)."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "-", name).strip("-._") or "experiment"
    return f"exp-{cleaned}"


def apply_embed_text_mode(chunks, mode):
    """Change what the embedding model reads for each chunk (the displayed text never changes).

    title_heading: "<document title> | <heading>\\n<text>"   (the current baseline)
    heading:       "<heading>\\n<text>"
    none:          "<text>" only
    """
    if mode not in EMBED_TEXT_MODES:
        raise ValueError(f"embed text mode must be one of {EMBED_TEXT_MODES}")
    for chunk in chunks:
        if mode == "title_heading":
            chunk.embed_text = f"{chunk.doc_title} | {chunk.heading}\n{chunk.text}"
        elif mode == "heading":
            chunk.embed_text = f"{chunk.heading}\n{chunk.text}"
        else:
            chunk.embed_text = chunk.text
    return chunks


# ---------------------------------------------------------------- comparing two runs

def rank_value(rank):
    """Lower is better; a missing hit is worse than any rank."""
    return math.inf if rank is None else rank


def compare_rows(baseline_rows, variant_rows):
    """Question-by-question comparison of in-scope ranks. Returns (summary, details)."""
    base = {r["id"]: r["rank"] for r in baseline_rows if r["category"] == "in_scope"}
    new = {r["id"]: r["rank"] for r in variant_rows if r["category"] == "in_scope"}
    shared = sorted(set(base) & set(new))
    better, worse, same = [], [], []
    for qid in shared:
        a, b = rank_value(base[qid]), rank_value(new[qid])
        (better if b < a else worse if b > a else same).append(qid)
    detail = {qid: (base[qid], new[qid]) for qid in shared}
    summary = {"compared": len(shared), "better": better, "worse": worse, "same": same,
               "sign_test_p": sign_test_p(len(better), len(worse))}
    return summary, detail


def sign_test_p(wins, losses):
    """Two-sided exact sign test: how surprising is this split if the change did nothing?

    Questions whose rank did not change are ignored. A small p (below about 0.05) suggests the
    difference is real; with few changed questions even a clean 3-0 split gives p = 0.25.
    """
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def format_comparison(summary, detail, baseline_label, variant_label):
    lines = [f"\nComparison with {baseline_label}  ({summary['compared']} in-scope questions)",
             f"  better: {len(summary['better'])}   worse: {len(summary['worse'])}   same: {len(summary['same'])}"
             f"   sign test p = {summary['sign_test_p']:.3f}"]
    for title, ids in (("improved", summary["better"]), ("got worse", summary["worse"])):
        if ids:
            lines.append(f"  {title}:")
            for qid in ids:
                old, new = detail[qid]
                lines.append(f"    {qid}: rank {old if old else 'MISS'} -> {new if new else 'MISS'}")
    lines.append(f"  ({variant_label} is only a candidate if it improves some questions without making others worse.)")
    return "\n".join(lines)


def markdown_row(record, baseline_label=None):
    s = record["summary"]
    cells = [datetime.now().strftime("%Y-%m-%d"), record["label"], record.get("change", ""),
             record["dataset"], record["split"], str(s["n_in_scope"]),
             *(f"{s[f'hit@{k}']['value']:.3f}" for k in KS if f"hit@{k}" in s), f"{s['mrr']:.3f}",
             f"compare with {baseline_label}" if baseline_label else ""]
    return "| " + " | ".join(cells) + " |"


def find_baseline(runs_dir=RUNS_DIR, prefix="baseline", dataset=None, split=None, batch=None):
    """Newest saved run whose label starts with the prefix and that is comparable.

    When dataset, split or batch are given, only runs made with exactly those are considered,
    so a comparison can never silently mix different question sets.
    """
    candidates = []
    for path in sorted(Path(runs_dir).glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not record["label"].startswith(prefix):
            continue
        if dataset is not None and record.get("dataset") != dataset:
            continue
        if split is not None and record.get("split") != split:
            continue
        if record.get("batch") != batch:
            continue
        candidates.append((path, record))
    if not candidates:
        raise FileNotFoundError(
            f"No saved run labelled '{prefix}*' for dataset={dataset}, split={split}, batch={batch} in {runs_dir}. "
            "Run the baseline first with the same --split and --batch.")
    return candidates[-1]


# ---------------------------------------------------------------- running a variant

def build_variant(name, docs, embedder, chunk_target, chunk_overlap, min_words, embed_text, index_root=EXPERIMENT_INDEX_DIR):
    """Chunk and index the corpus with the variant's settings; return the number of chunks."""
    from src.rag.chunk import chunk_all
    from src.rag.index import build_index

    chunks = chunk_all(docs, chunk_target, chunk_overlap, min_words)
    apply_embed_text_mode(chunks, embed_text)
    safe = index_name(name)
    build_index(chunks, embedder, index_dir=Path(index_root) / safe, collection=safe)
    return len(chunks)


def run_variant(questions, embedder, name, k, index_root=EXPERIMENT_INDEX_DIR, hybrid=False,
                reranker=None, candidates=20):
    """Evaluate a variant's index with the chosen retrieval pipeline (vector, hybrid, reranked)."""
    from src.rag.retrieve import Retriever
    safe = index_name(name)
    retriever = Retriever(embedder, Path(index_root) / safe, safe, hybrid=hybrid, reranker=reranker,
                          candidates=candidates)
    return evaluate_retrieval(questions, retriever, k=k)


def main():
    from src.rag import config

    parser = argparse.ArgumentParser(description="Run a retrieval experiment against the baseline")
    parser.add_argument("--name", required=True, help="short label, e.g. no-heading")
    parser.add_argument("--change", default="", help="one-line description of what changed")
    parser.add_argument("--embed-text", choices=EMBED_TEXT_MODES, default="title_heading")
    parser.add_argument("--chunk-target", type=int, default=config.CHUNK_TARGET_WORDS)
    parser.add_argument("--chunk-overlap", type=int, default=config.CHUNK_OVERLAP_WORDS)
    parser.add_argument("--min-chunk-words", type=int, default=config.MIN_CHUNK_WORDS)
    parser.add_argument("--model", default=config.EMBED_MODEL)
    parser.add_argument("--hybrid", action="store_true", help="fuse vector search with keyword (BM25) search")
    parser.add_argument("--rerank", nargs="?", const="default",
                        help="rerank candidates with a cross-encoder (optionally give the model name)")
    parser.add_argument("--candidates", type=int, default=20, help="candidates passed to the fusion/reranking stage")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--batch", type=int, help="only questions from this batch (default: all batches)")
    parser.add_argument("--baseline", help="path to a saved run to compare with (default: newest baseline-*)")
    parser.add_argument("--questions", default=DEFAULT_PATH)
    args = parser.parse_args()

    from src.rag.chunk import load_processed_docs
    from src.rag.embed import Embedder

    docs = load_processed_docs(config.PROCESSED_DIR)
    questions = load_questions(args.questions)
    errors, _ = validate_questions(questions, docs)
    if errors:
        raise SystemExit("The question file has errors:\n  - " + "\n  - ".join(errors))
    if args.split == "test":
        print("Running on the TEST split. Do this only to report a finished design, never to choose between variants.")
    selected = select_batch(select_split(questions, args.split), args.batch)
    fingerprint = dataset_fingerprint(args.questions)

    if args.baseline:
        base_path = Path(args.baseline)
        base_record = json.loads(base_path.read_text(encoding="utf-8"))
    else:
        try:
            base_path, base_record = find_baseline(dataset=fingerprint, split=args.split, batch=args.batch)
        except FileNotFoundError as exc:
            raise SystemExit(str(exc))
    if (base_record["dataset"], base_record["split"], base_record.get("batch")) != (fingerprint, args.split, args.batch):
        raise SystemExit(f"The baseline ({base_path.name}) used a different dataset, split or batch. "
                         "Re-run the baseline first, otherwise the comparison is not valid.")

    embedder = Embedder(args.model)
    n_chunks = build_variant(args.name, docs, embedder, args.chunk_target, args.chunk_overlap,
                             args.min_chunk_words, args.embed_text)
    reranker, rerank_model = None, None
    if args.rerank:
        from src.rag.retrieve import DEFAULT_RERANKER, load_reranker
        rerank_model = DEFAULT_RERANKER if args.rerank == "default" else args.rerank
        reranker = load_reranker(rerank_model)
    rows, summary = run_variant(selected, embedder, args.name, args.k, hybrid=args.hybrid,
                                reranker=reranker, candidates=args.candidates)
    print(format_report(summary, rows, args.split, args.k))

    cmp_summary, detail = compare_rows(base_record["rows"], rows)
    print(format_comparison(cmp_summary, detail, base_record["label"], args.name))

    settings = {"embed_model": args.model, "chunk_target_words": args.chunk_target,
                "chunk_overlap_words": args.chunk_overlap, "min_chunk_words": args.min_chunk_words,
                "embed_text": args.embed_text, "n_chunks": n_chunks, "hybrid": args.hybrid,
                "reranker": rerank_model, "candidates": args.candidates if (args.hybrid or rerank_model) else None}
    record = {"label": args.name, "change": args.change, "created": datetime.now().isoformat(timespec="seconds"),
              "git_commit": git_commit(), "dataset": fingerprint, "split": args.split,
              "batch": args.batch, "k": args.k, "settings": settings, "dataset_summary": summarise(selected), "summary": summary,
              "compared_with": base_path.name, "comparison": {k_: v for k_, v in cmp_summary.items()}, "rows": rows}
    out = save_run(record)
    print(f"\nSaved: {out}")
    print("\nRow for docs/experiments.md:")
    print(markdown_row(record, base_record["label"]))


if __name__ == "__main__":
    main()
