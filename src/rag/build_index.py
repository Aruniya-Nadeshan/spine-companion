"""Chunk the processed documents, embed them and build the search index.

    python -m src.rag.build_index
"""
import argparse
import statistics
from collections import Counter

from src.rag.chunk import chunk_all, load_processed_docs
from src.rag.config import (CHUNK_OVERLAP_WORDS, CHUNK_TARGET_WORDS, INDEX_DIR,
                            MAX_WARN_WORDS, PROCESSED_DIR)
from src.rag.index import build_index


def summarise(chunks):
    """Print how many chunks each source produced and how big they are."""
    per_source = Counter(c.source_id for c in chunks)
    words = [c.n_words for c in chunks]
    print(f"\n{'source':40} {'chunks':>6}")
    for source_id, n in per_source.items():
        print(f"{source_id:40} {n:>6}")
    print(f"\nTotal chunks: {len(chunks)}")
    print(f"Words per chunk: min {min(words)}, median {int(statistics.median(words))}, max {max(words)}")
    too_big = [c for c in chunks if c.n_words > MAX_WARN_WORDS]
    if too_big:
        print(f"WARNING: {len(too_big)} chunk(s) over {MAX_WARN_WORDS} words, e.g. {too_big[0].id}")


def main():
    parser = argparse.ArgumentParser(description="Build the scoliosis search index")
    parser.add_argument("--processed-dir", default=PROCESSED_DIR)
    parser.add_argument("--index-dir", default=INDEX_DIR)
    args = parser.parse_args()

    docs = load_processed_docs(args.processed_dir)
    chunks = chunk_all(docs, CHUNK_TARGET_WORDS, CHUNK_OVERLAP_WORDS)
    summarise(chunks)

    from src.rag.embed import Embedder
    print("\nLoading the embedding model (the first run downloads it)...")
    build_index(chunks, Embedder(), index_dir=args.index_dir)
    print(f"Index built in {args.index_dir}")


if __name__ == "__main__":
    main()
