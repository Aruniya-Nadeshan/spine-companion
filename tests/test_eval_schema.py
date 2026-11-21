import json

import pytest

from src.eval.schema import (assign_split, dataset_fingerprint, load_questions, normalise,
                             summarise, validate_questions)

DOCS = [
    {"id": "niams", "sections": [{"heading": "Overview", "paragraphs": [
        "Scoliosis is a sideways curve of the spine.", "Girls are more likely than boys to have this type."]}]},
    {"id": "sosort", "sections": [{"heading": "Bracing", "paragraphs": [
        "Rigid bracing is recommended for growing patients with progressive curves."]}]},
]


def q(id="q1", **overrides):
    base = {"id": id, "question": "What is scoliosis?", "category": "in_scope", "subtype": "basics",
            "evidence": [{"source_id": "niams", "contains": "sideways curve of the spine"}]}
    base.update(overrides)
    return base


def test_normalise_unifies_quotes_dashes_case_and_spaces():
    assert normalise("  Don\u2019t \u201cPANIC\u201d \u2013 now\u00a0ok ") == 'don\'t "panic" - now ok'


def test_split_is_deterministic_and_roughly_thirty_percent_test():
    ids = [f"q{i:03d}" for i in range(1000)]
    splits = [assign_split(i) for i in ids]
    assert splits == [assign_split(i) for i in ids]
    assert 250 < splits.count("test") < 350


def test_valid_dataset_has_no_errors():
    errors, warnings = validate_questions([q()], DOCS)
    assert errors == [] and warnings == []


def test_evidence_must_exist_in_the_named_source():
    errors, _ = validate_questions([q(evidence=[{"source_id": "niams", "contains": "bracing is recommended"}])], DOCS)
    assert any("not found in niams" in e for e in errors)


def test_evidence_is_matched_after_normalisation():
    ev = [{"source_id": "niams", "contains": "SIDEWAYS  curve\nof the spine"}]
    assert validate_questions([q(evidence=ev)], DOCS)[0] == []


def test_unknown_source_is_an_error():
    errors, _ = validate_questions([q(evidence=[{"source_id": "nope", "contains": "x" * 20}])], DOCS)
    assert any("unknown source" in e for e in errors)


def test_in_scope_needs_evidence_and_others_must_not_have_it():
    errors, _ = validate_questions([q(evidence=[])], DOCS)
    assert any("need at least one evidence" in e for e in errors)
    errors, _ = validate_questions([q("q2", category="out_of_scope", subtype="off_topic")], DOCS)
    assert any("only in_scope" in e for e in errors)


def test_bad_category_and_subtype_are_errors():
    assert any("unknown category" in e for e in validate_questions([q(category="weird")], DOCS)[0])
    assert any("not valid for in_scope" in e for e in validate_questions([q(subtype="red_flag")], DOCS)[0])


def test_missing_fields_and_duplicate_ids():
    errors, _ = validate_questions([{"id": "q1", "question": ""}], DOCS)
    assert any("missing" in e for e in errors)
    errors, _ = validate_questions([q("q1"), q("q1", question="Another question")], DOCS)
    assert any("duplicate id" in e for e in errors)


def test_short_evidence_and_repeated_questions_warn():
    ev = [{"source_id": "niams", "contains": "Scoliosis is"}]
    _, warnings = validate_questions([q("q1", evidence=ev), q("q2", evidence=ev)], DOCS)
    assert any("very short" in w for w in warnings)
    assert any("same question text" in w for w in warnings)


def test_load_questions_reports_the_bad_line(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(json.dumps(q("q1")) + "\n\n{not json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 3"):
        load_questions(path)


def test_load_questions_skips_blank_lines_and_fills_defaults(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text('{"id": "q1", "question": "x", "category": "out_of_scope", "subtype": "off_topic"}\n\n',
                    encoding="utf-8")
    (item,) = load_questions(path)
    assert item["evidence"] == [] and item["notes"] == ""


def test_fingerprint_changes_when_the_file_changes(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text("a", encoding="utf-8")
    first = dataset_fingerprint(path)
    path.write_text("b", encoding="utf-8")
    assert first != dataset_fingerprint(path) and len(first) == 12


def test_summarise_counts_categories_and_sources():
    summary = summarise([q("q1"), q("q2", category="out_of_scope", subtype="off_topic", evidence=[])])
    assert summary["total"] == 2
    assert summary["by_category"] == {"in_scope": 1, "out_of_scope": 1}
    assert summary["by_source"] == {"niams": 1}
