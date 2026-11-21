# Spine Companion — Literature Review Tracker

## Research Focus
Evidence-grounded AI for scoliosis education and reliable healthcare question answering.

---

## Paper 1
* **Title:** Evidence-Chain Reliable RAG: Word-Level Hallucination Detection, Source Attribution, and Provenance Explanation for LLM Applications[cite: 1]
* **Year:** 2024[cite: 1]
* **Link:** Not listed in manuscript (Published in *Journal of Advanced Computing & Intelligent Systems*, Vol. 2024, pp. 77–88)[cite: 1, 2, 13]
* **Problem addressed:** Standard RAG systems still generate unsupported claims, altered numbers, or fabricated entities even when given retrieved passages[cite: 1]. Existing metrics (like BLEU, ROUGE, or BERTScore) and sentence-level NLI detectors fail to pinpoint exact unsupported word spans or provide auditable source-chunk provenance[cite: 1].
* **What did they build/do?** Built a reproducible, offline evidence-chain evaluation and auditing package that aligns generated answers with retrieved passages/records, scores hallucination risk at both sentence and word levels, and returns the exact source chunk supporting each claim[cite: 1, 2, 3].
* **AI/technical approach:** Combines lexical content-word coverage, sparse retrieval matching (BM25 and TF-IDF cosine similarity), and deterministic numeric/named-entity mismatch rules (`NLI-lite`) into supervised classifiers (`EvidenceChain-LR` and `EvidenceChain-RF`)[cite: 2, 3]. Word-level hallucination probabilities are derived by multiplying sentence-level risk by token novelty/mismatch signals, while top-1 provenance attribution uses maximum chunk similarity[cite: 3].
* **How did they evaluate it?** Evaluated on a RAGTruth-compatible audit corpus (140 sources, 840 responses, 2,250 sentences, and 23,284 word tokens across QA, Summarization, and Data-to-Text tasks) using source-level train/dev/test splits[cite: 1, 2, 4]. Measured Precision, Recall, F1, Accuracy, ROC-AUC, PR-AUC, feature ablations, and top-1 source attribution accuracy[cite: 3, 6, 7, 8]. `EvidenceChain-RF` achieved **0.545 F1** (0.919 ROC-AUC) at the word level and **0.975 F1** at the sentence level, while TF-IDF argmax reached **62.0%** top-1 evidence attribution[cite: 1, 6, 7, 8].
* **Limitations:** Evaluated on a controlled/synthetic audit corpus with injected fact replacements rather than the full public RAGTruth dataset with subtle real-world LLM reasoning errors[cite: 11]; relies on English-centric rules (capitalization and Arabic numerals)[cite: 11]; modest word-level PR-AUC (0.357) due to class imbalance and span-boundary noise around neighboring words[cite: 1, 6, 11].
* **What can Spine Companion learn from this?** Rather than relying solely on opaque LLM-as-a-judge checks, Spine Companion can pair lightweight deterministic verification (checking numeric measurements like Cobb angles, brace-wear hours, and clinical terms against retrieved scoliosis guidelines) with chunk-level source attribution to highlight unverified spans and show users exact source provenance[cite: 3, 12].

---

## Paper 2
* **Title:** ASHABot: An LLM-Powered Chatbot to Support the Informational Needs of Community Health Workers[cite: 14]
* **Year:** 2025[cite: 14]
* **Link:** https://doi.org/10.1145/3706598.3713680[cite: 14]
* **Problem addressed:** Frontline community health workers (ASHAs) in India have limited formal medical training and reference materials, while facing time constraints, long distances, and social hesitation/fear of judgment when asking supervisors (ANMs) or doctors basic or sensitive health questions[cite: 14, 15].
* **What did they build/do?** Designed, built, and field-deployed **ASHABot**, a bilingual (Hindi/English), voice-and-text WhatsApp chatbot over a doctor-curated knowledge base with an *experts-in-the-loop* escalation workflow for unanswered queries[cite: 15, 16, 17].
* **AI/technical approach:** Built on Microsoft's open-source `BYOeB` (Build Your Own expert Bot) framework using **GPT-4** with retrieval over a curated government/medical handbook knowledge base[cite: 15, 16, 17]. When the bot triggers an `"I don't know"` fallback, it routes the question to multiple human supervisors (ANMs) and uses an LLM consensus-synthesis prompt (with majority voting) to generate a verified answer and update the knowledge base[cite: 16, 17, 31, 32]. Also uses dual Hindi+English query input to mitigate speech-to-text/translation errors and suggests clickable "Related Questions"[cite: 17, 21].
* **How did they evaluate it?** Conducted pre-deployment benchmarking against ground-truth answers from Doctors, CHOs, and ANMs (achieving >85% accuracy across evaluations)[cite: 18, 19], followed by a 3.5-month IRB-approved field deployment with 20 ASHAs and 15 ANMs in Rajasthan, India[cite: 18, 19]. Analyzed 1,761 ASHA messages and 788 ANM responses alongside 28 semi-structured interviews[cite: 19, 20]. Automated responses covered **83.6%** of clinical queries with a **95.7%** user helpfulness rating[cite: 21].
* **Limitations:** Human-in-the-loop escalation struggled in practice—ANMs ignored most prompts due to workload, lack of incentives, and fear of accountability, resulting in consensus on only 19 of 264 escalated queries (~58.6-hour average delay)[cite: 21, 23, 27]; speech-to-text/translation errors on regional dialects reduced user trust in audio input[cite: 23, 25]; users exhibited over-reliance ("technodeterminism"), treating the bot as an infallible authority even when warned[cite: 25, 26]; small single-district sample size[cite: 27].
* **What can Spine Companion learn from this?**
  1. **Guided Follow-ups:** Suggested "Related Questions" accounted for 59.1% of queries—adding clickable follow-up prompts can help scoliosis patients/caregivers ask questions they don't know how to formulate[cite: 21, 24].
  2. **Calibrated Trust & Refusal:** Explicitly saying `"I don't know"` builds trust, but Spine Companion must actively guard against patient over-reliance by positioning itself as a fallible educational supplement to orthopedic clinicians rather than a diagnostic authority[cite: 14, 25, 26].
  3. **Low-Friction Escalation:** If clinician review is used, asynchronous crowdsourcing causes multi-day delays unless paired with clear incentives and low-burden workflows[cite: 21, 27].

---

## Paper 3
* **Title:** Medical QA dialogue datasets in RAG systems performance evaluation and ChatGPT optimization[cite: 36]
* **Year:** 2025[cite: 36, 51]
* **Link:** https://doi.org/10.1038/s41598-025-28015-4[cite: 36, 51]
* **Problem addressed:** Building and maintaining formal clinical guideline knowledge bases for medical RAG is costly and labor-intensive, while general LLMs hallucinate without grounding[cite: 36, 37, 50]. Furthermore, it is unclear how corpus metadata structuring and multi-stage retrieval pipelines trade off clinical accuracy against real-time latency[cite: 37, 45, 50].
* **What did they build/do?** Evaluated real-world doctor-patient consultation dialogues as a scalable RAG knowledge source and benchmarked different corpus indexing schemas, retrieval pipelines, and LLM generators for clinical QA[cite: 36, 38, 39, 44].
* **AI/technical approach:** Embedded ~58,897–70,000 Chinese doctor-patient dialogues (spanning Oncology, Pediatrics, Surgery, and Andrology) using `m3e-base`[cite: 38, 40, 43, 44]. Compared answer-centric indexing (`D1`: embedding doctor responses) against title-centric metadata indexing (`D2`: embedding concise patient question titles with answers stored as metadata)[cite: 39]. Tested four pipelines—`Vector-only`, `Rerank-only` (Cross-Encoder), `RRF` (BM25 + dense Reciprocal Rank Fusion), and `Cascade RRF→Rerank`—across `GPT-3.5`, `GPT-4o`, and `GPT-5`[cite: 36, 39, 44].
* **How did they evaluate it?** Evaluated on held-out stratified test splits (350 oncology cases; 250 multi-department cases) using ROUGE, BLEU, BERTScore, cosine similarity, end-to-end latency, qualitative error analysis of the bottom 5% outputs, and blinded 5-point Likert evaluations by three medical specialists (Readability, Accuracy, Authenticity)[cite: 38, 43, 45, 47, 48]. Title-centric `D2` increased retrieval similarity by **30.8%** over `D1`[cite: 41]; `Rerank-only` + `GPT-4o` achieved the best accuracy-latency balance (~4.0s total latency; 4.91/5 clinician authenticity rating)[cite: 46, 47, 49, 50].
* **Limitations:** Lacks explicit safety triaging, risk-aware refusal behaviors, or hallucination auditing workflows[cite: 47, 50]; evaluated exclusively on Chinese medical dialogues without query rewriting/expansion for noisy or underspecified patient questions[cite: 47, 50]; rerankers occasionally prioritized superficial semantic closeness over clinical distinction (e.g., conflating acute vs. chronic stages or structurally similar conditions)[cite: 48].
* **What can Spine Companion learn from this?**
  1. **Metadata Design Matters Most:** Indexing clean, concise question/topic titles alongside structured clinical metadata outperforms embedding long, noisy text blocks[cite: 36, 50].
  2. **Keep Retrieval Lean:** A single-stage **Dense Retrieval + Cross-Encoder Reranker** pipeline paired with a fast model (`GPT-4o` class) provides the best accuracy-to-latency ratio (~4s), whereas over-engineered cascade pipelines (`RRF→Rerank`) amplify irrelevant context and double latency[cite: 46, 47, 50].
  3. **Clinical Granularity Filtering:** Spine Companion should separate metadata by clinical stage/severity (e.g., mild vs. moderate vs. surgical scoliosis; pediatric vs. adult) so the reranker does not mix incompatible treatment advice[cite: 48, 50].

---

## Initial Observations

* **What problems are existing systems trying to solve?**
  * Reducing LLM hallucinations and ungrounded medical advice in high-stakes healthcare QA without the prohibitive cost of training domain-specific foundation models from scratch[cite: 1, 36, 37].
  * Bridging knowledge gaps for non-specialist users (patients or frontline health workers) who struggle with complex medical terminology, hesitate to ask basic/sensitive questions, or lack immediate access to specialists[cite: 14, 15, 22].
  * Making RAG outputs auditable and trustworthy through source attribution, uncertainty admission (`"I don't know"`), and human expert oversight[cite: 1, 2, 16, 25].

* **What techniques are commonly used?**
  * **Curated & Metadata-Structured RAG:** Grounding general-purpose LLMs (e.g., GPT-4/GPT-4o) over domain-specific knowledge bases or structured QA pairs where concise titles/questions are indexed cleanly[cite: 16, 17, 39, 50].
  * **Hybrid & Reranked Retrieval:** Combining dense vector embeddings with lexical signals (BM25/TF-IDF) and Cross-Encoder reranking, while keeping pipelines single-stage to avoid noise amplification[cite: 2, 3, 45, 50].
  * **Verification & Guardrails:** Deterministic rule/feature checks for numbers and entities (`EvidenceChain`), conservative confidence thresholds with explicit `"I don't know"` refusals, and human/expert-in-the-loop review[cite: 2, 3, 17, 20].
  * **Guided UX Scaffolding:** Providing clickable follow-up prompts ("Related Questions") and multimodal inputs to help users articulate complex health queries[cite: 15, 21, 24].

* **How are these systems evaluated?**
  * **Multi-Level Automated Metrics:** Combining overlap/semantic metrics (ROUGE, BLEU, BERTScore) with classification metrics (Precision, Recall, F1, ROC-AUC, PR-AUC) for hallucination detection and top-1 source attribution accuracy[cite: 3, 6, 8, 41].
  * **Latency & Ablation Benchmarks:** Measuring end-to-end response time (targeting <4–6s for interactive usability) alongside component ablations (e.g., removing mismatch rules or rerankers)[cite: 6, 7, 46, 47].
  * **Clinician & Field Evaluation:** Blinded physician scoring (Accuracy, Readability, Completeness, Authenticity) paired with real-world user logs and qualitative interviews to uncover behavioral failure modes[cite: 18, 19, 43, 48].

* **What limitations repeatedly appear?**
  * **Semantic Similarity $\neq$ Clinical Safety:** Rerankers and LLMs can conflate different disease stages or adjacent conditions that share vocabulary, or fabricate plausible-sounding details when retrieved context is weak[cite: 11, 48].
  * **User Over-Reliance vs. Expert Bottlenecks:** Users tend to treat fluent AI bots as infallible authorities even when warned[cite: 25, 26], yet routing uncertain queries to human clinicians creates severe latency and workload bottlenecks[cite: 21, 27].
  * **Noisy User Inputs:** Underspecified queries, dialect/transcription errors, and lack of patient context (e.g., age, severity) degrade retrieval quality when no query-clarification or rewriting layer exists[cite: 23, 47, 50].

* **What questions remain unanswered?**
  * How can a healthcare RAG system enforce **risk-aware refusal and clinical triage** (e.g., detecting red-flag scoliosis symptoms or surgical thresholds) without relying on slow human-in-the-loop queues[cite: 21, 47, 50]?
  * How can **token/span-level provenance and uncertainty indicators** be surfaced in a patient-facing UI so users can verify claims easily without inducing blind trust or alert fatigue[cite: 11, 12, 26]?
  * How effectively does **metadata stratification by clinical context** (e.g., age group, curve severity/Cobb angle, treatment stage) prevent cross-stage advice conflation in specialized orthopedic education[cite: 48, 50]?
