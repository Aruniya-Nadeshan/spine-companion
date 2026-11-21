from src.eval.audit import audit_question


def hit(source, heading, text, score=0.7):
    return {"text": text, "score": score, "metadata": {"source_id": source, "heading": heading}}


def test_audit_marks_hits_and_shows_text():
    question = {"id": "q1", "question": "Does it run in families?",
                "evidence": [{"source_id": "niams", "contains": "parent, brother, or sister"}]}
    hits = [hit("sosort", "Sports", "Unrelated sports text."),
            hit("niams", "Who Gets Scoliosis?", "You are more likely if your parent, brother, or sister has it.")]
    lines = audit_question(question, hits)
    text = "\n".join(lines)
    assert "q1  Does it run in families?" in text
    assert "[niams] 'parent, brother, or sister'" in text
    assert any(l.strip().startswith("[1]") and "HIT" not in l for l in lines)
    assert any("HIT" in l and "[2]" in l for l in lines)
    assert "Unrelated sports text." in text


def test_long_chunks_are_truncated_in_the_preview():
    question = {"id": "q1", "question": "q?", "evidence": [{"source_id": "a", "contains": "zzz"}]}
    lines = audit_question(question, [hit("a", "H", "word " * 200)], preview_chars=100)
    assert any(l.rstrip().endswith("...") for l in lines)
