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
- **OGL (Open Government Licence):** the UK licence under which the NHS makes content reusable, with conditions.

---

## Not built yet (so I do not overclaim)

Chunking, embeddings and the vector index; retrieval; answer generation; the evaluation set and metrics; safety behaviours and the red-team set; the API and web interface; deployment and CI. The ingestion pipeline and the scope and licence work are the only finished parts.

## Open questions to revisit

- Which openly licensed sources cover adult scoliosis and everyday-life topics?
- Can a clinician or physiotherapist review the red-flag list?
- How do I keep answers from clinician-oriented sources in plain language without changing their meaning?
