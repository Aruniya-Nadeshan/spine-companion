import math

import pytest

from src.eval.experiment import build_variant, run_variant
from src.rag.chunk import chunk_document
from src.rag.retrieve import BM25, Retriever, reciprocal_rank_fusion, stem, tokenize


def test_stemming_and_tokenizing_drop_stopwords_and_plurals():
    assert stem("braces") == "brace" and stem("grows") == "grow" and stem("class") == "class"
    assert stem("studies") == "study" and stem("is") == "is"
    assert tokenize("Will she need a new brace as she grows?") == ["need", "new", "brace", "grow"]


def test_bm25_ranks_documents_that_share_rare_words_higher():
    docs = ["the brace has to be changed for a new one as the child grows",
            "scoliosis is a sideways curve of the spine",
            "a brace is recommended for curves above twenty five degrees"]
    scores = BM25(docs).scores("new brace as she grows")
    assert scores[0] > scores[2] > 0 and scores[1] == 0


def test_bm25_handles_an_empty_query_and_empty_corpus():
    assert BM25(["a b c"]).scores("the of") == [0.0]
    assert BM25([]).scores("anything") == []


def hit(source, section, text="t", score=0.0):
    return {"text": text, "score": score, "metadata": {"source_id": source, "section_index": section, "piece_index": 0}}


def test_reciprocal_rank_fusion_rewards_agreement_between_rankings():
    vector = [hit("a", 1), hit("a", 2), hit("a", 3)]
    keyword = [hit("a", 3), hit("a", 2), hit("a", 9)]
    fused = reciprocal_rank_fusion([vector, keyword], k=60)
    keys = [(h["metadata"]["section_index"]) for h in fused]
    assert set(keys[:2]) == {2, 3}                 # in both lists, so ahead of those in only one
    assert set(keys) == {1, 2, 3, 9}
    assert fused[0]["metadata"]["section_index"] == 3
    assert fused[0]["score"] == pytest.approx(1 / 61 + 1 / 63)    # ranked 3rd by vector, 1st by keyword
    assert fused[1]["score"] == pytest.approx(1 / 62 + 1 / 62)
    assert fused[1]["score"] > fused[2]["score"]


def make_doc():
    return {"id": "d", "title": "Guide", "publisher": "P", "url": "u", "licence": "L", "attribution": "A",
            "date_accessed": "2026-11-22",
            "sections": [
                {"heading": "Bracing", "paragraphs": ["The brace has to be changed for a new one as the child grows quickly. " * 3]},
                {"heading": "Causes", "paragraphs": ["Genes and hormones may play a role in idiopathic scoliosis causes. " * 3]},
                {"heading": "Surgery", "paragraphs": ["Spinal fusion joins vertebrae together with metal rods and screws. " * 3]}]}


@pytest.fixture
def index(tmp_path, fake_embedder):
    build_variant("t", [make_doc()], fake_embedder, 250, 40, 0, "none", index_root=tmp_path)
    return tmp_path


def test_vector_retriever_returns_hits_with_scores(index, fake_embedder):
    from src.eval.experiment import index_name
    name = index_name("t")
    retriever = Retriever(fake_embedder, index / name, name)
    hits = retriever("genes hormones causes", 3)
    assert hits[0]["metadata"]["heading"] == "Causes" and len(hits) == 3
    assert all("score" in h for h in hits)


def test_hybrid_retriever_adds_keyword_matches(index, fake_embedder):
    from src.eval.experiment import index_name
    name = index_name("t")
    retriever = Retriever(fake_embedder, index / name, name, hybrid=True, candidates=3)
    hits = retriever("new brace as she grows", 3)
    assert hits[0]["metadata"]["heading"] == "Bracing"
    assert len({h["metadata"]["heading"] for h in hits}) == len(hits)       # no duplicates after fusion


class KeywordReranker:
    """Stand-in cross-encoder: prefers passages containing the word 'fusion'."""
    def predict(self, pairs):
        return [text.lower().count("fusion") for _question, text in pairs]


def test_reranker_reorders_the_candidates(index, fake_embedder):
    from src.eval.experiment import index_name
    name = index_name("t")
    plain = Retriever(fake_embedder, index / name, name)
    reranked = Retriever(fake_embedder, index / name, name, reranker=KeywordReranker(), candidates=3)
    question = "brace changed child grows"
    assert plain(question, 1)[0]["metadata"]["heading"] == "Bracing"
    top = reranked(question, 1)[0]
    assert top["metadata"]["heading"] == "Surgery" and top["score"] > 0


def test_run_variant_accepts_the_new_options(index, fake_embedder):
    questions = [{"id": "q1", "question": "new brace as she grows", "category": "in_scope", "subtype": "treatment",
                  "evidence": [{"source_id": "d", "contains": "changed for a new one"}]}]
    rows, summary = run_variant(questions, fake_embedder, "t", 3, index_root=index, hybrid=True, candidates=3)
    assert rows[0]["rank"] == 1 and summary["hit@1"]["value"] == 1.0
