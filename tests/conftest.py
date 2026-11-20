import re
import zlib

import pytest


class FakeEmbedder:
    """Deterministic stand-in for the real model: hashes words into a small vector.

    Texts that share words get similar vectors, which is enough to test the
    plumbing (chunking, indexing, searching, metadata) without downloading a model.
    """
    DIM = 128

    def _vec(self, text):
        vec = [0.0] * self.DIM
        for word in re.findall(r"[a-z]+", text.lower()):
            vec[zlib.crc32(word.encode()) % self.DIM] += 1.0
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]

    def embed_documents(self, texts, batch_size=32):
        return [self._vec(t) for t in texts]

    def embed_query(self, query):
        return self._vec(query)


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()
