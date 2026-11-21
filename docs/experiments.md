# Experiment log

One row per measured change. Metrics are on the dev split unless stated. Change one thing at a time, record the decision even when the answer is "no improvement", and only compare runs that used the same dataset fingerprint and split.

| Date | Label | What changed | Dataset | Split | n | hit@1 | hit@3 | hit@5 | MRR | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-21 | baseline | bge-small, 250/40 words, merge under 40 | ec62287a5c0c | dev | 22 | 0.364 | 0.727 | 0.864 | 0.560 | First measurement; labels incomplete for 6 questions (see audit) |
| 2026-11-21 | baseline-v1.1 | same system; evidence labels audited (6 questions gained a valid extra passage) | (see run file) | dev | 22 | 0.545 | 0.818 | 0.909 | 0.687 | Reference for all later comparisons. The gain over `baseline` comes from the labels, not the system. |

## What the first two runs showed

- Treatment questions were found 9/9 within the top 5; 2 of the 22 dev questions are genuine misses.
- **q005** ("Does scoliosis run in the family?"): the NIAMS sentence says "parent, brother, or sister" and shares no word with the question, so keyword search will not rescue it. This is a meaning-matching problem.
- **q029** ("Why does scoliosis seem to get worse more often in girls?"): retrieval returns the NIAMS statement that girls are *more likely to get* scoliosis, not the SOSORT statement that curves *progress* more often in girls. A related fact, not the answer.
- A passing hit is not always a good answer for a patient. q001 ranks a SOSORT definition (it opens with Hippocrates and Galen) above the NIAMS one. Both count as relevant, but only one is written for a patient.
- Similarity scores cannot flag a miss: the missed questions scored 0.69 to 0.80 at rank 1, the same as hits.

## Hypotheses to test (written before running, so they cannot be bent to fit the results)

Run each with `python -m src.eval.experiment --name <name> ...`, one change at a time.

| # | Name | Command options | Prediction | What would make me wrong |
|---|---|---|---|---|
| H1 | no-heading | `--embed-text none` | "What is X?" questions stop being pulled to "Definitions" chunks (q018 improves). q001 may get worse. | Nothing changes, or more questions get worse than better |
| H2 | heading-only | `--embed-text heading` | Small effect: the document title adds little | A clear change either way |
| H3 | small-chunks | `--chunk-target 120 --chunk-overlap 20 --min-chunk-words 20` | NIAMS treatment answers become findable on their own (the surgery and bracing text no longer share a chunk). SOSORT precision improves; some questions lose context | Misses increase |
| H4 | bge-base | `--model BAAI/bge-base-en-v1.5` | A stronger model may connect "family" with "parent, brother, or sister" (q005). Slower | q005 still misses |
| H5 | hybrid (needs code) | keyword plus vector search | Helps exact-term questions; will not fix q005 because the question and the answer share no word | It fixes q005 |
| H6 | reranker (needs code) | a second model reorders the top results | Improves hit@1 and the "related fact, wrong answer" cases such as q029 | No change at rank 1 |
| H7 | source balance (needs code) | take top results per source before merging | Stops clinician-written SOSORT chunks outranking patient-language NIAMS ones | NIAMS answers still lose |

## How to read an experiment
1. Look at the comparison, not only the average: how many questions got **better**, how many **worse**, and the sign-test p-value.
2. With roughly 20 questions, a clean 3-0 improvement has p = 0.25. Only a larger and cleaner pattern is worth acting on.
3. Adopt a variant only if it helps some questions and hurts none (or very few), and it makes sense for a reason you can explain.
4. Confirm a finished design once on the test split, and say so in the Decision column.
