"""Split processed documents into chunks that can be embedded and retrieved.

Rules:
- A section that fits in about one chunk stays whole.
- A longer section is split on sentence boundaries into chunks of about
  CHUNK_TARGET_WORDS words, repeating the last ~CHUNK_OVERLAP_WORDS words of
  each chunk at the start of the next, so a thought cut at a boundary survives.
- Every chunk keeps its source, heading and attribution (licence metadata).
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.rag.config import CHUNK_OVERLAP_WORDS, CHUNK_TARGET_WORDS

# Split after . ! ? when the next sentence starts with a capital, digit or bracket.
# Known limitation: abbreviations such as "e.g. Smith" can be split wrongly.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[\"'])")
# A section up to this size is kept whole instead of being split.
WHOLE_SECTION_FACTOR = 1.2


@dataclass
class Chunk:
    id: str
    source_id: str
    doc_title: str
    heading: str
    text: str            # shown to the user and given to the LLM
    embed_text: str      # what the embedding model reads (adds title and heading)
    metadata: dict       # stored in the index next to the vector

    @property
    def n_words(self):
        return len(self.text.split())


def split_sentences(text):
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]


def split_text(text, target=CHUNK_TARGET_WORDS, overlap=CHUNK_OVERLAP_WORDS):
    """Split text into overlapping pieces of about `target` words each."""
    pieces, current, count, fresh = [], [], 0, 0
    for sentence in split_sentences(text):
        n = len(sentence.split())
        if current and count + n > target:
            pieces.append(" ".join(current))
            # Carry the tail of this chunk (up to `overlap` words) into the next.
            carry, carried = [], 0
            for prev in reversed(current):
                pw = len(prev.split())
                if carried + pw > overlap:
                    break
                carry.insert(0, prev)
                carried += pw
            current, count, fresh = carry, carried, 0
        current.append(sentence)
        count += n
        fresh += 1
    # Only emit the last piece if it holds something not already in the previous one.
    if current and (fresh > 0 or not pieces):
        pieces.append(" ".join(current))
    return pieces


def chunk_document(doc, target=CHUNK_TARGET_WORDS, overlap=CHUNK_OVERLAP_WORDS):
    """Turn one processed document (the JSON from ingestion) into Chunk objects."""
    chunks = []
    for s_idx, section in enumerate(doc["sections"]):
        paragraphs = [p for p in section["paragraphs"] if p.strip()]
        if not paragraphs:
            continue
        full_text = "\n".join(paragraphs)
        if len(full_text.split()) <= target * WHOLE_SECTION_FACTOR:
            pieces = [full_text]
        else:
            pieces = split_text(" ".join(paragraphs), target, overlap)
        for p_idx, piece in enumerate(pieces):
            chunks.append(Chunk(
                id=f"{doc['id']}-{s_idx:03d}-{p_idx:02d}",
                source_id=doc["id"],
                doc_title=doc["title"],
                heading=section["heading"],
                text=piece,
                embed_text=f"{doc['title']} | {section['heading']}\n{piece}",
                metadata={
                    "source_id": doc["id"],
                    "doc_title": doc["title"],
                    "heading": section["heading"],
                    "url": doc["url"],
                    "licence": doc["licence"],
                    "attribution": doc["attribution"],
                    "date_accessed": doc["date_accessed"],
                    "section_index": s_idx,
                    "piece_index": p_idx,
                    "n_words": len(piece.split()),
                },
            ))
    return chunks


def load_processed_docs(processed_dir):
    """Read every data/processed/*.json file produced by ingestion."""
    paths = sorted(Path(processed_dir).glob("*.json"))
    if not paths:
        raise FileNotFoundError(
            f"No processed documents in {processed_dir}. Run: python -m src.ingest.run_ingest")
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def chunk_all(docs, target=CHUNK_TARGET_WORDS, overlap=CHUNK_OVERLAP_WORDS):
    chunks = []
    for doc in docs:
        chunks.extend(chunk_document(doc, target, overlap))
    return chunks
