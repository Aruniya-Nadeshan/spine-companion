"""Measure how well retrieval finds the passage that answers each question.

    python -m src.eval.retrieval_eval --label baseline            # dev split (default)
    python -m src.eval.retrieval_eval --label baseline --split all
    python -m src.eval.retrieval_eval --label final --split test  # only for a finished design

Metrics (in-scope questions only):
    hit@k  share of questions where a correct chunk is in the top k results
    MRR    mean of 1/rank of the first correct chunk (0 if none in the top k)
A chunk is correct if it comes from an evidence source AND contains its evidence phrase.

The run is saved to data/eval/runs/ with the settings, dataset fingerprint and git
commit, so every number can be traced back to what produced it.
"""
import argparse
import json
import statistics
import subprocess
from datetime import datetime
from pathlib import Path

from src.eval.schema import (DEFAULT_PATH, assign_split, dataset_fingerprint, load_questions,
                             normalise, summarise, validate_questions)

KS = (1, 3, 5)
RUNS_DIR = "data/eval/runs"


# ---------------------------------------------------------------- matching and metrics

def is_hit(hit, evidence):
    """True if this retrieved chunk is from an evidence source and contains its phrase."""
    text = normalise(hit["text"])
    source = hit["metadata"]["source_id"]
    return any(source == ev["source_id"] and normalise(ev["contains"]) in text for ev in evidence)


def first_relevant_rank(hits, evidence):
    """1-based rank of the first correct chunk, or None if there is none."""
    for rank, hit in enumerate(hits, start=1):
        if is_hit(hit, evidence):
            return rank
    return None


def wilson_interval(successes, n, z=1.96):
    """95% confidence interval for a proportion. Small samples give wide intervals."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def evaluate_retrieval(questions, search_fn, k=5):
    """Run every question through search and score the in-scope ones.

    search_fn(question_text, k) must return hits: {"text", "score", "metadata"}.
    """
    rows = []
    for q in questions:
        hits = search_fn(q["question"], k)
        rank = first_relevant_rank(hits, q["evidence"]) if q["category"] == "in_scope" else None
        rows.append({
            "id": q["id"], "category": q["category"], "subtype": q["subtype"],
            "rank": rank,
            "top_score": hits[0]["score"] if hits else None,
            "top_sources": [h["metadata"]["source_id"] for h in hits[:3]],
            "top_headings": [h["metadata"]["heading"][:80] for h in hits[:3]],
        })
    in_scope = [r for r in rows if r["category"] == "in_scope"]
    n = len(in_scope)
    summary = {"n_in_scope": n}
    for k_ in KS:
        if k_ <= k:
            hits_k = sum(1 for r in in_scope if r["rank"] is not None and r["rank"] <= k_)
            low, high = wilson_interval(hits_k, n)
            summary[f"hit@{k_}"] = {"value": hits_k / n if n else 0.0, "ci95": [low, high], "hits": hits_k}
    summary["mrr"] = (sum(1 / r["rank"] for r in in_scope if r["rank"]) / n) if n else 0.0
    by_subtype = {}
    for r in in_scope:
        entry = by_subtype.setdefault(r["subtype"], {"n": 0, "hits": 0})
        entry["n"] += 1
        entry["hits"] += int(r["rank"] is not None)
    summary["by_subtype"] = by_subtype
    return rows, summary


def score_distribution(rows):
    """Top-1 similarity per category/subtype: do in-scope and off-topic questions separate?"""
    groups = {}
    for r in rows:
        if r["top_score"] is not None:
            groups.setdefault(f"{r['category']}/{r['subtype']}", []).append(r["top_score"])
    return {name: {"n": len(v), "mean": statistics.mean(v), "median": statistics.median(v),
                   "min": min(v), "max": max(v)} for name, v in sorted(groups.items())}


def suggest_threshold(rows):
    """Best top-1 score cut-off for answering versus saying 'I don't know'.

    Compares in-scope questions (should be answered, so score >= threshold) with
    off-topic ones (should be declined, so score < threshold). Returns None if either
    group is empty. Personalised-advice and medication questions are about scoliosis,
    so a score cannot separate them; they need a different mechanism (Phase 5).
    """
    answer = [r["top_score"] for r in rows if r["category"] == "in_scope" and r["top_score"] is not None]
    decline = [r["top_score"] for r in rows if r["subtype"] == "off_topic" and r["top_score"] is not None]
    if not answer or not decline:
        return None
    best = None
    for t in sorted(set(answer + decline)):
        keep = sum(s >= t for s in answer) / len(answer)
        reject = sum(s < t for s in decline) / len(decline)
        balanced = (keep + reject) / 2
        if best is None or balanced > best["balanced_accuracy"]:
            best = {"threshold": t, "answered_in_scope": keep, "declined_off_topic": reject,
                    "balanced_accuracy": balanced}
    best["n_in_scope"], best["n_off_topic"] = len(answer), len(decline)
    return best


# ---------------------------------------------------------------- reporting and saving

def format_report(summary, rows, split, k):
    n = summary["n_in_scope"]
    lines = [f"\nRetrieval evaluation  (split={split}, {n} in-scope questions, k={k})", ""]
    for k_ in KS:
        key = f"hit@{k_}"
        if key in summary:
            s = summary[key]
            lines.append(f"  {key:7} {s['value']:.3f}   95% CI {s['ci95'][0]:.2f}-{s['ci95'][1]:.2f}   ({s['hits']}/{n})")
    lines.append(f"  {'MRR':7} {summary['mrr']:.3f}")
    if n < 30:
        lines.append(f"\n  Note: with only {n} questions these numbers are very uncertain (see the CI).")
    lines += ["", "  By subtype (hit@k):"]
    for name, e in sorted(summary["by_subtype"].items()):
        lines.append(f"    {name:12} {e['hits']}/{e['n']}")
    misses = [r for r in rows if r["category"] == "in_scope" and r["rank"] is None]
    if misses:
        lines += ["", f"  Misses ({len(misses)}): correct passage not in the top {k}"]
        for r in misses:
            lines.append(f"    {r['id']}: top results were {r['top_sources'][0] if r['top_sources'] else '-'} > "
                         f"{r['top_headings'][0] if r['top_headings'] else '-'}")
    return "\n".join(lines)


def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def save_run(record, runs_dir=RUNS_DIR):
    path = Path(runs_dir)
    path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = path / f"{stamp}-{record['label']}.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def select_split(questions, split):
    return questions if split == "all" else [q for q in questions if assign_split(q["id"]) == split]


def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval against the question set")
    parser.add_argument("--label", required=True, help="short name for this run, e.g. baseline")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--questions", default=DEFAULT_PATH)
    args = parser.parse_args()

    from src.rag import config
    from src.rag.chunk import load_processed_docs
    from src.rag.embed import Embedder
    from src.rag.index import open_collection
    from src.rag.search import search

    questions = load_questions(args.questions)
    errors, warnings = validate_questions(questions, load_processed_docs(config.PROCESSED_DIR))
    for w in warnings:
        print("warning:", w)
    if errors:
        print("\nThe question file has errors, so the evaluation was not run:")
        for e in errors:
            print("  -", e)
        raise SystemExit(1)

    if args.split == "test":
        print("Running on the TEST split. Use it only to report a finished design, never to tune.")
    selected = select_split(questions, args.split)
    embedder = Embedder()
    rows, summary = evaluate_retrieval(selected, lambda text, k: search(text, embedder, k=k), k=args.k)
    print(format_report(summary, rows, args.split, args.k))

    dist = score_distribution(rows)
    print("\n  Top-1 similarity by question type (mean / min / max):")
    for name, d in dist.items():
        print(f"    {name:28} n={d['n']:<3} {d['mean']:.3f} / {d['min']:.3f} / {d['max']:.3f}")
    threshold = suggest_threshold(rows)
    if threshold:
        print(f"\n  Suggested 'I don't know' cut-off: {threshold['threshold']:.3f}  "
              f"(answers {threshold['answered_in_scope']:.0%} of in-scope, declines "
              f"{threshold['declined_off_topic']:.0%} of off-topic)")

    record = {
        "label": args.label, "created": datetime.now().isoformat(timespec="seconds"),
        "git_commit": git_commit(), "dataset": dataset_fingerprint(args.questions),
        "split": args.split, "k": args.k,
        "settings": {"embed_model": config.EMBED_MODEL, "chunk_target_words": config.CHUNK_TARGET_WORDS,
                     "chunk_overlap_words": config.CHUNK_OVERLAP_WORDS, "min_chunk_words": config.MIN_CHUNK_WORDS,
                     "n_chunks": open_collection(config.INDEX_DIR, config.COLLECTION).count()},
        "dataset_summary": summarise(selected), "summary": summary,
        "score_distribution": dist, "suggested_threshold": threshold, "rows": rows,
    }
    print(f"\nSaved: {save_run(record)}")


if __name__ == "__main__":
    main()
