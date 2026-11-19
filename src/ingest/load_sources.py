"""Read the source log (data/sources.csv).

The CSV is the single source of truth for what may enter the index.
Only rows marked v1_use == "ingest" are returned, and each of those must
carry a URL, a licence and attribution text (see docs/scope.md, section 7).
"""
import csv
from pathlib import Path

DEFAULT_PATH = "data/sources.csv"

REQUIRED_COLUMNS = {
    "id", "title", "publisher", "url", "fetch_url", "format", "date_accessed",
    "licence", "attribution", "v1_use", "notes",
}
# "html" = a web page; "jats-xml" = article XML from an official API.
VALID_FORMATS = {"html", "jats-xml"}
# Fields an ingest row must not leave blank.
REQUIRED_FOR_INGEST = ("id", "title", "url", "licence", "attribution")


def load_all_sources(path=DEFAULT_PATH):
    """Return every row of the CSV as a list of dicts."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        return list(reader)


def load_ingest_sources(path=DEFAULT_PATH):
    """Return only rows with v1_use == 'ingest', validated."""
    rows = load_all_sources(path)
    ingest = [r for r in rows if r["v1_use"].strip().lower() == "ingest"]
    for row in ingest:
        blanks = [c for c in REQUIRED_FOR_INGEST if not row[c].strip()]
        if blanks:
            raise ValueError(
                f"Source '{row['id']}' is marked ingest but has blank: {blanks}"
            )
        # Defaults: download from the public URL, and treat it as HTML.
        row["fetch_url"] = row["fetch_url"].strip() or row["url"]
        row["format"] = row["format"].strip().lower() or "html"
        if row["format"] not in VALID_FORMATS:
            raise ValueError(
                f"Source '{row['id']}' has unknown format '{row['format']}' "
                f"(expected one of {sorted(VALID_FORMATS)})"
            )
    return ingest


def write_date_accessed(updates, path=DEFAULT_PATH):
    """Set date_accessed for the given {source_id: 'YYYY-MM-DD'} and save."""
    path = Path(path)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    for row in rows:
        if row["id"] in updates:
            row["date_accessed"] = updates[row["id"]]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
