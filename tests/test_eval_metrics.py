from src.eval.passages import find_text
from src.eval.retrieval_eval import (evaluate_retrieval, first_relevant_rank, is_hit,
                                     score_distribution, select_split, suggest_threshold,
                                     wilson_interval)
from src.eval.schema import assign_split


def hit(source, text, score=0.5, heading="H"):
    return {"text": text, "score": score, "metadata": {"source_id": source, "heading": heading}}


EVIDENCE = [{"source_id": "niams", "contains": "sideways curve"}]


def test_a_hit_needs_the_right_source_and_the_phrase():
    assert is_hit(hit("niams", "A SIDEWAYS  curve of the spine"), EVIDENCE)
    assert not is_hit(hit("sosort", "a sideways curve"), EVIDENCE)   # right words, wrong source
    assert not is_hit(hit("niams", "something else"), EVIDENCE)


def test_any_of_several_evidence_entries_counts():
    evidence = EVIDENCE + [{"source_id": "sosort", "contains": "rigid bracing"}]
    assert is_hit(hit("sosort", "Rigid bracing works"), evidence)


def test_first_relevant_rank_is_one_based_or_none():
    hits = [hit("niams", "nothing"), hit("niams", "sideways curve"), hit("niams", "sideways curve")]
    assert first_relevant_rank(hits, EVIDENCE) == 2
    assert first_relevant_rank(hits[:1], EVIDENCE) is None


def question(id, category="in_scope", subtype="basics", evidence=EVIDENCE):
    return {"id": id, "question": f"question {id}", "category": category, "subtype": subtype,
            "evidence": evidence if category == "in_scope" else []}


def test_metrics_hit_rates_and_mrr():
    results = {
        "question a": [hit("niams", "sideways curve")],                                   # rank 1
        "question b": [hit("niams", "x"), hit("niams", "x"), hit("niams", "sideways curve")],  # rank 3
        "question c": [hit("niams", "x")] * 5,                                              # miss
        "question d": [hit("niams", "x"), hit("niams", "sideways curve")],                 # rank 2
    }
    questions = [question(k.split()[1]) for k in results]
    rows, summary = evaluate_retrieval(questions, lambda text, k: results[text][:k], k=5)
    assert summary["n_in_scope"] == 4
    assert summary["hit@1"]["value"] == 0.25
    assert summary["hit@3"]["value"] == 0.75
    assert summary["hit@5"]["value"] == 0.75
    assert abs(summary["mrr"] - (1 + 1 / 3 + 0 + 1 / 2) / 4) < 1e-9
    assert summary["by_subtype"] == {"basics": {"n": 4, "hits": 3}}
    assert [r["rank"] for r in rows] == [1, 3, None, 2]


def test_out_of_scope_questions_are_not_scored_for_hits():
    questions = [question("a"), question("b", category="out_of_scope", subtype="off_topic")]
    rows, summary = evaluate_retrieval(questions, lambda text, k: [hit("niams", "sideways curve", 0.3)], k=5)
    assert summary["n_in_scope"] == 1
    assert rows[1]["rank"] is None and rows[1]["top_score"] == 0.3


def test_wilson_interval_is_wide_for_small_samples_and_bounded():
    low, high = wilson_interval(3, 4)
    assert 0.3 < low < 0.5 and 0.9 < high <= 1.0
    low2, high2 = wilson_interval(75, 100)
    assert (high2 - low2) < (high - low)
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_score_distribution_groups_by_category_and_subtype():
    rows = [{"category": "in_scope", "subtype": "basics", "top_score": 0.8},
            {"category": "in_scope", "subtype": "basics", "top_score": 0.6},
            {"category": "out_of_scope", "subtype": "off_topic", "top_score": 0.3}]
    dist = score_distribution(rows)
    assert dist["in_scope/basics"]["mean"] == 0.7 and dist["out_of_scope/off_topic"]["n"] == 1


def test_threshold_separates_answerable_from_off_topic():
    rows = ([{"category": "in_scope", "subtype": "basics", "top_score": s} for s in (0.9, 0.8, 0.7)]
            + [{"category": "out_of_scope", "subtype": "off_topic", "top_score": s} for s in (0.4, 0.3)])
    best = suggest_threshold(rows)
    assert 0.4 < best["threshold"] <= 0.7
    assert best["answered_in_scope"] == 1.0 and best["declined_off_topic"] == 1.0


def test_threshold_ignores_personal_advice_and_handles_missing_groups():
    rows = [{"category": "in_scope", "subtype": "basics", "top_score": 0.8},
            {"category": "out_of_scope", "subtype": "personal_advice", "top_score": 0.9}]
    assert suggest_threshold(rows) is None   # no off-topic questions to compare against


def test_select_split_partitions_the_questions():
    questions = [question(f"q{i:03d}") for i in range(60)]
    dev, test = select_split(questions, "dev"), select_split(questions, "test")
    assert len(dev) + len(test) == 60 and not {q["id"] for q in dev} & {q["id"] for q in test}
    assert all(assign_split(q["id"]) == "test" for q in test)
    assert select_split(questions, "all") == questions


def test_find_text_returns_source_section_and_snippet():
    docs = [{"id": "niams", "sections": [{"heading": "A", "paragraphs": ["no match"]},
                                           {"heading": "B", "paragraphs": ["Bracing may be needed."]}]}]
    ((source, idx, heading, snippet),) = find_text(docs, "bracing")
    assert (source, idx, heading) == ("niams", 1, "B") and "Bracing may be needed." in snippet
