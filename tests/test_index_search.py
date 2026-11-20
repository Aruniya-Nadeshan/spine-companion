from src.rag.chunk import chunk_all
from src.rag.index import build_index, open_collection
from src.rag.search import format_hit, search
from src.rag.smoke import run_smoke

import pytest


def make_doc(doc_id, sections):
    return {"id": doc_id, "title": f"Guide {doc_id}", "publisher": "Pub", "url": f"https://example.org/{doc_id}",
            "licence": "CC BY 4.0", "attribution": f"Credit {doc_id}", "date_accessed": "2026-11-19",
            "sections": sections}


DOCS = [
    make_doc("niams", [
        {"heading": "Symptoms", "paragraphs": ["Uneven shoulders and one hip higher than the other are signs of scoliosis."]},
        {"heading": "Causes", "paragraphs": ["Genes and hormones may play a role in idiopathic scoliosis."]},
    ]),
    make_doc("sosort", [
        {"heading": "Bracing", "paragraphs": ["Rigid bracing is recommended for growing patients with progressive curves."]},
    ]),
]


@pytest.fixture
def index_dir(tmp_path, fake_embedder):
    build_index(chunk_all(DOCS), fake_embedder, index_dir=tmp_path / "idx")
    return tmp_path / "idx"


def test_search_returns_the_matching_chunk_first(index_dir, fake_embedder):
    hits = search("what are the signs of uneven shoulders", fake_embedder, k=3, index_dir=index_dir)
    assert hits[0]["metadata"]["heading"] == "Symptoms"
    assert hits[0]["metadata"]["source_id"] == "niams"


def test_hits_carry_attribution_and_score_order(index_dir, fake_embedder):
    hits = search("bracing for growing patients", fake_embedder, k=3, index_dir=index_dir)
    assert hits[0]["metadata"]["attribution"] == "Credit sosort"
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_k_larger_than_index_does_not_crash(index_dir, fake_embedder):
    hits = search("scoliosis", fake_embedder, k=50, index_dir=index_dir)
    assert len(hits) == 3


def test_rebuilding_does_not_duplicate_chunks(tmp_path, fake_embedder):
    chunks = chunk_all(DOCS)
    build_index(chunks, fake_embedder, index_dir=tmp_path / "idx")
    build_index(chunks, fake_embedder, index_dir=tmp_path / "idx")
    assert open_collection(tmp_path / "idx").count() == len(chunks)


def test_empty_query_is_rejected(index_dir, fake_embedder):
    with pytest.raises(ValueError):
        search("   ", fake_embedder, index_dir=index_dir)


def test_missing_index_gives_a_helpful_error(tmp_path, fake_embedder):
    with pytest.raises(RuntimeError, match="build_index"):
        search("anything", fake_embedder, index_dir=tmp_path / "nothing")


def test_format_hit_shows_source_and_attribution(index_dir, fake_embedder):
    hit = search("causes genes hormones", fake_embedder, k=1, index_dir=index_dir)[0]
    text = format_hit(1, hit)
    assert "niams" in text and "Causes" in text and "Credit niams" in text


def test_run_smoke_reports_pass_and_fail():
    def fake_search(question, k):
        return [{"metadata": {"source_id": "niams"}}]

    results = run_smoke(fake_search, questions=[("q1", {"niams"}), ("q2", {"sosort"})])
    assert results == [("q1", True, "niams"), ("q2", False, "niams")]
