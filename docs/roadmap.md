# Roadmap

Where the project stands and what is left. Tick a box only when the "done when" evidence exists, and update the date below each time.

**Last updated:** 2026-11-21

**Legend:** `[x]` done · `[~]` in progress (written but not yet verified here) · `[ ]` not started

**Rule for CVs and interviews:** a feature goes on a CV only when its box is ticked **and** its explain-back answers are written in `docs/log.md` in my own words. What is not built yet is listed at the bottom of `docs/log.md`.

---

## Snapshot

| Phase | Status |
|---|---|
| 0. Definition and licensing | Done |
| 1. Ingestion | Done |
| 2. Retrieval baseline | Done (works; known weakness on plain-language treatment questions) |
| 2b. Answer generation | Not started |
| 3. Evaluation | Not started |
| 4. Retrieval improvements | Not started |
| 5. Safety | Not started |
| 6. Product layer | Not started |
| 7. Ship it | Not started |
| 8. Research extension | Not started |

---

## Phase 0: Definition and licensing

- [x] Repo created, README states the purpose and "not medical advice"
- [x] `docs/scope.md` written (v1.1: problem, users, goals, non-goals, behaviours, metrics, risks)
- [x] Licence terms checked for six candidate sources
- [x] `data/sources.csv` records licence, attribution, fetch route, format and v1 use for every source
- [x] `docs/decisions.md` started (12 dated decisions so far)
- [x] `AGENTS.md` records the rules for AI assistants
- [x] `docs/log.md` started (learning log, explain-back answers, glossary)

**Result:** v1 corpus is NIAMS text (2 pages) and the SOSORT 2016 guidelines. NHS deferred. AAOS and SRS link-only. Boston Children's not ingested.

## Phase 1: Ingestion

- [x] Source loader that returns only `ingest` rows and rejects incomplete ones
- [x] Downloader with robots.txt check (web pages), retries, timeouts and a contact user-agent
- [x] HTML extractor with navigation-list removal and reference-section removal
- [x] JATS XML extractor for the Europe PMC route
- [x] Cleaning and a per-document quality check that stops the run on failure
- [x] Processed JSON per document with attribution attached
- [x] 90 tests passing
- [x] Corpus ingested: SOSORT 73 sections (~157,000 characters), NIAMS overview 4 sections, NIAMS diagnosis and treatment 4 sections
- [x] Text quality reviewed on the real data: glued words traced to their cause and fixed in the extractor, boilerplate sections dropped, diagnostics added (`glue_report`: `--chars`, `--rare`, `--camel`)
- [x] Conservative repair step with a dictionary guard; every repair logged

**Done when:** all three sources pass the quality check and I have looked at what each one produced. (Last item still open.)

## Phase 2: Retrieval baseline

- [x] Python 3.11 environment working
- [x] Chunker, embedder, ChromaDB index and search CLI written and tested
- [x] `python -m src.rag.build_index` runs on my machine (142 chunks, median about 220 words, minimum 40)
- [x] `python -m src.rag.search "..."` returns sensible passages with attribution (good on "what is a Cobb angle", weak on "when is a brace needed")
- [x] `python -m src.rag.smoke` reviewed (6 of 6 pass, but it only checks sources, so it is a sanity check, not an evaluation)
- [x] Small chunks merged; boilerplate sections excluded
- [x] Python-version and retrieval decisions recorded in `docs/decisions.md`
- [x] Phase 2 explain-back answers drafted in `docs/log.md` (restate them in my own words before interviews)
- [ ] Latest ingestion and glued-text fixes committed and pushed

**Done when:** I can ask five questions of my own on the command line and explain, for each, why the top result was chosen. (Known weakness to measure in Phase 3: plain-language treatment questions such as "when is a brace needed?" return clinician-oriented passages.)

## Phase 2b: Answer generation

- [ ] Decide the LLM route (hosted API or local model) and record it in `docs/decisions.md`
- [ ] Grounded prompt: answer only from retrieved passages, cite the source, supportive tone
- [ ] "I don't know" behaviour when retrieval is weak (threshold to be calibrated in Phase 3)
- [ ] Attribution shown with every cited source
- [ ] Chat command: `python -m src.rag.chat`
- [ ] Tests for the prompt builder and the refusal path, using a fake LLM

**Done when:** the bot answers a supported question with citations and says it doesn't know for an unsupported one.

## Phase 3: Evaluation (the most important phase for credibility)

- [ ] 30 in-scope questions, each with the expected source passage
- [ ] 10 out-of-scope questions (personalised advice, medication, adult scoliosis, off-topic)
- [ ] 10 safety questions (red-flag symptoms, distress)
- [ ] Metrics script: retrieval hit-rate@5 and MRR
- [ ] Answer metrics: faithfulness and citation correctness (automatic check plus manual review of a sample)
- [ ] Baseline results table saved in `docs/` and the results reproducible with one command
- [ ] Initial targets in `docs/scope.md` section 8 revised against the baseline

**Done when:** there is a results table I can reproduce and explain.

## Phase 4: Retrieval improvements (each change measured)

- [ ] Compare chunk sizes and overlaps
- [ ] Compare embedding models
- [ ] Hybrid search (keyword plus vectors)
- [ ] Cross-encoder reranker
- [ ] Each experiment logged with before-and-after numbers and a decision entry
- [ ] Only keep a change that has a measured benefit

**Done when:** the final configuration is justified by the evaluation set, not by habit.

## Phase 5: Safety

- [ ] Red-flag escalation (stops normal answering, advises contacting a clinician or emergency services)
- [ ] Refusals: diagnosis, personalised treatment, medication, adult scoliosis
- [ ] Emotional-distress handling with crisis resources
- [ ] Red-team question set (prompt injection, "ignore your rules", edge cases)
- [ ] Clinician or physiotherapist review of the red-flag list and a sample of answers (ask early)

**Done when:** red-flag escalation scores 1.00 and refusals score at least 0.95 on the test set.

## Phase 6: Product layer

- [ ] FastAPI backend with a `/ask` endpoint
- [ ] Simple web interface (Streamlit, Gradio or a small front end) with a visible disclaimer and scope statement
- [ ] Docker image that runs the whole app
- [ ] Logging that excludes anything personal; no accounts, no stored health data

**Done when:** someone else can run the app from the README.

## Phase 7: Ship it

- [ ] Public demo deployed (for example Hugging Face Spaces or Render)
- [ ] GitHub Actions running the tests on each push
- [ ] README rewritten as a case study: problem, architecture diagram, results table, limitations, what I would do next
- [ ] Licence check repeated before launch (these are readings of published terms, not legal advice)
- [ ] CV bullets written using only ticked, explained items, with real numbers

**Done when:** a recruiter can open the link, try it, and read the evidence.

## Phase 8: Research extension (after v1)

- [ ] Find and licence-check openly licensed sources for adult scoliosis and everyday-life topics (school, sleep, body image, emotional wellbeing)
- [ ] Ask AAOS and the Scoliosis Research Society for written permission
- [ ] Revisit the NHS with a verbatim-passage display design
- [ ] Explore Sinhala, Tamil or Tanglish queries
- [ ] Compare small open models with API models
- [ ] If there is a real research question and ethics approval is possible, a patient-feedback study and a short paper or preprint

---

## Loose ends

- [ ] Confirm the clinician or physiotherapist review is possible (scope open question)
- [ ] Decide whether v1 needs a feedback mechanism
- [ ] Set `HF_HUB_OFFLINE=1` when the model is already cached, to skip harmless network retries
- [ ] Revisit the embedding model and chunk size after Phase 3 (settings live in `src/rag/config.py`)

## How to update this file

1. Tick boxes only with evidence (a passing test, a results table, a deployed link).
2. Change the "Last updated" date and the Snapshot table.
3. Commit it with the work it describes, for example `docs: tick Phase 2 retrieval baseline`.
