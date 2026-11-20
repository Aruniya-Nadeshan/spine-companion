"""Quick sanity check that retrieval finds the right source for a few obvious questions.

    python -m src.rag.smoke

This is NOT the evaluation (Phase 3 builds a proper question set with metrics).
It only catches gross failures, such as an empty or broken index.
"""
from src.rag.config import TOP_K

# (question, set of source ids where a good answer should come from)
SMOKE_QUESTIONS = [
    ("What are the symptoms of scoliosis in teens?", {"niams-scoliosis-overview"}),
    ("What causes scoliosis?", {"niams-scoliosis-overview"}),
    ("Who is more likely to get idiopathic scoliosis?", {"niams-scoliosis-overview"}),
    ("How do doctors diagnose scoliosis?", {"niams-scoliosis-diagnosis-treatment"}),
    ("When is a brace needed?", {"niams-scoliosis-diagnosis-treatment", "sosort-2016"}),
    ("How is bracing used for idiopathic scoliosis during growth?", {"sosort-2016"}),
]


def run_smoke(search_fn, questions=SMOKE_QUESTIONS, k=TOP_K):
    """Return a list of (question, passed, top_source) using any search function."""
    results = []
    for question, expected in questions:
        hits = search_fn(question, k)
        found = {h["metadata"]["source_id"] for h in hits}
        top = hits[0]["metadata"]["source_id"] if hits else None
        results.append((question, bool(found & expected), top))
    return results


def main():
    from src.rag.embed import Embedder
    from src.rag.search import search

    embedder = Embedder()
    results = run_smoke(lambda q, k: search(q, embedder, k=k))
    for question, passed, top in results:
        print(f"{'PASS' if passed else 'FAIL'}  {question}  (top hit: {top})")
    n_pass = sum(1 for _, passed, _ in results if passed)
    print(f"\n{n_pass}/{len(results)} passed")


if __name__ == "__main__":
    main()
