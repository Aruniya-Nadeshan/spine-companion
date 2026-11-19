import csv

import pytest

from src.ingest.load_sources import (
    load_all_sources, load_ingest_sources, write_date_accessed)

COLUMNS = ["id", "title", "publisher", "url", "fetch_url", "format", "date_accessed",
           "licence", "attribution", "v1_use", "notes"]


def make_csv(tmp_path, rows, columns=COLUMNS):
    path = tmp_path / "sources.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


def row(id, v1_use="ingest", **overrides):
    base = {"id": id, "title": f"Title {id}", "publisher": "Pub",
            "url": f"https://example.org/{id}", "fetch_url": "", "format": "",
            "date_accessed": "",
            "licence": "CC BY 4.0", "attribution": "Credit", "v1_use": v1_use,
            "notes": ""}
    base.update(overrides)
    return base


def test_returns_only_ingest_rows(tmp_path):
    path = make_csv(tmp_path, [row("a"), row("b", "link-only"), row("c", "deferred"), row("d")])
    ids = [r["id"] for r in load_ingest_sources(path)]
    assert ids == ["a", "d"]


def test_ingest_row_with_blank_licence_is_rejected(tmp_path):
    path = make_csv(tmp_path, [row("a", licence="")])
    with pytest.raises(ValueError, match="blank"):
        load_ingest_sources(path)


def test_blank_fields_allowed_for_non_ingest_rows(tmp_path):
    path = make_csv(tmp_path, [row("a"), row("b", "deferred", url="", attribution="")])
    assert [r["id"] for r in load_ingest_sources(path)] == ["a"]


def test_missing_column_is_rejected(tmp_path):
    path = make_csv(tmp_path, [], columns=["id", "title"])
    with pytest.raises(ValueError, match="missing columns"):
        load_all_sources(path)


def test_write_date_accessed_updates_only_named_rows(tmp_path):
    path = make_csv(tmp_path, [row("a"), row("b")])
    write_date_accessed({"a": "2026-11-19"}, path)
    rows = {r["id"]: r for r in load_all_sources(path)}
    assert rows["a"]["date_accessed"] == "2026-11-19"
    assert rows["b"]["date_accessed"] == ""


def test_fetch_url_and_format_have_defaults(tmp_path):
    path = make_csv(tmp_path, [row("a")])
    (src,) = load_ingest_sources(path)
    assert src["fetch_url"] == "https://example.org/a"
    assert src["format"] == "html"


def test_explicit_fetch_url_and_format_are_kept(tmp_path):
    path = make_csv(tmp_path, [row("a", fetch_url="https://api.example.org/a.xml", format="jats-xml")])
    (src,) = load_ingest_sources(path)
    assert src["fetch_url"] == "https://api.example.org/a.xml"
    assert src["format"] == "jats-xml"


def test_unknown_format_is_rejected(tmp_path):
    path = make_csv(tmp_path, [row("a", format="pdf")])
    with pytest.raises(ValueError, match="unknown format"):
        load_ingest_sources(path)
