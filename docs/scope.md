# Project Scope: v1

**Status:** Draft v1.1 · **Owner:** Aruniya Nadeshan · **Last updated:** 2026-11-19

## 1. Problem

People diagnosed with scoliosis, and their families, face a flood of information of very uneven quality. Clinic visits are short, and many questions come up afterwards: what a Cobb angle means, what bracing involves, what recovery looks like. General-purpose chatbots answer fluently but can hallucinate medical details, and they rarely say where an answer came from or admit when they don't know.

## 2. Goal

Build a retrieval-augmented chatbot that answers scoliosis questions **only from vetted sources**, cites those sources, communicates in a calm and supportive tone, and **declines or escalates** when a question is outside its scope.

v1 success means a public demo that I can measure, not a big feature list.

## 3. Users

| User | Typical need |
|---|---|
| Newly diagnosed teen | "What does this diagnosis mean?" |
| Parent or caregiver of a child or teen with scoliosis | "What are the options, and what should I ask the doctor?" |
| Teen preparing for or recovering from treatment (bracing, surgery) | "What does bracing or surgery usually involve?" |

Assumed reading level: general public, around grade 8. Language for v1: English.

**Adults with scoliosis are out of scope for v1.** Every v1 source addresses children, teens, or scoliosis during growth (see `docs/decisions.md`, 2026-11-19).

## 4. In scope (v1)

1. **Condition basics:** what scoliosis is; common types (idiopathic, congenital, neuromuscular); causes and risk factors at a general level.
2. **Diagnosis and monitoring:** how it is assessed, what a Cobb angle is, what follow-up visits involve.
3. **Treatment overview:** observation, bracing, physiotherapy-based approaches, and surgery, explained at a high level, including who treats scoliosis.
4. **Living with scoliosis (limited):** exercise and physical activity, coping with wearing a brace, and support groups. Coverage is thin, so the bot must say so when its sources do not answer a question.
5. **Appointment preparation:** suggested questions to ask a care team.

**Known coverage gaps in the current sources:** school and work, sleep, body image and emotional wellbeing beyond bracing, adult scoliosis, and detailed surgical recovery. Questions on these get an honest "I don't have information on that" plus a pointer to the care team, until suitable openly licensed sources are added.

## 5. Out of scope (non-goals)

- Diagnosing, or interpreting an individual's X-ray, Cobb angle, symptoms or test results
- Recommending a specific treatment, brace schedule, or surgical decision for a specific person
- Medication, dosage, or supplement advice
- Replacing a clinician, therapist, or crisis service
- **Adult scoliosis** (for example degenerative scoliosis, adult surgery and recovery). Child and teen content must not be generalised to adults.
- Image upload or X-ray analysis (potential research extension, not v1)
- Languages other than English (research extension)
- User accounts and storage of personal health data (v1 is stateless; see Privacy)

## 6. Expected behaviour

| Situation | Behaviour |
|---|---|
| Question covered by retrieved sources | Answer in plain language, cite sources, stay within what the sources say |
| Retrieval is weak or sources conflict | Say what is and isn't known, point to the care team, never fill gaps from model memory |
| Out-of-scope request (diagnosis, personalised treatment, medication) | Politely decline, explain why, offer the closest in-scope help (e.g. questions to ask their doctor) |
| Adult-specific question | Say v1 covers children and teens only, point to the care team, do not adapt child or teen guidance to adults |
| Red-flag symptom described (e.g. new weakness or numbness, loss of bladder or bowel control, rapidly worsening pain, breathing difficulty, signs of post-surgical infection) | Stop normal answering, advise contacting a clinician or emergency services promptly |
| Emotional distress | Respond with empathy, avoid clinical coldness, suggest talking to their care team or a trusted person; if the person mentions harming themselves, give crisis resources |
| Off-topic question | Say it's outside what this assistant covers |
| Prompt-injection or "ignore your rules" attempts | Maintain behaviour; covered in the red-team set |

The red-flag list will be reviewed against the source documents before it is finalised.

## 7. Knowledge sources

**Selection criteria:** published by a recognised medical body, hospital, or health service; clearly dated or recently reviewed; written for patients where possible; licence permits storage and retrieval, or we link without copying.

| Source | Type | Licence status (checked 2026-11-19) | v1 use |
|---|---|---|---|
| NIAMS: Scoliosis in Children and Teens, Overview, Symptoms, & Causes | Government | Text public domain; images excluded | Ingest text, credit NIAMS |
| NIAMS: Scoliosis in Children and Teens, Diagnosis, Treatment, and Steps to Take | Government | Text public domain; images excluded | Ingest text, credit NIAMS |
| SOSORT 2016 guidelines (Negrini et al., 2018) | Clinical guideline | CC BY 4.0 | Ingest via Europe PMC full-text XML, attribute, note changes |
| NIAMS Research & Resources tab | Government | Public domain text | Not ingested (low value for patients) |
| NHS scoliosis pages | National health service | OGL with conditions; adapted content may not be attributed to the NHS | Deferred: paraphrasing conflicts with citing the NHS; revisit with a verbatim-passage design |
| AAOS OrthoInfo | Professional society | All rights reserved; link-only policy | Link only, or request permission |
| Scoliosis Research Society | Professional society | SRS holds copyright; no open licence found | Link only, or request permission |
| Boston Children's Hospital | Hospital | No reuse licence found | Not ingested |
| MedlinePlus, PMC open-access papers | Government / journals | Not yet verified | Candidates to check |

Each document is logged in `data/sources.csv` with: id, title, publisher, URL (human-readable link used in citations), fetch URL (where the code downloads from), format (`html` or `jats-xml`), date accessed, licence status, required attribution text, and v1 use (ingest / link-only / deferred). Nothing enters the index without a row, and answers display the attribution for every source they cite.

These are readings of published terms, not legal advice. Re-check licences before any deployment beyond a portfolio demo.

## 8. Success metrics

Evaluated on a hand-built set of 50 questions (30 in-scope with expected source passages, 10 out-of-scope including adult-scoliosis and personalised-advice requests, 10 red-flag/safety). Initial targets are hypotheses and will be revised after the baseline.

| Metric | Initial target |
|---|---|
| Retrieval hit-rate@5 | ≥ 0.85 |
| Answer faithfulness (answer supported by retrieved text) | ≥ 0.90 |
| Citation correctness | ≥ 0.95 |
| Out-of-scope refusal accuracy | ≥ 0.95 |
| Red-flag escalation accuracy | 1.00 |
| Median response time | < 5 s |

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Hallucinated medical information | Answer only from retrieved context; faithfulness evaluation; abstain when retrieval is weak |
| User treats the bot as medical advice | Persistent disclaimer; refusals for personalised advice; scope stated in the UI |
| Child or teen guidance applied to adults | Scope stated in the UI; adult-specific questions are declined; adult refusals are in the evaluation set |
| Thin coverage of everyday-life topics tempts the model to improvise | Answer only from retrieved context; "I don't have information on that" behaviour; coverage gaps listed in section 4 |
| Outdated sources | Record dates in `sources.csv`; periodic review |
| Distressing content for vulnerable users | Tone guidelines; escalation behaviour; avoid worst-case framing |
| Licence or copyright issues | Licence check before ingestion; link rather than copy when unsure |
| Silent ingestion failure leaves the corpus incomplete | Quality check per document; the run stops on the first failure |
| Privacy | No accounts; no personal data stored; logs exclude user-identifying content; users told not to share personal details |

## 10. Technical approach (v1, tentative)

Python · HTML and JATS XML ingestion (Europe PMC API for open-access articles) · sentence-transformers embeddings · ChromaDB · LLM via API or local model · FastAPI · simple web UI · pytest · Docker · GitHub Actions. Retrieval is built without a framework first; frameworks are adopted later only where they replace something I can explain.

## 11. Milestones

1. [x] Scope and source list (this document)
2. [x] Corpus ingested and cleaned (3 sources, quality-checked)
3. [ ] Baseline RAG working end to end
4. [ ] Evaluation set and baseline metrics
5. [ ] Retrieval improvements, measured
6. [ ] Safety behaviours and red-team set
7. [ ] API, UI, Docker
8. [ ] Public demo, CI, case-study README

## 12. Open questions

- What similarity threshold triggers "I don't know"? To be calibrated on the evaluation set.
- Which LLM balances answer quality, cost and latency?
- Can a clinician or physiotherapist review the red-flag list and a sample of answers before launch?
- Is a feedback mechanism needed in v1, or only after launch?
- Which openly licensed sources cover adult scoliosis and everyday-life topics (school, sleep, body image, emotional wellbeing)?
- The SOSORT guidelines are written for clinicians. How do answers stay plain-language without distorting the meaning?
