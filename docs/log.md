# Learning log

**How to use this file.** Each entry says what was built, what I learned, and the explain-back answers: my answers to "can I explain this without looking at the code?". These answers were first drafted with AI help. Before using any of it in an interview or on a CV, I restate it in my own words and check that I understand it. Only things I have built and can explain go on a CV.

---

## Entry 1: Project setup and scope (2026-11-19)

**What I did**
- Created the `spine-companion` repo with a README that states the purpose and a "not medical advice" line.
- Wrote `docs/scope.md`: problem, users, goals and non-goals, expected behaviours, success metrics, risks, milestones and open questions.
- Checked the licence terms of six candidate sources before collecting any data, and recorded the result in `data/sources.csv`.

**What I learned**
- A health chatbot needs a written list of what it will *not* do before it needs any code.
- Licence checking comes first. Of six sources, only two (NIAMS text, SOSORT guidelines) could be copied and indexed as they stand. That changed the whole data plan.
- Metrics with targets can be written before any code exists. They are hypotheses to be revised after the first measurement.

---

## Entry 2: Ingestion pipeline (2026-11-19)

**What I built:** a pipeline that reads `sources.csv`, downloads each `ingest` source, extracts the text and section headings, cleans it, checks its quality, and saves one JSON file per document with attribution attached.

**Results on the first real run:** SOSORT 73 sections and about 156,900 characters; NIAMS overview 4 sections and 2,769 characters; NIAMS diagnosis and treatment 4 sections and 4,189 characters.

**Explain-back answers**

*1. Why does the run stop on the first failure instead of skipping the broken source?*
If one source is skipped, the chatbot is built on a smaller knowledge base without anyone noticing. A missing source would then look like the bot "not knowing" something, my evaluation numbers would be misleading, and I would waste time debugging retrieval when the real fault was upstream. A rerun takes seconds, so failing loudly is cheap.

*2. Why is attribution stored inside each JSON file and not looked up later?*
The licences require credit (NIAMS asks for it, CC BY requires attribution, and the NHS terms were strict about it). If the attribution lives in a separate place, a later step can forget it. Keeping it with the text means every chunk can inherit it and every answer can show it.

*3. What happens if NIAMS redesigns its page and the extractor finds only a menu?*
The extractor would return very little text and few sections, the quality check (at least 2,000 characters and 3 sections) would fail, and the run would stop without writing a file. The limit is a minimum, not proof of correctness: a redesign that still produced enough boilerplate could pass, which is why I also compare the output with the real page by eye.

*4. What does `EXCLUDED_HEADINGS` do, and why would references hurt retrieval?*
It drops sections like References, Acknowledgements and Funding. A reference list is author names, journal titles and years. In a search index it would produce passages that match queries badly, take up space, and could be retrieved as if they were answers.

---

## Entry 3: Reaching the SOSORT guidelines (2026-11-19)

**What happened:** the first attempt to download the article from PubMed Central was refused by robots.txt. The pipeline stopped with a clear error instead of scraping anyway. I switched to Europe PMC's full-text API, added `fetch_url` and `format` columns to `sources.csv`, and wrote a second extractor for JATS XML (the article format).

**Explain-back answers**

*1. Why is `url` kept separate from `fetch_url`?*
`url` is the page a person can open, and it is what citations should point to. `fetch_url` is the machine endpoint the code downloads from. For SOSORT they are different, so one column could not serve both purposes.

*2. Why does the XML route skip the robots.txt check, and why would skipping it be wrong for a normal website?*
robots.txt is a site owner's instruction to crawlers about web pages. An official API is documented for programmatic use, which is a different channel. A normal website has not offered that, so ignoring its robots.txt would be impolite and could breach its terms. The decision lives in `docs/decisions.md` so it can be questioned later.

*3. Why are citation markers like `[12]` removed before embedding?*
They carry no meaning on their own, they add noise to the text the model embeds, and they could end up in answers. The reference list they point to is also removed, so the numbers would point nowhere.

---

## Entry 4: Reliability and real-world findings (2026-11-19)

**What happened**
- The Europe PMC download timed out at 30 seconds. I added a 120-second read timeout and up to 3 attempts for transient failures.
- Comparing the NIAMS output with a PDF of the live page showed that the extracted text was accurate but that page tab labels were being indexed as content. I fixed it by removing navigation lists.
- The comparison also showed that the NIAMS page has three tabs. The URL I started with covered only the first, so I added the Diagnosis and Treatment page as a second source.
- Both NIAMS pages and the SOSORT guidelines address children, teens or scoliosis during growth, so v1 does not cover adults.

**Explain-back answers**

*Why not retry a 404?*
A 404 is a client error: asking again will not change the answer, and it only adds load to someone else's server. Timeouts, connection errors and 5xx server errors are temporary, so those are retried.

*Why detect navigation at the list level, not per item?*
The selected tab was plain text, not a link, so a rule that checked each item for being a link missed it. Checking the whole list (at least half the items are links and all items are short) catches menus while leaving real bullet lists alone. A test proves a list like "Genes / Hormones / Changes in cell structure" is never dropped.

**What I learned**
- Passing a quality check does not mean extraction is right. Comparing the output with the real page found things the check could not.
- A source can look complete and be only part of the content (the NIAMS tabs).
- A corpus has a *population* as well as a topic. Here it is children and teens, which affects who the bot can safely help.

---

## Entry 5: Retrieval baseline (2026-11-20)

**What I built:** a chunker, an embedding wrapper (bge-small), a ChromaDB index and a search command. The first index had 155 chunks (SOSORT 146, NIAMS 9), a median of 214 words and a smallest chunk of 8 words. After merging small chunks it has 142 chunks with a minimum of 40 words. `python -m src.rag.search "what is a Cobb angle"` returns relevant passages with attribution, and the six smoke questions all passed.

**What the results taught me**
- "What is a Cobb angle?" found good passages. "When is a brace needed?" did not: the top five were SOSORT recommendations about who builds and checks braces. The smoke test still said PASS because it only checked which source a hit came from.
- Two likely causes: the corpus is lopsided (SOSORT has far more chunks than NIAMS), and SOSORT is written for clinicians while a patient's question is in plain language. I will measure this properly in Phase 3 before changing anything.

**Explain-back answers**

*1. Why do chunks overlap, and what could go wrong if they didn't?*
A thought can be cut in half at a chunk boundary. Repeating the last sentences of one chunk at the start of the next means an idea that straddles the boundary still appears whole in at least one chunk. Without overlap, a question could match neither half well, and the answer could be lost.

*2. Why does the embedding text include the title and heading, while the text shown to the user does not?*
The heading tells the embedding model what the passage is about (a paragraph that says "it is recommended" means little alone), which improves matching. The user and the language model read the plain passage, so nothing extra clutters the answer, and the heading is still shown separately as the source label.

*3. Why does `build_index` delete and recreate the collection each time?*
So rebuilding is repeatable and cannot leave duplicates or stale chunks from an older version of the data. The index is derived data: the processed files are the truth.

*4. Why test the plumbing with a fake embedder and not the real model?*
The real model needs a large download and is slow, and its results can change between versions. The fake one is instant and deterministic, so the tests check what I wrote (chunking, storing, searching, metadata) and not the model. The real model is checked separately with the smoke test.

*5. Why did the smoke test pass the brace question when the results were poor?*
I wrote it to check only the source of each hit, and SOSORT was on the allowed list. A passing check proves only what it tests. The Phase 3 evaluation checks for specific expected passages, and answer quality too.

---

## Entry 6: Finding the cause of glued words (2026-11-20 to 11-21)

**What happened:** words in the SOSORT text were running together (`experienceand`, `theCobb`, `dysfunctionTo`). I first assumed my extractor dropped spaces, then that hidden characters were involved. Both guesses were wrong. Diagnostic reports showed the real pattern: bullets and subheadings inside paragraphs were joined with no spacing, because the extractor concatenated element text without boundaries. I fixed the extractor, kept a cautious repair step as a safety net, and checked the result on the real data.

**Result:** one repair left on SOSORT (`fulltime` to `full time`), no hidden characters, and the 20 words with a capital in the middle are all real names or abbreviations. A web address was left intact. "the Cobb" now appears 22 times and "theCobb" 0 times.

**Explain-back answers**

*1. Why is fixing a problem at its cause better than repairing its symptoms afterwards?*
A repair step has to guess what the text should have been, so it can be wrong, and it needs more rules every time a new case appears. Fixing the extractor removes the problem for all text, including cases I have not seen yet. The repair step is kept only as a cautious net.

*2. Why can't a repair rule rely only on how rare a word is?*
Rarity does not separate glue from real words. A rare real word (a medical term, a name) looks the same as a glued one, and glue that repeats often (a systematic fault) is not rare at all. So the rule also checks a dictionary, whether the parts are common in the document, and how the word compares with its parts.

*3. What does the dictionary check protect?*
Real English words that happen to be two shorter words joined, such as "thereby" or "sometimes". If one appears rarely, a rarity-only rule would split it wrongly.

*4. Why does the repair step skip web addresses?*
Splitting `scoliosisjournal` inside `http://www.scoliosisjournal.com` would break the address. A repair should never change something it cannot be sure is prose.

*5. Why did the first diagnostic report say nothing was wrong while the problem was visible in search results?*
That report could only list words it could cut into parts the document used often, so it was blind to the rest. A diagnostic only shows what its rules can see. When a report and the real data disagree, check the data directly (for example by counting an exact string), and add a view that does not depend on the same assumptions (the `--chars`, `--rare` and `--camel` reports).

**What I learned:** my first two explanations were guesses, and measuring with real data beat both. Passing tests on made-up examples did not mean the real text was fine.

---

## Entry 7: Building the evaluation (2026-11-21 to 11-22)

**What I did:** wrote `docs/eval-plan.md`; built a question file (107 questions in three batches) with evidence labels; wrote tools to validate labels, run retrieval, audit labels, view per-question results and compare runs; ran a baseline, audited labels, and measured.

**What I learned**
- "Looks fine on the questions I try" was wrong: the first smoke test passed a question whose results were poor.
- Some "failures" were incomplete labels. Judging everything retrieved, not only failures, gave a fairer score.
- A bigger average hides what changed; comparing question by question (better, worse, same) is more informative at this size.

**Explain-back answers**

*1. Why label evidence as a source plus a phrase and not by chunk id?*
Chunk ids change whenever chunk size or splitting changes. A phrase from the source stays valid, so the same labels can judge every variant.

*2. Why is the dev/test split decided by a hash of the question id?*
So nobody, including me, can move a question between splits after seeing which way it helps. Tuning on dev and reporting on test only works if that choice is not influenced by the results.

*3. Why does the report show a confidence interval?*
With 20 to 50 questions the measured rate could easily be several points away from the true one. The interval shows how far, and a difference smaller than it is not evidence.

*4. Why must questions be written before looking at what retrieval returns?*
Otherwise the set drifts towards what already works and flatters the system.

*5. Why can't a similarity score reject a question such as "my curve is 38 degrees, should I have surgery?"*
That question is about scoliosis, so it scores like the answerable ones. Refusing it needs a rule about what the bot may not do, not a measure of how close the text is.

*6. Why audit all retrieved chunks and not only the failures?*
Fixing only failures can only raise the score. Judging every result by one standard is fair, and each change is written down.

*7. Why isn't a label fix an improvement?*
The system did not change; only the ruler did. Scores rose from 0.545 to 0.86 hit@5 on dev from the audit alone, which is why later experiments compare with the re-run baseline.

---

## Entry 8: Experiments and what they taught me (2026-11-21 to 11-23)

**What I tested:** removing the document title or heading from the embedded text (H1, H2), smaller chunks (H3), a larger embedding model (H4), keyword plus vector search (H5), a cross-encoder reranker (H6), both together (H8, "Design A"), and small-to-big child chunks (H9). Each had a written prediction. Full table in `docs/experiments.md`.

**Headline results**
- On dev, Design A (hybrid + rerank) improved 15 questions and worsened 2 against the baseline (p=0.002; hit@5 0.735 to 0.857).
- On a fresh batch it moved the same way but less (hit@5 0.50 to 0.58, 12 questions).
- On the independent test split it did not improve the ranking (6 better, 8 worse; hit@1 0.46 to 0.35), though hit@5 rose from 0.77 to 0.89 (3 questions of 26).
- Smaller chunks, small-to-big and a larger embedding model did not clear my bar.
- Several of my predictions were wrong, including the cause of the q018 failure and whether keyword search could fix q005.

**What this means:** retrieval is decent but not as good as the dev numbers suggested, and I cannot show that Design A is better than the plain baseline beyond doubt. The decision between them will use answer quality.

**Explain-back answers**

*1. Why write predictions and decision rules before running an experiment?*
A prediction made afterwards can always be explained away. Writing it first lets me see where my understanding was wrong. The H4 rule stopped me adopting a change that looked tempting.

*2. Why did Design A look much better on dev than on test?*
I chose it after looking at dev failures, and I ran about ten comparisons on dev, so some wins were luck and some were fitting to those questions. The test split had never influenced anything.

*3. Why compare experiments question by question?*
An average can move because of one or two questions. Counting how many got better, worse or stayed the same, with a sign test, shows whether the change is consistent.

*4. Why can a reranker only improve results among its candidates?*
It reorders what the first stage found. If the right passage is not in the top 20, it cannot appear.

*5. Why does reciprocal rank fusion combine rankings and not raw scores?*
Cosine similarity and BM25 scores are on different scales, so adding them is meaningless. Ranks are comparable.

*6. Why did q065 and q066 fail although the answer is in the corpus?*
The answer is one sentence inside a long mixed passage, and the question is short. The passage as a whole is about something broader, so it does not look close to the question.

*7. Why can absolute dev numbers not be quoted as the system's performance?*
Dev questions influenced the design. Only questions the design never saw, such as the test split, give an honest estimate, and even those carry wide intervals with a few dozen questions.

---

## Known issues

- "When is a brace needed?" is a regression case: it worsened under Design A on the test split (rank 1 to 4).
- Facts buried in long mixed passages are still often missed (q065 surgery rates, q090 leg length, q091 the 10 degree threshold).
- Labels for batch 2 and batch 3 were never audited, so measured scores on them are probably too low.
- Dev and test sets are small (49 and 26 in-scope questions), so every difference is uncertain.
- The corpus is lopsided: SOSORT has 133 chunks, the two NIAMS pages 9.
- The sources cover children and teens only; there is no adult scoliosis content and little on everyday-life topics.
- Some oddities are spelled that way in the source and are left as written (for example `informations`, `olysthesis`).

---

## Glossary

- **RAG (retrieval-augmented generation):** the chatbot first retrieves relevant passages from a trusted collection, then writes its answer from those passages instead of from memory.
- **Ingestion:** turning source documents into clean, labelled text ready for the system to use.
- **Chunk:** a piece of a document (a few paragraphs) that is embedded and retrieved on its own.
- **Embedding:** a list of numbers that represents the meaning of a piece of text, so similar texts can be found by comparing numbers.
- **Vector database (ChromaDB):** a store that finds the chunks whose embeddings are closest to a question's embedding.
- **Hit-rate@k:** the share of test questions where the correct passage appears among the top k results.
- **Faithfulness:** whether an answer is supported by the passages it was built from.
- **JATS:** the XML format used by PubMed Central and Europe PMC for journal articles.
- **robots.txt:** a file where a website tells automated programs which pages they may fetch.
- **CC BY 4.0:** a Creative Commons licence allowing reuse with credit, a link to the licence and a note of any changes.
- **Public domain:** material with no copyright restrictions. NIAMS text is public domain; its images may not be.
- **Cosine similarity:** a score for how close two embeddings are in meaning (1.0 is identical, higher is better). It is what ranks the search results.
- **Top-k:** the number of best-matching passages returned by a search (5 here).
- **Chunk overlap:** the words repeated between neighbouring chunks so ideas are not cut at a boundary.
- **Block versus inline XML elements:** block elements (paragraphs, list items, titles) start and end a piece of text and need a space around them; inline elements (italics, links) sit inside a sentence and add none.
- **Dictionary guard:** a check that a word is not already ordinary English before the repair step is allowed to split it.
- **hit@k / MRR:** hit@k is the share of questions whose correct passage is in the top k results; MRR is the average of 1 divided by the rank of the first correct passage.
- **Sign test:** compares how many questions improved with how many got worse and asks how likely that split is if the change did nothing.
- **Pre-registration:** writing the prediction and the decision rule before running an experiment.
- **BM25 / hybrid search:** a classic keyword ranking function, combined with vector search by merging the two rankings.
- **Cross-encoder reranker:** a model that reads the question and a passage together and scores how well it answers, used to reorder a short list of candidates.
- **Small-to-big retrieval:** match on small chunks but return the larger passage they came from.
- **OGL (Open Government Licence):** the UK licence under which the NHS makes content reusable, with conditions.

---

## Not built yet (so I do not overclaim)

Answer generation and its evaluation (faithfulness, citation correctness); safety behaviours and the red-team set; the API and web interface; deployment and CI. Finished so far: the scope and licence work, ingestion, a retrieval system with two pipelines (plain vector search, and hybrid search with a reranker), and a retrieval evaluation (107 questions, dev/test splits, experiment log) that shows retrieval works for most questions but that the better pipeline is not yet proven.

## Open questions to revisit

- Which openly licensed sources cover adult scoliosis and everyday-life topics?
- Can a clinician or physiotherapist review the red-flag list?
- How do I keep answers from clinician-oriented sources in plain language without changing their meaning?
