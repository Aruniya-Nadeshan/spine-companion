"""Settings for the retrieval pipeline. Change them here, not inside the code.

Every value is a starting point: Phase 4 compares alternatives against the
evaluation set and records the results in docs/decisions.md.
"""
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
# bge models work better when short questions get this instruction in front.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

CHUNK_TARGET_WORDS = 250   # aim for chunks of about this many words
CHUNK_OVERLAP_WORDS = 40   # repeat roughly this many words between neighbours
MAX_WARN_WORDS = 350       # warn if a chunk is bigger (model reads ~512 tokens)
MIN_CHUNK_WORDS = 40       # chunks smaller than this are merged into a neighbour
MAX_MERGED_WORDS = 350     # never merge into a chunk that would exceed this size

PROCESSED_DIR = "data/processed"
INDEX_DIR = "data/index"
COLLECTION = "spine_companion"
TOP_K = 5
