"""Fail loudly when extraction looks wrong, so a silent failure cannot reach the index."""

MIN_CHARS = 2000
MIN_SECTIONS = 3


def count_chars(sections):
    return sum(len(p) for s in sections for p in s["paragraphs"])


def check_quality(sections, min_chars=MIN_CHARS, min_sections=MIN_SECTIONS):
    """Return a list of problems (empty list means the document passed)."""
    problems = []
    n_chars = count_chars(sections)
    if n_chars < min_chars:
        problems.append(f"only {n_chars} characters extracted (minimum {min_chars})")
    if len(sections) < min_sections:
        problems.append(f"only {len(sections)} sections found (minimum {min_sections})")
    return problems
