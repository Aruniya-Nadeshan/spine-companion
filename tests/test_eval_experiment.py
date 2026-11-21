import json

import pytest

from src.eval.experiment import (apply_embed_text_mode, build_variant, compare_rows, find_baseline,
                                 format_comparison, index_name, markdown_row, run_variant, sign_test_p)
from src.rag.chunk import chunk_document


def make_doc():
    return {"id": "niams", "title": "Guide", "publisher": "P", "url": "https://example.org",
            "licence": "PD", "attribution": "Credit", "date_accessed": "2026-11-21",
            "sections": [{"heading": "Symptoms",
                          "paragraphs": ["Uneven shoulders and one hip higher than the other are signs of scoliosis. " * 4]},
                         {"heading": "Causes",
                          "paragraphs": ["Genes and hormones may play a role in idiopathic scoliosis. " * 4]}]}


def test_embed_text_modes_change_only_what_the_model_reads():
    chunks = chunk_document(make_doc(), min_words=0)
    shown = [c.text for c in chunks]
    apply_embed_text_mode(chunks, "none")
    assert all(c.embed_text == c.text for c in chunks)
    apply_embed_text_mode(chunks, "heading")
    assert chunks[0].embed_text.startswith("Symptoms\n")
    apply_embed_text_mode(chunks, "title_heading")
    assert chunks[0].embed_text.startswith("Guide | Symptoms\n")
    assert [c.text for c in chunks] == shown      # displayed text is never modified


def test_unknown_embed_text_mode_is_rejected():
    with pytest.raises(ValueError):
        apply_embed_text_mode([], "everything")


@pytest.mark.parametrize("wins,losses,expected", [(0, 0, 1.0), (3, 0, 0.25), (5, 0, 0.0625), (3, 1, 0.625), (4, 4, 1.0)])
def test_sign_test_known_values(wins, losses, expected):
    assert sign_test_p(wins, losses) == pytest.approx(expected)


def row(id, rank, category="in_scope"):
    return {"id": id, "category": category, "rank": rank}


def test_compare_rows_counts_better_worse_and_same_with_missing_treated_as_worst():
    base = [row("a", 3), row("b", 1), row("c", None), row("d", 2), row("e", 1, "out_of_scope")]
    new = [row("a", 1), row("b", 2), row("c", 4), row("d", 2), row("e", 1, "out_of_scope")]
    summary, detail = compare_rows(base, new)
    assert summary["better"] == ["a", "c"]
    assert summary["worse"] == ["b"]
    assert summary["same"] == ["d"]
    assert summary["compared"] == 4
    assert detail["c"] == (None, 4)
    text = format_comparison(summary, detail, "baseline", "variant")
    assert "better: 2   worse: 1   same: 1" in text and "c: rank MISS -> 4" in text


def test_build_and_run_a_variant_end_to_end(tmp_path, fake_embedder):
    docs = [make_doc()]
    n = build_variant("v1", docs, fake_embedder, 250, 40, 0, "none", index_root=tmp_path)
    assert n == 2
    questions = [{"id": "q1", "question": "uneven shoulders and hip", "category": "in_scope", "subtype": "basics",
                  "evidence": [{"source_id": "niams", "contains": "one hip higher than the other"}]}]
    rows, summary = run_variant(questions, fake_embedder, "v1", 5, index_root=tmp_path)
    assert rows[0]["rank"] == 1 and summary["hit@1"]["value"] == 1.0


def test_markdown_row_has_the_experiment_log_columns():
    record = {"label": "no-heading", "change": "embed text only", "dataset": "abc123", "split": "dev",
              "summary": {"n_in_scope": 22, "hit@1": {"value": 0.5}, "hit@3": {"value": 0.75},
                          "hit@5": {"value": 0.9}, "mrr": 0.66}}
    row_text = markdown_row(record, "baseline-v1.1")
    assert "| no-heading | embed text only | abc123 | dev | 22 | 0.500 | 0.750 | 0.900 | 0.660 |" in row_text
    assert row_text.endswith("compare with baseline-v1.1 |")


def test_find_baseline_returns_the_newest_matching_run(tmp_path):
    for stamp, label in (("20261121-100000", "baseline"), ("20261121-110000", "no-heading"),
                         ("20261121-120000", "baseline-v1.1")):
        (tmp_path / f"{stamp}-{label}.json").write_text(json.dumps({"label": label}), encoding="utf-8")
    path, record = find_baseline(tmp_path)
    assert record["label"] == "baseline-v1.1" and path.name.endswith("baseline-v1.1.json")
    with pytest.raises(FileNotFoundError):
        find_baseline(tmp_path, prefix="missing")


def test_index_names_are_made_safe_for_chromadb():
    assert index_name("no-heading") == "exp-no-heading"
    assert index_name("v1") == "exp-v1"                      # short names are fine because of the prefix
    assert index_name("small chunks (120/20)") == "exp-small-chunks--120-20"
    assert index_name("///") == "exp-experiment"
