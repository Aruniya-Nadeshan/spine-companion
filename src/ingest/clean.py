"""Normalise extracted text so later steps (chunking, embedding) see clean input."""
import re
import unicodedata


def clean_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    # get_text(" ") leaves a space before punctuation: "word ," -> "word,"
    text = re.sub(r"\s+([.,;:!?)\]])", r"\1", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    return text.strip()


def clean_sections(sections):
    """Clean every heading and paragraph, dropping anything left empty."""
    cleaned = []
    for sec in sections:
        paragraphs = [clean_text(p) for p in sec["paragraphs"]]
        paragraphs = [p for p in paragraphs if p]
        heading = clean_text(sec["heading"])
        if paragraphs:
            cleaned.append({"heading": heading, "paragraphs": paragraphs})
    return cleaned
