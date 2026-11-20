"""Turn text into embeddings (lists of numbers) with a local sentence-transformers model.

The heavy library is imported inside __init__ so tests can run without it.
Vectors are normalised, so cosine similarity is a plain dot product.
"""
from src.rag.config import EMBED_MODEL, QUERY_PREFIX


class Embedder:
    def __init__(self, model_name=EMBED_MODEL):
        from sentence_transformers import SentenceTransformer  # slow import, so done lazily

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts, batch_size=32):
        vectors = self.model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True,
            show_progress_bar=len(texts) > 64)
        return vectors.tolist()

    def embed_query(self, query):
        vector = self.model.encode(QUERY_PREFIX + query, normalize_embeddings=True)
        return vector.tolist()
