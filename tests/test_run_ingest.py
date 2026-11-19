import json

import pytest

from src.ingest.run_ingest import IngestError, process_source

SOURCE = {"id": "demo", "title": "Demo", "publisher": "Pub", "url": "https://example.org/demo",
          "fetch_url": "https://example.org/demo", "format": "html",
          "date_accessed": "2026-11-19", "licence": "CC BY 4.0", "attribution": "Credit demo",
          "v1_use": "ingest", "notes": ""}


def long_page(n_sections=3):
    body = "".join(f"<h2>Section {i}</h2><p>{'Scoliosis text. ' * 80}</p>" for i in range(n_sections))
    return f"<html><head><title>Demo</title></head><body><main>{body}</main></body></html>"


def test_process_source_writes_json_with_attribution(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "processed"
    raw.mkdir()
    (raw / "demo.html").write_text(long_page(), encoding="utf-8")
    doc = process_source(SOURCE, raw, out, skip_fetch=True)
    saved = json.loads((out / "demo.json").read_text(encoding="utf-8"))
    assert saved["attribution"] == "Credit demo"
    assert saved["licence"] == "CC BY 4.0"
    assert saved["date_accessed"] == "2026-11-19"
    assert len(saved["sections"]) == 3
    assert doc["n_chars"] == saved["n_chars"] > 2000


def test_empty_extraction_stops_the_run_and_writes_nothing(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "processed"
    raw.mkdir()
    (raw / "demo.html").write_text("<html><body><main></main></body></html>", encoding="utf-8")
    with pytest.raises(IngestError, match="quality check"):
        process_source(SOURCE, raw, out, skip_fetch=True)
    assert not (out / "demo.json").exists()


def test_skip_fetch_without_raw_file_fails(tmp_path):
    with pytest.raises(IngestError, match="does not exist"):
        process_source(SOURCE, tmp_path / "raw", tmp_path / "out", skip_fetch=True)


def jats_article(n_sections=3):
    secs = "".join(
        f"<sec><title>Topic {i}</title><p>{'Bracing guidance. ' * 80}<xref ref-type=\"bibr\" rid=\"r{i}\">[{i}]</xref></p></sec>"
        for i in range(n_sections))
    return ("<article><front><article-meta><title-group><article-title>Demo guidelines</article-title>"
            "</title-group></article-meta></front><body>" + secs + "</body></article>")


def test_process_source_handles_jats_xml(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "processed"
    raw.mkdir()
    xml_source = dict(SOURCE, format="jats-xml")
    (raw / "demo.xml").write_text(jats_article(), encoding="utf-8")
    process_source(xml_source, raw, out, skip_fetch=True)
    saved = json.loads((out / "demo.json").read_text(encoding="utf-8"))
    assert [s["heading"] for s in saved["sections"]] == ["Topic 0", "Topic 1", "Topic 2"]
    assert "[1]" not in saved["sections"][1]["paragraphs"][0]
