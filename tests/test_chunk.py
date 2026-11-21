from src.rag.chunk import chunk_all, chunk_document, merge_small_chunks, split_sentences, split_text

LONG_SENTENCES = [f"Sentence number {i} talks about bracing for scoliosis in growing teenagers." for i in range(60)]


def make_doc(sections):
    return {"id": "demo", "title": "Demo guide", "publisher": "Pub", "url": "https://example.org/demo",
            "licence": "CC BY 4.0", "attribution": "Credit demo", "date_accessed": "2026-11-19",
            "sections": sections}


def test_split_sentences_basic():
    assert split_sentences("First one. Second one! Third?") == ["First one.", "Second one!", "Third?"]


def test_small_section_stays_one_chunk_with_paragraphs():
    doc = make_doc([{"heading": "Causes", "paragraphs": ["Genes.", "Hormones."]}])
    (chunk,) = chunk_document(doc, min_words=0)
    assert chunk.text == "Genes.\nHormones."
    assert chunk.heading == "Causes"


def test_long_section_is_split_into_several_chunks_near_target_size():
    doc = make_doc([{"heading": "Bracing", "paragraphs": [" ".join(LONG_SENTENCES)]}])
    chunks = chunk_document(doc, target=100, overlap=20)
    assert len(chunks) > 3
    assert all(c.n_words <= 100 + 15 for c in chunks)  # target plus at most one sentence


def test_consecutive_chunks_overlap():
    chunks = split_text(" ".join(LONG_SENTENCES), target=100, overlap=30)
    assert len(chunks) > 2
    for before, after in zip(chunks, chunks[1:]):
        last_sentence = split_sentences(before)[-1]
        assert last_sentence in after  # the end of one chunk reappears at the start of the next


def test_no_duplicate_tail_chunk():
    chunks = split_text(" ".join(LONG_SENTENCES), target=100, overlap=30)
    assert len(chunks) == len(set(chunks))
    # the final chunk must contain at least one sentence that is not in the previous chunk
    assert split_sentences(chunks[-1])[-1] not in chunks[-2]


def test_every_sentence_appears_in_some_chunk():
    chunks = split_text(" ".join(LONG_SENTENCES), target=100, overlap=30)
    joined = " ".join(chunks)
    assert all(s in joined for s in LONG_SENTENCES)


def test_chunks_carry_source_metadata_and_unique_ids():
    doc = make_doc([{"heading": "A", "paragraphs": ["One."]},
                    {"heading": "B", "paragraphs": [" ".join(LONG_SENTENCES)]}])
    chunks = chunk_all([doc], target=100, overlap=20)
    assert len({c.id for c in chunks}) == len(chunks)
    for c in chunks:
        assert c.metadata["attribution"] == "Credit demo"
        assert c.metadata["licence"] == "CC BY 4.0"
        assert c.metadata["source_id"] == "demo"
        assert c.metadata["url"] == "https://example.org/demo"


def test_embed_text_includes_title_and_heading_but_text_does_not():
    doc = make_doc([{"heading": "Symptoms", "paragraphs": ["Uneven shoulders."]}])
    (chunk,) = chunk_document(doc)
    assert "Demo guide" in chunk.embed_text and "Symptoms" in chunk.embed_text
    assert chunk.text == "Uneven shoulders."


def test_sections_without_text_produce_no_chunks():
    doc = make_doc([{"heading": "Empty", "paragraphs": ["  "]}])
    assert chunk_document(doc) == []


def words(n, word="alpha"):
    return " ".join([f"{word}"] * n) + "."


def test_small_chunk_is_merged_into_the_previous_one_with_its_heading():
    doc = make_doc([{"heading": "Big", "paragraphs": [words(100)]},
                    {"heading": "Tiny", "paragraphs": ["Short note."]}])
    (chunk,) = chunk_document(doc, min_words=40)
    assert chunk.heading == "Big"
    assert "Tiny: Short note." in chunk.text
    assert chunk.metadata["merged_headings"] == "Tiny"
    assert chunk.metadata["n_words"] == chunk.n_words


def test_small_first_chunk_is_folded_into_the_next_one():
    doc = make_doc([{"heading": "Tiny", "paragraphs": ["Short note."]},
                    {"heading": "Big", "paragraphs": [words(100)]}])
    (chunk,) = chunk_document(doc, min_words=40)
    assert chunk.heading == "Big"
    assert chunk.text.startswith("Tiny: Short note.")


def test_chunks_at_or_above_the_minimum_are_not_merged():
    doc = make_doc([{"heading": "A", "paragraphs": [words(60)]},
                    {"heading": "B", "paragraphs": [words(45)]}])
    assert len(chunk_document(doc, min_words=40)) == 2


def test_merge_never_creates_a_chunk_larger_than_the_limit():
    doc = make_doc([{"heading": "A", "paragraphs": [words(120)]},
                    {"heading": "B", "paragraphs": ["Tiny."]}])
    unmerged = chunk_document(doc, min_words=0)
    chunks = merge_small_chunks(unmerged, min_words=40, max_words=100)
    assert len(chunks) == 2  # 120 + 1 words would exceed the limit of 100, so no merge
