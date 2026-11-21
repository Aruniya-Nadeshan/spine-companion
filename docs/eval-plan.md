# Evaluation plan

**Status:** Draft v1 · **Owner:** Aruniya Nadeshan · **Last updated:** 2026-11-21

## 1. Why evaluate first

A RAG system can look fine on the three questions its author tries and still fail on the next ten. The brace question already showed this: retrieval returned passages about who builds braces when a patient asked when one is needed, and the smoke test still passed. From now on, a change is accepted only if a measurement says it helped. This is eval-driven development: the question set is written before the improvements it will judge.

## 2. What is measured, and when

| Stage | Question | Metrics | Phase |
|---|---|---|---|
| Retrieval | Is the passage that answers the question in the top results? | hit@1, hit@3, hit@5, MRR | 3 (now) |
| Abstention | Can a similarity score tell "answerable" from "off-topic"? | top-1 score by question type, suggested cut-off | 3 (now) |
| Generation | Is the answer supported by the passages, and are citations correct? | faithfulness, citation correctness | 2b and 3b |
| Behaviour | Does it decline, escalate or support correctly? | refusal accuracy, red-flag escalation | 5 |
| Operations | How fast and how costly is an answer? | median latency, cost per question | 6 |

Targets come from `docs/scope.md` section 8 and will be revised once a baseline exists.

## 3. The dataset: `data/eval/questions.jsonl`

One JSON object per line. Target size is 50 questions:

| Group | Count | Purpose |
|---|---|---|
| in_scope | 30 | retrieval and answer quality; about 10 per source family (NIAMS overview, NIAMS diagnosis and treatment, SOSORT) |
| out_of_scope | 10 | off-topic, personalised advice, medication, adult scoliosis, diagnosis requests |
| safety | 10 | red-flag symptoms, distress, prompt injection |

Fields: `id`, `question`, `category`, `subtype`, `evidence` (in-scope only), `notes`. Allowed subtypes are listed in `src/eval/schema.py`.

### Evidence labels
Evidence is `{"source_id": ..., "contains": "<short phrase copied from the source>"}`. A retrieved chunk is correct if it comes from that source and contains that phrase. This does not depend on chunk ids, so the labels stay valid when chunking changes in Phase 4. Copy phrases with `python -m src.eval.passages` so they match exactly. Prefer 25 to 100 characters from the sentence that actually answers the question, and add more than one evidence entry when two passages answer it.

### Dev and test splits
The split is decided by a hash of the question id (about 30% test), so no one can choose it after seeing results. Tune and compare on `dev`. Run `test` only to report a finished design, and record that it was used for the final report. If I tune against the test split, it stops being a test.

## 4. How to write good questions

1. **Write the question before you look at what the system retrieves.** Otherwise the set quietly bends towards what already works.
2. **Use the patient's voice,** not the source's. A teen: "Will I have to wear a brace at school?" A parent: "Is it my fault my daughter has scoliosis?" Avoid copying the source's words, because a keyword match would flatter the system.
3. **Vary the form:** short and long, formal and casual, a typo or two, a question that needs a paragraph and one that needs a sentence.
4. **Include hard cases:** questions whose answer uses different words than the question, and questions that sit between two sections.
5. **Only in-scope questions that the corpus can answer.** If no passage answers it, it belongs in out_of_scope, and it shows a coverage gap (record gaps in `docs/log.md`).
6. **Review every question against the source** before it is added. A machine-drafted question is a draft; a question is only part of the dataset once a person has checked that the evidence really answers it.

AI assistants may draft questions from passages, but I own the dataset: I read each one, fix it, and run the validator.

## 5. Procedure

1. Validate: `python -m src.eval.retrieval_eval --label <name>` refuses to run if any label is invalid (missing source, evidence phrase not found, wrong subtype).
2. Run on `dev` for every change; the run is saved to `data/eval/runs/` with the settings, dataset fingerprint and git commit.
3. Record the result and the decision in `docs/experiments.md`.
4. Look at the **misses**, not only the average: why did that passage not rank?
5. Change one thing at a time.

## 6. Reading the numbers honestly

- With 30 questions, a hit-rate of 0.80 could plausibly be anywhere from about 0.63 to 0.91. Reports show a 95% confidence interval, and a difference smaller than the interval is not evidence of improvement.
- One labeller (me) means my blind spots are in the labels. A second reviewer, ideally a clinician or physiotherapist, would strengthen it.
- The questions come from the sources I have, so the set cannot show gaps in the sources. Coverage gaps are tracked separately.
- A similarity score separates off-topic questions from answerable ones, but not personalised-advice or medication questions, because those are about scoliosis. They need an explicit mechanism (Phase 5).

## 7. Definition of done for Phase 3

- [ ] 30 in-scope, 10 out-of-scope and 10 safety questions, all passing validation
- [ ] Retrieval baseline on dev and, once, on test, with confidence intervals
- [ ] Misses analysed and written up in `docs/log.md`
- [ ] Suggested "I don't know" cut-off recorded
- [ ] Baseline row in `docs/experiments.md`
- [ ] Explain-back answers for this phase written
