# Project Scope: v1

**Status:** Draft v1 · **Owner:** Aruniya Nadeshan · **Last updated:** 2026-11-19

## 1. Problem

People diagnosed with scoliosis, and their families, face a flood of information of very uneven quality. Clinic visits are short, and many questions come up afterwards: what a Cobb angle means, what bracing involves, what recovery looks like. General-purpose chatbots answer fluently but can hallucinate medical details, and they rarely say where an answer came from or admit when they don't know.

## 2. Goal

Build a retrieval-augmented chatbot that answers scoliosis questions **only from vetted sources**, cites those sources, communicates in a calm and supportive tone, and **declines or escalates** when a question is outside its scope.

v1 success means a public demo that I can measure, not a big feature list.

## 3. Users

| User | Typical need |
|---|---|
| Newly diagnosed teen or adult | "What does this diagnosis mean?" |
| Parent or caregiver | "What are the options, and what should I ask the doctor?" |
| Person preparing for or recovering from treatment | "What does bracing or surgery recovery usually involve?" |

Assumed reading level: general public, around grade 8. Language for v1: English.

## 4. In scope (v1)

1. **Condition basics:** what scoliosis is; common types (idiopathic, congenital, neuromuscular, degenerative); causes and risk factors at a general level.
2. **Diagnosis and monitoring:** how it is assessed, what a Cobb angle is, what follow-up visits involve.
3. **Treatment overview:** observation, bracing, physiotherapy-based approaches, and surgery, explained at a high level, including general recovery expectations.
4. **Living with scoliosis:** exercise and sport, school and work, sleep, general back-pain self-management, body image and emotional wellbeing.
5. **Appointment preparation:** suggested questions to ask a care team.

## 5. Out of scope (non-goals)

- Diagnosing, or interpreting an individual's X-ray, Cobb angle, symptoms or test results
- Recommending a specific treatment, brace schedule, or surgical decision for a specific person
- Medication, dosage, or supplement advice
- Replacing a clinician, therapist, or crisis service
- Image upload or X-ray analysis (potential research extension, not v1)
- Languages other than English (research extension)
- User accounts and storage of personal health data (v1 is stateless; see Privacy)

## 6. Expected behaviour

| Situation | Behaviour |
|---|---|
| Question covered by retrieved sources | Answer in plain language, cite sources, stay within what the sources say |
| Retrieval is weak or sources conflict | Say what is and isn't known, point to the care team, never fill gaps from model memory |
| Out-of-scope request (diagnosis, personalised treatment, medication) | Politely decline, explain why, offer the closest in-scope help (e.g. questions to ask their doctor) |
| Red-flag symptom described (e.g. new weakness or numbness, loss of bladder or bowel control, rapidly worsening pain, breathing difficulty, signs of post-surgical infection) | Stop normal answering, advise contacting a clinician or emergency services promptly |
| Emotional distress | Respond with empathy, avoid clinical coldness, suggest talking to their care team or a trusted person; if the person mentions harming themselves, give crisis resources |
| Off-topic question | Say it's outside what this assistant covers |
| Prompt-injection or "ignore your rules" attempts | Maintain behaviour; covered in the red-team set |

The red-flag list will be reviewed against the source documents before it is finalised.

## 7. Knowledge sources

**Selection criteria:** published by a recognised medical body, hospital, or health service; clearly dated or recently reviewed; written for patients where possible; licence permits storage and retrieval, or we link without copying.

| Candidate source | Type | Licence / terms check |
|---|---|---|
| Scoliosis Research Society (SRS) patient pages | Professional society | ☐ to verify |
| NHS scoliosis pages | National health service | ☐ to verify |
| NIAMS (NIH) scoliosis information | Government | ☐ to verify |
| AAOS OrthoInfo | Professional society | ☐ to verify |
| Boston Children's Hospital / other children's hospitals | Hospital | ☐ to verify |
| Open-access clinical guidelines (e.g. SOSORT) | Guidelines | ☐ to verify |

Each document is logged in `data/sources.csv` with: id, title, publisher, URL, date accessed, licence status. Nothing enters the index without a row.

## 8. Success metrics

Evaluated on a hand-built set of 50 questions (30 in-scope with expected source passages, 10 out-of-scope, 10 red-flag/safety). Initial targets are hypotheses and will be revised after the baseline.

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
| Outdated sources | Record dates in `sources.csv`; periodic review |
| Distressing content for vulnerable users | Tone guidelines; escalation behaviour; avoid worst-case framing |
| Licence or copyright issues | Licence check before ingestion; link rather than copy when unsure |
| Privacy | No accounts; no personal data stored; logs exclude user-identifying content; users told not to share personal details |

## 10. Technical approach (v1, tentative)

Python · PDF/HTML ingestion · sentence-transformers embeddings · ChromaDB · LLM via API or local model · FastAPI · simple web UI · pytest · Docker · GitHub Actions. Retrieval is built without a framework first; frameworks are adopted later only where they replace something I can explain.

## 11. Milestones

1. Scope and source list (this document)
2. Corpus ingested and cleaned
3. Baseline RAG working end to end
4. Evaluation set and baseline metrics
5. Retrieval improvements, measured
6. Safety behaviours and red-team set
7. API, UI, Docker
8. Public demo, CI, case-study README

## 12. Open questions

- What similarity threshold triggers "I don't know"? To be calibrated on the evaluation set.
- Which LLM balances answer quality, cost and latency?
- Can a clinician or physiotherapist review the red-flag list and a sample of answers before launch?
- Is a feedback mechanism needed in v1, or only after launch?