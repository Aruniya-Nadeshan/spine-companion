"""Retrieval pipelines: vector search, optionally fused with keyword search, optionally reranked.

    vector      embed the question, take the nearest chunks (the baseline)
    hybrid      also rank chunks by keyword match (BM25) and fuse the two rankings (RRF)
    rerank      take the top N candidates and let a second model, which reads the question
                and each passage together, put them in a better order
    small-to-big  (an index option, see experiment --child-words) match on small child chunks but
                return the whole parent passage

Each stage is optional, so an experiment can change exactly one thing at a time.
Every hit is {"text", "score", "metadata"}; "score" belongs to the last stage that ran
(cosine similarity, RRF score or reranker score), so scores from different pipelines are not
comparable with each other.
"""
import math
import re
from collections import Counter

from src.rag.config import COLLECTION, INDEX_DIR
from src.rag.index import open_collection

DEFAULT_RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
STOPWORDS = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "and", "or", "is", "are", "was", "be", "do", "does",
             "did", "how", "what", "when", "why", "which", "who", "my", "i", "me", "we", "she", "he", "her", "his",
             "it", "its", "that", "this", "with", "can", "will", "would", "should", "there", "if", "so", "as", "by"}


# ---------------------------------------------------------------- keyword search (BM25)

def stem(word):
    """Very light stemming so 'braces' matches 'brace' and 'grows' matches 'grow'."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokenize(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


class BM25:
    """The standard BM25 ranking function over a list of documents."""

    def __init__(self, documents, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.tokens = [Counter(tokenize(d)) for d in documents]
        self.lengths = [sum(t.values()) for t in self.tokens]
        self.n = len(documents)
        self.avg_len = (sum(self.lengths) / self.n) if self.n else 0.0
        doc_freq = Counter()
        for t in self.tokens:
            doc_freq.update(t.keys())
        self.idf = {w: math.log(1 + (self.n - df + 0.5) / (df + 0.5)) for w, df in doc_freq.items()}

    def scores(self, query):
        query_terms = tokenize(query)
        result = []
        for counts, length in zip(self.tokens, self.lengths):
            score = 0.0
            for term in query_terms:
                tf = counts.get(term, 0)
                if tf:
                    norm = tf + self.k1 * (1 - self.b + self.b * length / (self.avg_len or 1))
                    score += self.idf[term] * tf * (self.k1 + 1) / norm
            result.append(score)
        return result


# ---------------------------------------------------------------- fusion

def chunk_key(hit):
    """Identify a chunk. Child chunks of one parent differ by child_index."""
    meta = hit["metadata"]
    return (meta["source_id"], meta["section_index"], meta["piece_index"], meta.get("child_index", 0))


def reciprocal_rank_fusion(rankings, k=60):
    """Merge several ranked hit lists. A chunk scores 1/(k+rank) in each list it appears in."""
    fused, hits = Counter(), {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            key = chunk_key(hit)
            fused[key] += 1.0 / (k + rank)
            hits.setdefault(key, hit)
    ordered = sorted(fused, key=lambda key: fused[key], reverse=True)
    return [{**hits[key], "score": fused[key]} for key in ordered]


# ---------------------------------------------------------------- the pipeline

class Retriever:
    """Callable: retriever(question, k) -> list of hits, best first."""

    def __init__(self, embedder, index_dir=INDEX_DIR, collection=COLLECTION, hybrid=False,
                 reranker=None, candidates=20, rrf_k=60):
        self.embedder, self.hybrid, self.reranker = embedder, hybrid, reranker
        self.candidates, self.rrf_k = candidates, rrf_k
        self.col = open_collection(index_dir, collection)
        self._bm25 = self._bm25_hits = None

    def _vector(self, question, n):
        result = self.col.query(query_embeddings=[self.embedder.embed_query(question)],
                                n_results=min(n, self.col.count()),
                                include=["documents", "metadatas", "distances"])
        return [{"text": d, "score": 1.0 - dist, "metadata": m} for d, m, dist in
                zip(result["documents"][0], result["metadatas"][0], result["distances"][0])]

    def _keyword(self, question, n):
        if self._bm25 is None:
            data = self.col.get(include=["documents", "metadatas"])
            self._bm25_hits = [{"text": d, "metadata": m} for d, m in zip(data["documents"], data["metadatas"])]
            # the heading is searchable, as it is for the embedding model in the heading variants
            self._bm25 = BM25([f"{h['metadata']['heading']} {h['text']}" for h in self._bm25_hits])
        scores = self._bm25.scores(question)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [{**self._bm25_hits[i], "score": scores[i]} for i in order if scores[i] > 0]

    @staticmethod
    def _collapse_to_parents(hits):
        """If the index holds small child chunks, return each matching parent once, best child first."""
        if not hits or "parent_text" not in hits[0]["metadata"]:
            return hits
        seen, parents = set(), []
        for hit in hits:
            meta = dict(hit["metadata"])
            parent_id = meta["parent_id"]
            if parent_id in seen:
                continue
            seen.add(parent_id)
            text = meta.pop("parent_text")
            parents.append({"text": text, "score": hit["score"], "metadata": meta})
        return parents

    def __call__(self, question, k):
        n = max(self.candidates, k)
        pool = self._vector(question, n)
        if self.hybrid:
            pool = reciprocal_rank_fusion([pool, self._keyword(question, n)], self.rrf_k)[:n]
        if self.reranker is not None and pool:
            scores = self.reranker.predict([(question, hit["text"]) for hit in pool])
            ranked = sorted(zip(scores, pool), key=lambda pair: float(pair[0]), reverse=True)
            pool = [{**hit, "score": float(score)} for score, hit in ranked]
        return self._collapse_to_parents(pool)[:k]


def load_reranker(model_name=DEFAULT_RERANKER):
    """A cross-encoder from sentence-transformers (downloaded on first use)."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)
