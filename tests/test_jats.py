from src.ingest.extract import extract_document, extract_jats

JATS = """<?xml version="1.0"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front><article-meta>
    <title-group><article-title>2016 SOSORT <italic>guidelines</italic></article-title></title-group>
    <abstract><sec><title>Background</title><p>Braces are used for scoliosis.</p></sec></abstract>
  </article-meta></front>
  <body>
    <sec><title>Bracing</title>
      <p>Bracing is recommended in growing patients<xref ref-type="bibr" rid="B1">[1]</xref>, see <xref ref-type="fig" rid="F1">Fig. 1</xref>.</p>
      <fig id="F1"><caption><p>Figure caption that must be dropped.</p></caption></fig>
      <list><list-item><p>Wear it as prescribed</p></list-item></list>
      <sec><title>Indications</title><p>Curves between 20 and 40 degrees.</p></sec>
    </sec>
    <sec><title>References</title><p>Should be excluded.</p></sec>
  </body>
  <back><ref-list><ref><mixed-citation>Citation text</mixed-citation></ref></ref-list></back>
</article>"""


def test_title_and_abstract_are_extracted():
    doc = extract_jats(JATS)
    assert doc["title"] == "2016 SOSORT guidelines"
    assert doc["sections"][0]["heading"] == "Abstract > Background"


def test_nested_sections_get_a_trail_heading():
    headings = [s["heading"] for s in extract_jats(JATS)["sections"]]
    assert headings == ["Abstract > Background", "Bracing", "Bracing > Indications"]


def test_citation_markers_figures_and_references_are_removed():
    doc = extract_jats(JATS)
    text = " ".join(p for s in doc["sections"] for p in s["paragraphs"])
    assert "[1]" not in text
    assert "Figure caption" not in text
    assert "Citation text" not in text
    assert "Should be excluded" not in text
    assert "Fig. 1" in text  # figure cross-references in prose are kept


def test_list_items_are_included():
    bracing = extract_jats(JATS)["sections"][1]["paragraphs"]
    assert "Wear it as prescribed" in bracing


def test_extract_document_dispatches_by_format():
    assert extract_document(JATS, "jats-xml")["title"].startswith("2016 SOSORT")
    html_doc = extract_document("<html><head><title>T</title></head><body><main><p>x</p></main></body></html>", "html")
    assert html_doc["title"] == "T"
