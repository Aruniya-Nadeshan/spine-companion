from src.ingest.clean import clean_sections, clean_text
from src.ingest.extract import extract_html
from src.ingest.quality import check_quality

SAMPLE = """
<html><head><title>Overview of Scoliosis</title><script>var x=1;</script></head>
<body>
  <nav><li>Menu item that must disappear</li></nav>
  <main>
    <h1>Overview of Scoliosis</h1>
    <p>Scoliosis is a sideways curve of the spine.</p>
    <h2>Symptoms</h2>
    <p>Most people with mild scoliosis have <em>no</em> symptoms .</p>
    <ul><li><p>Uneven shoulders</p></li><li>Uneven waist</li></ul>
    <h2>References</h2>
    <ol><li>Smith J. A citation that must be dropped.</li></ol>
  </main>
  <footer>Footer text that must disappear</footer>
</body></html>
"""


def test_extract_splits_sections_and_removes_noise():
    doc = extract_html(SAMPLE)
    headings = [s["heading"] for s in doc["sections"]]
    all_text = " ".join(p for s in doc["sections"] for p in s["paragraphs"])
    assert doc["title"] == "Overview of Scoliosis"
    assert headings == ["Overview of Scoliosis", "Symptoms"]
    assert "Menu item" not in all_text
    assert "Footer text" not in all_text
    assert "citation" not in all_text


def test_nested_list_paragraph_is_not_duplicated():
    doc = extract_html(SAMPLE)
    symptoms = doc["sections"][1]["paragraphs"]
    assert symptoms.count("Uneven shoulders") == 1
    assert "Uneven waist" in symptoms


def test_clean_text_fixes_spacing_and_unicode():
    assert clean_text("no  symptoms\u00a0 .") == "no symptoms."
    assert clean_text("( see below )") == "(see below)"


def test_clean_sections_drops_empty_paragraphs():
    sections = [{"heading": " Intro ", "paragraphs": ["  ", "Real text ."]},
                {"heading": "Empty", "paragraphs": ["   "]}]
    assert clean_sections(sections) == [{"heading": "Intro", "paragraphs": ["Real text."]}]


def test_quality_check_flags_tiny_or_unstructured_documents():
    tiny = [{"heading": "A", "paragraphs": ["short"]}]
    problems = check_quality(tiny)
    assert any("characters" in p for p in problems)
    assert any("sections" in p for p in problems)


def test_quality_check_passes_reasonable_document():
    sections = [{"heading": f"H{i}", "paragraphs": ["x" * 1000]} for i in range(3)]
    assert check_quality(sections) == []


TABS_HTML = """
<html><head><title>Scoliosis | NIAMS</title></head><body><main>
  <h1>Scoliosis in Children and Teens</h1>
  <ul>
    <li>Overview, Symptoms, &amp; Causes</li>
    <li><a href="/dx">Diagnosis, Treatment, &amp; Steps To Take</a></li>
    <li><a href="/more">Research &amp; Resources</a></li>
  </ul>
  <h2>Symptoms of Scoliosis</h2>
  <p>Signs may include the following.</p>
  <ul><li>Top of shoulders are uneven.</li>
      <li>See <a href="/x">the guide</a> for more detail.</li></ul>
</main></body></html>
"""


def test_navigation_tab_list_is_dropped_but_real_bullets_kept():
    doc = extract_html(TABS_HTML)
    text = " ".join(p for s in doc["sections"] for p in s["paragraphs"])
    assert "Overview, Symptoms" not in text  # current tab is plain text, still navigation
    assert "Diagnosis, Treatment" not in text
    assert "Research & Resources" not in text
    assert "Top of shoulders are uneven." in text
    assert "See the guide for more detail." in text  # partly a link, so it is content


def test_a_list_of_real_bullets_is_never_treated_as_navigation():
    html = ("<html><body><main><h2>Causes</h2><ul><li>Genes.</li><li>Hormones.</li>"
            "<li>Changes in cell structure.</li></ul></main></body></html>")
    doc = extract_html(html)
    assert doc["sections"][0]["paragraphs"] == ["Genes.", "Hormones.", "Changes in cell structure."]
