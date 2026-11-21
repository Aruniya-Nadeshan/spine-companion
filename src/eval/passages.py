"""Browse the processed corpus to find phrases for evaluation labels.

    python -m src.eval.passages                                  # list sources and sections
    python -m src.eval.passages --source niams-scoliosis-overview
    python -m src.eval.passages --source sosort-2016 --section 20
    python -m src.eval.passages --find "brace"                   # where does a word appear?

Copy evidence phrases from here, so they match the text exactly.
"""
import argparse

from src.rag.chunk import load_processed_docs
from src.rag.config import PROCESSED_DIR


def find_text(docs, needle, context=60, limit=25):
    """Return (source_id, section_index, heading, snippet) for each match of `needle`."""
    needle_low = needle.lower()
    matches = []
    for doc in docs:
        for s_idx, section in enumerate(doc["sections"]):
            for paragraph in section["paragraphs"]:
                pos = paragraph.lower().find(needle_low)
                if pos >= 0:
                    snippet = paragraph[max(0, pos - context):pos + len(needle) + context]
                    matches.append((doc["id"], s_idx, section["heading"], snippet))
                    if len(matches) >= limit:
                        return matches
    return matches


def main():
    parser = argparse.ArgumentParser(description="Browse the processed corpus")
    parser.add_argument("--source")
    parser.add_argument("--section", type=int)
    parser.add_argument("--find")
    parser.add_argument("--processed-dir", default=PROCESSED_DIR)
    args = parser.parse_args()
    docs = load_processed_docs(args.processed_dir)

    if args.find:
        for source_id, s_idx, heading, snippet in find_text(docs, args.find):
            print(f"{source_id}  section {s_idx}  >  {heading[:70]}\n    ...{snippet}...\n")
        return
    if not args.source:
        for doc in docs:
            print(f"{doc['id']:40} {len(doc['sections']):>3} sections")
        return
    doc = next((d for d in docs if d["id"] == args.source), None)
    if doc is None:
        raise SystemExit(f"Unknown source '{args.source}'. Known: {[d['id'] for d in docs]}")
    if args.section is None:
        for s_idx, section in enumerate(doc["sections"]):
            words = sum(len(p.split()) for p in section["paragraphs"])
            print(f"{s_idx:>3}  {words:>5} words  {section['heading'][:90]}")
        return
    section = doc["sections"][args.section]
    print(f"[{args.source} section {args.section}] {section['heading']}\n")
    for paragraph in section["paragraphs"]:
        print(paragraph + "\n")


if __name__ == "__main__":
    main()
