from src.ingest.glue_report import camel_tokens, rare_unknown_words, suspects, unusual_characters

BASE = ("experience and preparation avoid problems surface assessment scoliosis is the Cobb "
        "angle for patients with that there by of in to brace wear ")
KNOWN = set(BASE.lower().split()) | {"thereby"}


def is_known(word):
    return word in KNOWN


def rows_for(extra, times=8):
    sections = [{"heading": "Intro", "paragraphs": [BASE * times, extra]}]
    return {r["word"]: r for r in suspects(sections, is_known=is_known)}


def test_frequent_glue_is_reported_as_too_common():
    rows = rows_for("theCobb " * 12)
    assert rows["theCobb"]["reason"] == "appears more than 10 times"
    assert rows["theCobb"]["count"] == 12


def test_missed_glue_would_be_flagged_as_repairable():
    assert rows_for("experienceand")["experienceand"]["reason"] == "would be repaired"


def test_ordinary_words_are_hidden_unless_all_is_requested():
    assert "thereby" not in rows_for("thereby")
    sections = [{"heading": "H", "paragraphs": [BASE * 8, "thereby"]}]
    shown = {r["word"] for r in suspects(sections, is_known=is_known, show_all=True)}
    assert "thereby" in shown


def test_unusual_characters_reports_invisible_ones():
    sections = [{"heading": "H", "paragraphs": ["the\u200bCobb angle of 30\u00b0"]}]
    found = {ch: (name, n) for ch, name, n in unusual_characters(sections)}
    assert found["\u200b"] == ("ZERO WIDTH SPACE", 1)
    assert found["\u00b0"] == ("DEGREE SIGN", 1)


def test_rare_unknown_words_lists_long_rare_words_with_context():
    sections = [{"heading": "H", "paragraphs": [BASE * 8, "a hugelylonggluedtoken appears here and common words"]}]
    rows = rare_unknown_words(sections, is_known=is_known)
    assert [r["word"] for r in rows] == ["hugelylonggluedtoken"]
    assert "appears here" in rows[0]["context"]


def test_rare_unknown_words_ignores_known_acronyms_and_frequent_words():
    sections = [{"heading": "H", "paragraphs": [BASE * 8, "SOSORTGUIDELINES " + "scoliosisbracing " * 5]}]
    assert rare_unknown_words(sections, is_known=is_known) == []


def test_camel_tokens_lists_words_with_a_capital_in_the_middle():
    sections = [{"heading": "H", "paragraphs": ["searched PubMed for dysfunctionTo prevent, Cobb angle and SOSORT"]}]
    assert [r["word"] for r in camel_tokens(sections)] == ["dysfunctionTo", "PubMed"]
