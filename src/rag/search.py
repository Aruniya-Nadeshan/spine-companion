"""Retrieve the most relevant chunks for a question.

    python -m src.rag.search "what is a Cobb angle"
    python -m src.rag.search "when is a brace needed" --k 3
"""
import argparse

from src.rag.config import COLLECTION, INDEX_DIR, TOP_K
from src.rag.index import open_collection


def search(query, embedder, k=TOP_K, index_dir=INDEX_DIR, collection=COLLECTION):
    """Return up to k hits, best first: {"text", "score", "metadata"}.

    score is cosine similarity (1.0 = identical meaning, higher is better).
    """
    if not query.strip():
        raise ValueError("Query is empty")
    col = open_collection(index_dir, collection)
    result = col.query(
        query_embeddings=[embedder.embed_query(query)],
        n_results=min(k, col.count()),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"text": doc, "score": 1.0 - dist, "metadata": meta}
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0])
    ]


def format_hit(rank, hit, width=300):
    m = hit["metadata"]
    preview = " ".join(hit["text"].split())
    if len(preview) > width:
        preview = preview[:width].rstrip() + "..."
    return (f"[{rank}] score {hit['score']:.3f}  {m['source_id']}  >  {m['heading']}\n"
            f"    {preview}\n"
            f"    Source: {m['attribution']}")


def main():
    parser = argparse.ArgumentParser(description="Search the scoliosis index")
    parser.add_argument("query")
    parser.add_argument("--k", type=int, default=TOP_K)
    args = parser.parse_args()

    from src.rag.embed import Embedder
    hits = search(args.query, Embedder(), k=args.k)
    print(f"\nQuestion: {args.query}\n")
    for rank, hit in enumerate(hits, start=1):
        print(format_hit(rank, hit))
        print()


if __name__ == "__main__":
    main()
