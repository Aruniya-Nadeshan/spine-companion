"""Turn raw HTML into a title plus a list of sections.

Each section is {"heading": str, "paragraphs": [str, ...]}.
Navigation, scripts and footers are removed, and sections such as
References are dropped because they add noise to retrieval.
"""
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside",
              "form", "noscript", "svg", "button"]
HEADING_TAGS = ["h1", "h2", "h3", "h4"]
TEXT_TAGS = ["p", "li"]

# Sections that are not useful knowledge for the chatbot.
EXCLUDED_HEADINGS = {"references", "reference", "footnotes", "abbreviations",
                     "acknowledgements", "acknowledgments", "funding",
                     "competing interests", "publisher's note", "author information"}


def _is_link_only(el):
    """True if every word in this element is link text (typical of tab and menu lists)."""
    links = el.find_all("a")
    if not links:
        return False
    link_text = "".join(a.get_text(" ", strip=True) for a in links)
    return link_text.replace(" ", "") == el.get_text(" ", strip=True).replace(" ", "")


def _remove_navigation_lists(root):
    """Delete lists that are really menus or page tabs.

    A list counts as navigation when it has 2+ items, at least half of them are
    pure links, and every item is short. The current tab is often plain text
    rather than a link, which is why the check is on the list, not each item.
    """
    for lst in root.find_all(["ul", "ol"]):
        items = lst.find_all("li", recursive=False)
        if len(items) < 2:
            continue
        link_only = sum(_is_link_only(li) for li in items)
        all_short = all(len(li.get_text(" ", strip=True)) <= 80 for li in items)
        if link_only * 2 >= len(items) and all_short:
            lst.decompose()


def extract_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    root = soup.find("main") or soup.find("article") or soup.body or soup
    _remove_navigation_lists(root)

    sections = []
    current = {"heading": title or "Introduction", "paragraphs": []}
    for el in root.find_all(HEADING_TAGS + TEXT_TAGS):
        # Skip a <p> inside an <li> (or nested items): the parent already holds the text.
        if el.name in TEXT_TAGS and el.find_parent(TEXT_TAGS):
            continue
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name in HEADING_TAGS:
            if current["paragraphs"]:
                sections.append(current)
            current = {"heading": text, "paragraphs": []}
        else:
            current["paragraphs"].append(text)
    if current["paragraphs"]:
        sections.append(current)

    sections = [s for s in sections
                if s["heading"].strip().lower() not in EXCLUDED_HEADINGS]
    return {"title": title, "sections": sections}


# ---------------------------------------------------------------------------
# JATS XML (the article format used by PubMed Central / Europe PMC)
# ---------------------------------------------------------------------------


# Elements whose text is not useful prose for retrieval.
JATS_SKIP = {"table-wrap", "fig", "supplementary-material", "disp-formula"}


def _local(tag):
    """Strip any XML namespace: '{ns}p' -> 'p'."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _jats_text(el):
    """All text under el, dropping citation markers like [12] and skipped blocks."""
    parts = [el.text or ""]
    for child in el:
        name = _local(child.tag)
        is_citation = name == "xref" and child.get("ref-type") == "bibr"
        if not is_citation and name not in JATS_SKIP:
            parts.append(_jats_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def _jats_paragraphs(sec):
    """Paragraphs that sit directly in a <sec>/<abstract>, including list items."""
    paragraphs = []
    for child in sec:
        name = _local(child.tag)
        if name == "p":
            paragraphs.append(_jats_text(child))
        elif name == "list":
            for item in child.iter():
                if _local(item.tag) == "p":
                    paragraphs.append(_jats_text(item))
    return paragraphs


def _walk_sec(sec, trail, sections):
    """Depth-first walk; each <sec> becomes a section headed 'Parent > Child'."""
    title_el = next((c for c in sec if _local(c.tag) == "title"), None)
    title = _jats_text(title_el).strip() if title_el is not None else ""
    if title.strip().lower() in EXCLUDED_HEADINGS:
        return
    trail = trail + [title] if title else trail
    paragraphs = _jats_paragraphs(sec)
    if paragraphs:
        sections.append({"heading": " > ".join(trail) or "Untitled", "paragraphs": paragraphs})
    for child in sec:
        if _local(child.tag) == "sec":
            _walk_sec(child, trail, sections)


def extract_jats(xml_text):
    """Turn JATS article XML into {'title', 'sections'} (same shape as extract_html)."""
    root = ET.fromstring(xml_text)
    # Europe PMC may wrap the article in a response element.
    article = root if _local(root.tag) == "article" else next(
        (el for el in root.iter() if _local(el.tag) == "article"), root)

    title_el = next((el for el in article.iter() if _local(el.tag) == "article-title"), None)
    title = _jats_text(title_el).strip() if title_el is not None else ""

    sections = []
    abstract = next((el for el in article.iter() if _local(el.tag) == "abstract"), None)
    if abstract is not None:
        _walk_sec(abstract, ["Abstract"], sections)
    body = next((el for el in article.iter() if _local(el.tag) == "body"), None)
    if body is not None:
        _walk_sec(body, [], sections)
    return {"title": title, "sections": sections}


def extract_document(content, fmt):
    """Pick the right extractor for a source's declared format."""
    if fmt == "jats-xml":
        return extract_jats(content)
    if fmt == "html":
        return extract_html(content)
    raise ValueError(f"Unknown format: {fmt}")
