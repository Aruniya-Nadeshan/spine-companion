import json

import pytest

from src.eval.compare_runs import check_comparable, format_source_mix, load_run, source_mix


def row(id, sources, category="in_scope"):
    return {"id": id, "category": category, "rank": 1, "top_sources": sources}


def test_source_mix_counts_top1_and_top3_shares():
    rows = [row("a", ["sosort", "niams", "niams"]), row("b", ["niams", "sosort", "sosort"]),
            row("c", ["niams"], category="out_of_scope")]
    mix = source_mix(rows)
    assert mix["sosort"] == {"top1": 0.5, "top3": 0.5}
    assert mix["niams"] == {"top1": 0.5, "top3": 0.5}


def test_source_mix_ignores_out_of_scope_and_empty_rows():
    assert source_mix([row("c", ["niams"], category="safety"), row("d", [])]) == {}


def test_format_source_mix_lists_each_source():
    text = format_source_mix("run", {"niams": {"top1": 0.25, "top3": 0.5}})
    assert "run" in text and "niams" in text and "25%" in text and "50%" in text


def test_runs_must_share_dataset_and_split():
    a = {"dataset": "x", "split": "dev"}
    assert check_comparable(a, {"dataset": "x", "split": "dev"}) == []
    problems = check_comparable(a, {"dataset": "y", "split": "test"})
    assert len(problems) == 2


def test_load_run_by_label_returns_the_newest_match(tmp_path):
    for stamp, label in (("20261121-100000", "baseline"), ("20261121-110000", "baseline"), ("20261121-120000", "other")):
        (tmp_path / f"{stamp}-{label}.json").write_text(json.dumps({"label": label, "stamp": stamp}), encoding="utf-8")
    path, record = load_run("baseline", tmp_path)
    assert record["stamp"] == "20261121-110000"
    with pytest.raises(FileNotFoundError):
        load_run("missing", tmp_path)


def test_load_run_accepts_a_file_path(tmp_path):
    file = tmp_path / "run.json"
    file.write_text(json.dumps({"label": "x"}), encoding="utf-8")
    assert load_run(str(file))[1]["label"] == "x"


def test_runs_must_share_the_same_batch():
    a = {"dataset": "x", "split": "dev", "batch": 2}
    assert check_comparable(a, {"dataset": "x", "split": "dev", "batch": 2}) == []
    assert any("batches" in p for p in check_comparable(a, {"dataset": "x", "split": "dev"}))
