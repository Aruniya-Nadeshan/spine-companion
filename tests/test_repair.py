from src.ingest.repair import build_vocab, repair_sections

BASE = ("experience and preparation avoid problems surface assessment scoliosis is the Cobb "
        "angle for patients with that there by of in to brace wear ")
KNOWN = set(BASE.lower().split()) | {"thereby"}  # stand-in for the English dictionary


def is_known(word):
    return word in KNOWN


def repaired(extra, filler_times=8):
    sections = [{"heading": "Intro", "paragraphs": [BASE * filler_times, extra]}]
    out, repairs = repair_sections(sections, is_known=is_known)
    return out[0]["paragraphs"][1], repairs


def test_glued_words_are_split():
    text, repairs = repaired("it requires experienceand preparation to avoidproblems here")
    assert text == "it requires experience and preparation to avoid problems here"
    assert {r["from"] for r in repairs} == {"experienceand", "avoidproblems"}


def test_short_function_word_at_the_end_is_found():
    text, _ = repaired("the disease scoliosisis common")
    assert "scoliosis is" in text


def test_capital_letters_are_preserved():
    text, _ = repaired("Surfaceassessment and theCobb angle")
    assert text == "Surface assessment and the Cobb angle"


def test_systematic_glue_repeated_several_times_is_still_repaired():
    text, repairs = repaired("theCobb theCobb theCobb theCobb")
    assert text == "the Cobb the Cobb the Cobb the Cobb"
    assert repairs == [{"from": "theCobb", "to": "the Cobb", "count": 4}]


def test_dictionary_words_are_never_split_even_if_they_look_glued():
    text, repairs = repaired("thereby reducing risk")
    assert text == "thereby reducing risk"
    assert repairs == []


def test_unknown_terms_without_known_parts_are_left_alone():
    text, repairs = repaired("kyphoscoliosis was observed")
    assert text == "kyphoscoliosis was observed"
    assert repairs == []


def test_prefixes_are_respected():
    text, repairs = repaired("nonoperative care")
    assert text == "nonoperative care"
    assert repairs == []


def test_acronyms_and_numbers_are_untouched():
    text, repairs = repaired("SOSORTGUIDELINES 2016 Cobb30")
    assert text == "SOSORTGUIDELINES 2016 Cobb30"
    assert repairs == []


def test_a_word_used_as_often_as_its_parts_is_real_vocabulary():
    # "bracewear" appears 6 times; "brace" and "wear" appear 8 times in the filler
    text, repairs = repaired("bracewear " * 6)
    assert "bracewear" in text
    assert repairs == []


def test_very_frequent_unknown_words_are_never_split():
    sections = [{"heading": "H", "paragraphs": [("scoliosispatients " + BASE) * 12]}]
    _, repairs = repair_sections(sections, is_known=is_known)
    assert repairs == []


def test_short_glue_of_two_function_words_is_repaired_but_other_short_words_are_not():
    text, repairs = repaired("one ofthe cases and cobbis rare")
    assert "of the" in text
    assert "cobbis" in text  # 6 letters, not made of function words, so left alone
    assert [r["from"] for r in repairs] == ["ofthe"]


def test_repairs_are_counted_and_reported():
    _, repairs = repaired("avoidproblems and avoidproblems")
    assert repairs == [{"from": "avoidproblems", "to": "avoid problems", "count": 2}]


def test_headings_are_repaired_too():
    sections = [{"heading": "Intro", "paragraphs": [BASE * 8]},
                {"heading": "Surfaceassessment", "paragraphs": ["short"]}]
    out, _ = repair_sections(sections, is_known=is_known)
    assert out[1]["heading"] == "Surface assessment"


def test_build_vocab_counts_lowercase_words():
    vocab = build_vocab([{"heading": "Cobb Angle", "paragraphs": ["The cobb angle."]}])
    assert vocab["cobb"] == 2 and vocab["angle"] == 2


def test_web_addresses_are_left_alone():
    text, repairs = repaired("see scoliosisisthe.example.org and www.avoidproblems.com or me@experienceand.org")
    assert "scoliosisisthe.example.org" in text
    assert "www.avoidproblems.com" in text
    assert "me@experienceand.org" in text
    assert repairs == []


def test_a_glued_word_at_the_end_of_a_sentence_is_still_repaired():
    text, _ = repaired("This helps avoidproblems. Next sentence")
    assert "avoid problems. Next sentence" in text


CAMEL_KNOWN = KNOWN | {"dysfunction", "prevent", "literature", "methodology", "background", "treat", "to"}


def camel(extra):
    sections = [{"heading": "Intro", "paragraphs": [(BASE + "dysfunction prevent literature methodology background treat ") * 8, extra]}]
    out, repairs = repair_sections(sections, is_known=lambda w: w in CAMEL_KNOWN)
    return out[0]["paragraphs"][1], repairs


def test_capital_at_the_join_with_a_function_word_is_split():
    text, repairs = camel("respiratory dysfunctionTo prevent or treat")
    assert text == "respiratory dysfunction To prevent or treat"
    assert repairs == [{"from": "dysfunctionTo", "to": "dysfunction To", "count": 1}]


def test_capital_at_the_join_between_two_real_words_is_split():
    text, _ = camel("see flow-chartsLiterature review and MethodologyBackground notes")
    assert "flow-charts Literature review" not in text  # "charts" is not a word the fake dictionary knows
    assert "Methodology Background notes" in text


def test_known_names_with_internal_capitals_are_kept():
    text, repairs = camel("searched PubMed and ScoliScore and SpineCor and McMaster")
    assert text == "searched PubMed and ScoliScore and SpineCor and McMaster"
    assert repairs == []


def test_acronyms_and_mixed_case_names_are_not_split():
    text, repairs = camel("BrAIST and iPhone and SPORTDiscus")
    assert text == "BrAIST and iPhone and SPORTDiscus"
    assert repairs == []


def test_camel_glue_inside_a_web_address_is_left_alone():
    text, repairs = camel("see example.com/dysfunctionTo for details")
    assert "example.com/dysfunctionTo" in text
    assert repairs == []
