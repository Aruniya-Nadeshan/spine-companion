# Decisions

A short record of each design choice: what was decided, why, what else was considered, and when to revisit it. Newest entries are at the bottom.

---

## 2026-11-19: Defer the NHS as a source

**Decision:** The NHS website is not ingested in v1.
**Why:** The NHS terms allow reuse of unchanged content with attribution and a copy date or regular refresh. Adapted content (any change to wording that alters its meaning or impact) must instead carry a generic Open Government Licence notice, and may not be attributed to the NHS. A RAG chatbot paraphrases retrieved text, which counts as adaptation, and this project's purpose is to cite its sources.
**Alternatives considered:** Ingest anyway and cite the NHS (breaches the terms); show NHS passages verbatim with date and attribution, separate from the generated answer (possible, but extra design work).
**Revisit when:** A verbatim-passage display mode exists, or v1 is working and more sources are needed.

## 2026-11-19: Raw and processed data stay out of git

**Decision:** `data/raw/` and `data/processed/` are git-ignored. The repo holds the recipe: `sources.csv` plus the ingestion code.
**Why:** A public repo containing full copies of other organisations' text is redistribution, and it would carry each source's attribution and refresh conditions with it. Anyone can regenerate the data by running the pipeline.
**Revisit when:** Reproducibility needs a frozen snapshot (e.g. for a paper), which would need a licence check per source.

## 2026-11-19: Link-only and excluded sources

**Decision:** AAOS OrthoInfo and the Scoliosis Research Society are link-only. Boston Children's Hospital is not ingested. The NIAMS "Research & Resources" tab is not ingested.
**Why:** AAOS forbids replicating its material. SRS holds the copyright and no open licence was found. No reuse licence was found for Boston Children's. The NIAMS research tab is mostly research progress and links, so it has little value for patients.
**Revisit when:** Written permission is obtained from AAOS or SRS (a good milestone to pursue).

## 2026-11-19: Fetch SOSORT through the Europe PMC API, not by scraping PubMed Central

**Decision:** The SOSORT 2016 guidelines are downloaded as JATS XML from Europe PMC's full-text endpoint. `sources.csv` has a `fetch_url` column (where the code downloads from) and a `format` column (`html` or `jats-xml`). `url` stays as the human-readable link used in citations.
**Why:** The first attempt, fetching the PMC article page, was blocked by robots.txt, and the pipeline correctly refused to continue. The article is CC BY 4.0, and Europe PMC offers a documented route for programmatic access to open-access full text. Structured XML is also easier to parse reliably than a web page.
**Alternatives considered:** Saving the page manually in a browser and using `--skip-fetch` (quick, but not reproducible).
**Revisit when:** The endpoint changes, or another open-access article needs the same route.

## 2026-11-19: robots.txt is checked for web pages but not for official APIs

**Decision:** For `html` sources the fetcher checks robots.txt and stops if fetching is disallowed. For `jats-xml` sources (official APIs) it does not.
**Why:** robots.txt expresses a site owner's wishes about crawlers visiting web pages. An API documented for programmatic access is a different channel. Ignoring robots.txt on a normal website would be impolite and could breach its terms.
**Revisit when:** A new source type is added, since each one needs this question asked again.

## 2026-11-19: Stop on the first ingestion failure

**Decision:** If any source fails to download or fails the quality check, the run stops and writes nothing for that source.
**Why:** A partly empty corpus silently changes what the chatbot can answer, and it would later look like the bot "doesn't know" rather than "was never given the information". Failing loudly is cheap because a rerun takes seconds.
**Alternatives considered:** Skip the failure and report at the end.
**Revisit when:** The corpus is large enough that one flaky source should not block the others.

## 2026-11-19: Attribution and licence travel with every processed document

**Decision:** Each `data/processed/<id>.json` stores the source id, URL, licence, attribution text and access date alongside the text.
**Why:** Attribution is a licence requirement, and keeping it attached to the text means it cannot be lost in later steps. Chunks will inherit it as metadata, so citations can show it automatically.

## 2026-11-19: Downloads retry on transient failures, with a longer timeout

**Decision:** A 10-second connect timeout and a 120-second read timeout, up to 3 attempts with a growing pause. Timeouts, connection errors and server errors (5xx) are retried. Client errors (4xx) are not.
**Why:** The first Europe PMC request timed out at 30 seconds because the full-text XML is large. Retrying a 404 would not change the answer and would only add load to someone else's server.

## 2026-11-19: Remove navigation lists at the list level

**Decision:** The HTML extractor deletes any list with 2+ items where at least half are pure links and every item is short.
**Why:** The NIAMS page tabs sat in an ordinary list, and the currently selected tab is plain text, not a link, so a per-item rule missed it. The tab labels were being indexed as content. Ordinary bullet lists (such as the causes of scoliosis) have no links, so they are never treated as navigation, and a test protects that.
**Revisit when:** A new source's menus slip through, which the per-document section listing should reveal.

## 2026-11-19: v1 targets children, teens and their caregivers

**Decision:** v1 covers scoliosis in children and teens, and says so. Adult scoliosis is out of scope.
**Why:** Every v1 source is written for children, teens or scoliosis during growth. Applying that guidance to adults would be unsupported and could mislead. The bot should decline adult-specific questions and point to the care team, and the evaluation set includes such questions.
**Revisit when:** Openly licensed, adult-focused sources are found and licence-checked (a v2 goal).

## 2026-11-19: Be honest about thin coverage of everyday-life topics

**Decision:** "Living with scoliosis" stays in v1 only as far as the sources support it: exercise and activity, coping with a brace, and support groups. School, sleep, body image and emotional wellbeing are listed as known gaps.
**Why:** Answering from sources the bot doesn't have would break the core rule (answer only from retrieved, vetted text). A truthful "I don't have information on that" is a feature, and it also marks the next research question: finding good sources for these topics.

## 2026-11-19: AI-assisted workflow with an explain-back rule

**Decision:** The owner writes the specification and makes the design decisions. AI tools draft code, tests and documents in small diffs. Nothing is committed until the owner can explain it in her own words, and `AGENTS.md` records the project rules for any AI assistant.
**Why:** It saves time while keeping the owner able to change the project without help. Tests act as the safeguard against trusting output that hasn't been verified.

---

## 2026-11-21: Python 3.11 for the project environment

**Decision:** The project environment uses Python 3.11.
**Why:** The retrieval dependencies (PyTorch, ChromaDB) lag behind the newest Python releases, and ChromaDB had a reported incompatibility with Python 3.14. Python 3.12 was not installed; 3.11 was, and is widely supported across ML libraries.
**Revisit when:** The dependencies officially support the newer versions.

## 2026-11-21: Retrieval baseline settings

**Decision:** Embeddings come from `BAAI/bge-small-en-v1.5` (free, runs locally on a CPU). Vectors are stored in a local ChromaDB collection and compared by cosine similarity. Chunks are about 250 words with 40 words of overlap, split on sentence boundaries. A section that already fits in about one chunk stays whole. Search returns the top 5. Questions get the instruction prefix the bge model expects. Every value lives in `src/rag/config.py`.
**Why:** It is a small, free, well-known setup that I can run and explain. It is a baseline, not a final answer.
**Alternatives considered:** `all-MiniLM-L6-v2` (older, also free); other chunk sizes.
**Revisit when:** Phase 4, with the evaluation set deciding between alternatives.

## 2026-11-21: Build and verify retrieval before adding the language model

**Decision:** Retrieval is built and checked on its own first. Answer generation comes after.
**Why:** Most RAG failures start in retrieval. If a language model writes fluent answers over bad passages, the faults are hidden. Testing retrieval alone makes them visible.

## 2026-11-21: Merge chunks under 40 words into a neighbour, keeping their heading

**Decision:** A chunk under 40 words is merged into the previous chunk (or the next one, at the start of a document), prefixed with its own heading, and never beyond 350 words in total.
**Why:** Tiny chunks (the first index had one of 8 words) give weak, noisy matches. Keeping the heading label means nothing is lost.
**Result:** 155 chunks became 142, with a smallest chunk of 40 words.

## 2026-11-21: Drop publisher boilerplate sections

**Decision:** Sections such as Electronic supplementary material, Authors' contributions, Availability of data and materials and About this article are excluded, matching straight and curly apostrophes alike.
**Why:** They contain no scoliosis knowledge and would only add noise to the index.

## 2026-11-21: Fix glued text at its source, in the JATS extractor

**Context:** Words were running together in the SOSORT text (for example `dysfunctionTo`, `MethodologyBackground`, `following:Methodology`). My first two guesses were wrong: the publisher XML did contain some glued words, but the extractor was not dropping spaces, and there were no hidden characters (a character report showed only ordinary typography). A report of rare words then showed the real pattern: bullets and subheadings were being joined without spacing.
**Decision:** The extractor now treats block elements (paragraphs, lists, list items, titles, boxes) as boundaries and pads them with spaces, turns each bullet into its own paragraph, and avoids duplicating nested lists. Inline formatting such as italics adds no space.
**Why:** The fault was in my extractor. Repairing symptoms afterwards could never be reliable.

## 2026-11-21: Keep a conservative repair step as a safety net

**Decision:** After extraction, a repair step splits glued words only under strict rules: the word is not in an English dictionary (`pyspellchecker`); its parts are words the document itself uses often; it is rare compared with its parts; words under 7 letters are split only into common function words; common prefixes (non, anti, pre...) are respected; acronyms and parts of web addresses are never touched; and a second rule splits at a capital letter only when both sides are real words and the token is not a known name (a keep-list covers PubMed, ScoliScore, SpineCor and similar). Every repair is recorded in the document's JSON and can be printed.
**Why:** This is medical text, so an aggressive spell-checker could damage clinical terms. Logging every change makes the step auditable, and the attribution already states that changes were made.
**Result:** One repair on SOSORT (`fulltime` to `full time`). The remaining capital-in-the-middle tokens are all real names or abbreviations (BrAIST, McMaster, ScoliScore, SpineCor, HRQoL and similar). A web address (`scoliosisjournal.com`) is left intact.
**Revisit when:** A new source is added; run `python -m src.ingest.glue_report --camel` and `--rare` on it first.

## 2026-11-21: The smoke test is a sanity check, not an evaluation

**Decision:** `src.rag.smoke` only checks that a few obvious questions return a hit from an acceptable source. Phase 3 will check specific passages.
**Why:** It passed "When is a brace needed?" even though the top five results were SOSORT recommendations about who builds and checks braces, which does not answer a patient's question. Two causes are suspected: SOSORT has 133 chunks against 9 for NIAMS, and SOSORT is written for clinicians. This is recorded as a known issue to measure in Phase 3 and address in Phase 4 (for example with a reranker or source weighting).

---

## 2026-11-21: Evaluate with source-and-phrase evidence labels and a hash-based dev/test split

**Decision:** Each in-scope question lists evidence as a source plus a short phrase copied from the text. A retrieved chunk is correct if it comes from that source and contains the phrase. The dev/test split is decided by a hash of the question id (about 30% test), so nobody can choose it after seeing results. Later question sets get a `batch` number so a set that never influenced earlier choices can be kept for checking them.
**Why:** Labels by chunk id break whenever chunking changes. A split chosen by hand can be bent towards the results. Batches make it possible to ask whether a choice generalises.
**Result:** 107 questions (75 in-scope, 22 out-of-scope, 10 safety) in three batches.

## 2026-11-21: Audit labels by reading everything retrieved, not only failures

**Decision:** When a "failure" might be a valid answer we did not label, review all retrieved chunks for all questions of a split, add extra evidence only where a passage clearly answers the question, note why, and then re-run the baseline. A label fix is not an improvement, so later experiments compare with the re-run baseline.
**Why:** Fixing only the failures biases the score upwards. Six batch-1 questions gained valid extra evidence this way.
**Known limitation:** batch 2 and batch 3 labels were never audited, which probably understates every system's score on them.

## 2026-11-22: Write predictions and decision rules before running an experiment

**Decision:** Every experiment has a prediction and what would show it wrong, recorded in `docs/experiments.md` before it runs. The one adoption rule used (for H4) was fixed in advance: adopt only if at least 4 more questions improve than worsen and no more than 2 worsen.
**Why:** A prediction made after the result can always be bent to fit it. Several predictions were wrong (H1, H3, H5, H9), which is how I learned from them.

## 2026-11-23: Retrieval has two candidates; the final pick waits for end-to-end results

**Decision:** Keep two retrieval pipelines: the baseline (vector search, about 18 ms) and Design A (BM25 fusion and a cross-encoder reranker over 20 candidates, about 0.8 s). Choose between them using answer quality once generation exists.
**Why:** Design A improved recall in the top 5 on every question set (test: 0.77 to 0.89) and 15 questions against 2 on dev, but on the independent test split it did not improve ranking (6 better, 8 worse, hit@1 0.46 to 0.35). The differences are inside the noise of 26 questions. The generator will read several chunks, so recall may matter more than rank 1, but that must be measured.
**What was rejected:** ~120-word chunks (worse), small-to-big with 60-word children (7 regressions), bge-base embeddings (net +2, below the +4 rule), dropping the document title from the embedded text (small effects, not adopted).

## 2026-11-23: The test split is spent

**Decision:** The test split was used once for the baseline and once for Design A. It is not used again to choose between designs. New confirmation needs new questions.
**Why:** Each extra look makes a test set less independent. (It was run slightly before the planned go-ahead, but the design it tested was already the one the pre-registered H4 rule selected, so no selection decision depended on it.)

## 2026-11-23: A similarity score cannot decide whether to answer

**Decision:** Do not rely on a similarity cut-off for "I don't know", refusals or safety. Off-topic questions score 0.41 to 0.64, the weakest answerable questions 0.63 to 0.65, and personalised-advice, red-flag and injection questions score like answerable ones. Phase 5 needs explicit detection for those.
**Why:** The score distributions overlap, and a cut-off at the best dev value already rejects an answerable question.

## 2026-11-23: Make console output safe on Windows

**Decision:** Tools that print source text replace characters the console cannot show instead of crashing, and `audit` can write a UTF-8 file.
**Why:** Printing "≥" crashed a report on the cp1252 console.
