"""Explain which suspected glued words the repair step fixed, and why it skipped the rest.

    python -m src.ingest.glue_report                       # reads data/processed/sosort-2016.json
    python -m src.ingest.glue_report --id sosort-2016 --all
    python -m src.ingest.glue_report --chars      # invisible or unusual characters in the text
    python -m src.ingest.glue_report --rare       # long non-dictionary words used once or twice
    python -m src.ingest.glue_report --camel      # words with a capital in the middle ("theCobb")

It lists words that are not ordinary English but can be cut into words the
document uses often (for example "theCobb"), with the reason each one was or
was not repaired. Run it on already-processed data: a word listed as
"would be repaired" means the repair step missed something it should have caught.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from src.ingest.repair import (FUNCTION_WORDS, MAX_WHOLE_FREQ, RARITY_RATIO, SHORT_WORD,
                               WORD, _segment, build_vocab, default_is_known)


def explain(lower, original, vocab, is_known):
    """Return (reason, parts) for a suspicious word, or None if it cannot be cut into known words."""
    segmented = _segment(lower, vocab, depth=2)
    if segmented is None:
        return None
    parts, rarest = segmented
    if is_known(lower):
        return "ordinary English word", parts
    if original.isupper():
        return "all capitals (acronym)", parts
    if vocab[lower] > MAX_WHOLE_FREQ:
        return f"appears more than {MAX_WHOLE_FREQ} times", parts
    if vocab[lower] * RARITY_RATIO > rarest:
        return "about as common as its rarest part", parts
    if len(original) < SHORT_WORD and not all(p in FUNCTION_WORDS for p in parts):
        return "short word, not made of function words", parts
    return "would be repaired", parts


def suspects(sections, is_known=default_is_known, show_all=False):
    """Rows describing every distinct word that can be cut into known parts."""
    vocab = build_vocab(sections)
    seen, rows = set(), []
    for sec in sections:
        for text in [sec["heading"], *sec["paragraphs"]]:
            for original in WORD.findall(text):
                lower = original.lower()
                if lower in seen:
                    continue
                seen.add(lower)
                result = explain(lower, original, vocab, is_known)
                if result is None:
                    continue
                reason, parts = result
                if reason == "ordinary English word" and not show_all:
                    continue
                rows.append({"word": original, "count": vocab[lower], "parts": parts,
                             "part_counts": [vocab[p] for p in parts], "reason": reason})
    return sorted(rows, key=lambda r: (-r["count"], r["word"]))


def unusual_characters(sections):
    """Count every character that is not plain printable ASCII: [(char, name, count), ...]."""
    counts = Counter()
    for sec in sections:
        for text in [sec["heading"], *sec["paragraphs"]]:
            counts.update(ch for ch in text if ord(ch) > 126 or ord(ch) < 32)
    return [(ch, unicodedata.name(ch, "UNNAMED"), n) for ch, n in counts.most_common()]


def rare_unknown_words(sections, is_known=default_is_known, min_len=8, max_count=2, context=28):
    """Long words that are not ordinary English and are used rarely, with a snippet of context.

    Glued words that the repair step could not split often appear here, because
    the words they are made of are too rare in the document to trust.
    """
    vocab = build_vocab(sections)
    rows, seen = [], set()
    for sec in sections:
        for text in [sec["heading"], *sec["paragraphs"]]:
            for m in WORD.finditer(text):
                word, lower = m.group(0), m.group(0).lower()
                if (lower in seen or len(word) < min_len or word.isupper()
                        or vocab[lower] > max_count or is_known(lower)):
                    continue
                seen.add(lower)
                snippet = text[max(0, m.start() - context):m.end() + context]
                rows.append({"word": word, "count": vocab[lower], "context": snippet})
    return sorted(rows, key=lambda r: (-len(r["word"]), r["word"]))


def camel_tokens(sections, context=28):
    """Words where a lower-case letter is followed by a capital, with a snippet of context.

    After a good repair, what remains here should be real names (PubMed, ScoliScore),
    not glued sentences.
    """
    rows, seen = [], set()
    for sec in sections:
        for text in [sec["heading"], *sec["paragraphs"]]:
            for m in re.finditer(r"[A-Za-z]*[a-z][A-Z][A-Za-z]*", text):
                token = m.group(0)
                if token in seen:
                    continue
                seen.add(token)
                snippet = text[max(0, m.start() - context):m.end() + context]
                rows.append({"word": token, "context": snippet})
    return sorted(rows, key=lambda r: r["word"].lower())


def main():
    parser = argparse.ArgumentParser(description="Report suspected glued words")
    parser.add_argument("--id", default="sosort-2016")
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--all", action="store_true", help="also list ordinary English words")
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--chars", action="store_true", help="list unusual or invisible characters")
    parser.add_argument("--rare", action="store_true", help="list long rare non-dictionary words")
    parser.add_argument("--camel", action="store_true", help="list words with a capital in the middle")
    args = parser.parse_args()

    doc = json.loads((Path(args.processed_dir) / f"{args.id}.json").read_text(encoding="utf-8"))
    if args.chars:
        print(f"Unusual characters in {args.id}:")
        for ch, name, n in unusual_characters(doc["sections"]):
            print(f"    U+{ord(ch):04X}  {name:40} x{n}")
        return
    if args.camel:
        rows = camel_tokens(doc["sections"])
        print(f"Words with a capital in the middle in {args.id}: {len(rows)} (showing {min(len(rows), args.limit)})")
        for r in rows[:args.limit]:
            print(f"  {r['word']!r}  ...{r['context']!r}...")
        return
    if args.rare:
        rows = rare_unknown_words(doc["sections"])
        print(f"Long rare non-dictionary words in {args.id}: {len(rows)} (showing {min(len(rows), args.limit)})")
        for r in rows[:args.limit]:
            print(f"  {r['word']!r} x{r['count']}  ...{r['context']!r}...")
        return
    print(f"Repairs already applied to {args.id}: {len(doc.get('repairs', []))}")
    for r in doc.get("repairs", []):
        print(f"    {r['from']!r} -> {r['to']!r}  (x{r['count']})")

    rows = suspects(doc["sections"], show_all=args.all)
    print(f"\nSuspected glued words still in the text: {len(rows)} (showing {min(len(rows), args.limit)})")
    print(f"{'word':28} {'count':>5}  {'parts (counts)':32} reason")
    for r in rows[:args.limit]:
        parts = " + ".join(f"{p}({n})" for p, n in zip(r["parts"], r["part_counts"]))
        print(f"{r['word']:28} {r['count']:>5}  {parts:32} {r['reason']}")


if __name__ == "__main__":
    main()
