"""Store chunk embeddings in a local ChromaDB collection and open it again for search."""
import chromadb

from src.rag.config import COLLECTION, INDEX_DIR

BATCH = 128


def build_index(chunks, embedder, index_dir=INDEX_DIR, collection=COLLECTION):
    """Create the collection from scratch. Rebuilding always starts clean, so it is repeatable."""
    client = chromadb.PersistentClient(path=str(index_dir))
    try:
        client.delete_collection(collection)
    except Exception:
        pass  # nothing to delete on the first run
    col = client.create_collection(name=collection, metadata={"hnsw:space": "cosine"})

    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        col.add(
            ids=[c.id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch],
            embeddings=embedder.embed_documents([c.embed_text for c in batch]),
        )
    return col


def open_collection(index_dir=INDEX_DIR, collection=COLLECTION):
    client = chromadb.PersistentClient(path=str(index_dir))
    try:
        return client.get_collection(collection)
    except Exception as exc:
        raise RuntimeError(
            f"No index found in {index_dir}. Build it first: python -m src.rag.build_index"
        ) from exc
