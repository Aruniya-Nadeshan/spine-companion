"""Run the whole ingestion pipeline.

    python -m src.ingest.run_ingest              # download, extract, clean, check
    python -m src.ingest.run_ingest --skip-fetch # reuse files already in data/raw

Policy: stop at the first failure so we never build on a half-empty corpus.
"""
import argparse
import json
from pathlib import Path

from src.ingest.clean import clean_sections
from src.ingest.extract import extract_document
from src.ingest.fetch import fetch_source, raw_path as get_raw_path
from src.ingest.load_sources import DEFAULT_PATH, load_ingest_sources, write_date_accessed
from src.ingest.quality import check_quality, count_chars
from src.ingest.repair import repair_sections


class IngestError(Exception):
    """Raised when a document fails the quality check."""


def process_source(source, raw_dir, processed_dir, skip_fetch):
    """Fetch (optional), extract, clean, check and save one document."""
    if skip_fetch:
        raw_path = get_raw_path(source, raw_dir)
        if not raw_path.exists():
            raise IngestError(f"--skip-fetch used but {raw_path} does not exist")
        accessed = source["date_accessed"]
    else:
        raw_path, accessed = fetch_source(source, raw_dir)

    raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
    extracted = extract_document(raw_text, source["format"])
    sections = clean_sections(extracted["sections"])
    sections, repairs = repair_sections(sections)

    problems = check_quality(sections)
    if problems:
        raise IngestError(f"'{source['id']}' failed quality check: {'; '.join(problems)}")

    doc = {
        "id": source["id"],
        "title": source["title"],
        "publisher": source["publisher"],
        "url": source["url"],
        "licence": source["licence"],
        "attribution": source["attribution"],
        "date_accessed": accessed,
        "n_chars": count_chars(sections),
        "repairs": repairs,  # glued words that were split; review them with --show-repairs
        "sections": sections,
    }
    out = Path(processed_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{source['id']}.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return doc


def main():
    parser = argparse.ArgumentParser(description="Ingest sources listed in sources.csv")
    parser.add_argument("--sources", default=DEFAULT_PATH)
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--only", help="ingest just this source id")
    parser.add_argument("--show-repairs", action="store_true",
                        help="print every glued-word repair so it can be reviewed")
    args = parser.parse_args()

    sources = load_ingest_sources(args.sources)
    if args.only:
        sources = [s for s in sources if s["id"] == args.only]
        if not sources:
            raise SystemExit(f"No ingest source with id '{args.only}'")
    print(f"Ingesting {len(sources)} source(s)...\n")

    dates = {}
    print(f"{'id':38} {'sections':>8} {'chars':>8} {'repairs':>8}")
    for source in sources:
        doc = process_source(source, args.raw_dir, args.processed_dir, args.skip_fetch)
        dates[doc["id"]] = doc["date_accessed"]
        print(f"{doc['id']:38} {len(doc['sections']):>8} {doc['n_chars']:>8} {len(doc['repairs']):>8}")
        if args.show_repairs:
            for r in doc["repairs"]:
                print(f"    {r['from']!r} -> {r['to']!r}  (x{r['count']})")

    if not args.skip_fetch:
        write_date_accessed(dates, args.sources)
    print("\nAll sources passed the quality check.")


if __name__ == "__main__":
    main()
