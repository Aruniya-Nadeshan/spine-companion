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
