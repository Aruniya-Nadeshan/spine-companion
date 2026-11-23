# Experiment log

One row per measured run. Dev unless stated. Runs are comparable only when dataset fingerprint, split and batch match. The JSON for every run is in `data/eval/runs/`. "Better / worse" counts questions whose rank improved or got worse against the stated reference, and p is the exact sign test on those counts.

## Results

| Date | Label | What changed | Dataset | Split | n | hit@1 | hit@3 | hit@5 | MRR | Outcome |
|---|---|---|---|---|---|---|---|---|---|---|
| 11-21 | baseline | bge-small, 250/40 words, merge under 40 | ec62287a5c0c | dev | 22 | 0.364 | 0.727 | 0.864 | 0.560 | First measurement; 6 labels incomplete |
| 11-21 | baseline-v1.1 | same system, evidence labels audited | def401190635 | dev | 22 | 0.545 | 0.818 | 0.909 | 0.687 | Reference for the next four rows; the gain over `baseline` is from labels, not the system |
| 11-21 | no-heading (H1) | embed text only, no title or heading | def401190635 | dev | 22 | 0.727 | 0.864 | 0.909 | 0.799 | 6 better, 2 worse, p=0.29. Prediction partly wrong (q018 got worse) |
| 11-21 | heading-only (H2) | embed heading and text, no document title | def401190635 | dev | 22 | 0.636 | 0.864 | 0.955 | 0.758 | 4 better, 1 worse, p=0.38 |
| 11-21 | small-chunks (H3) | ~120-word chunks, overlap 20 | def401190635 | dev | 22 | 0.500 | 0.682 | 0.727 | 0.595 | 2 better, 7 worse, p=0.18. Rejected; prediction wrong (q018 still missed) |
| 11-22 | baseline-v2 | same system; dataset grown (batch 2 added) | efc030cda704 | dev | 37 | 0.541 | 0.730 | 0.811 | 0.644 | Reference for the next rows |
| 11-22 | baseline-b2 | batch 2 only, labels unaudited | efc030cda704 | dev, batch 2 | 15 | 0.533 | 0.600 | 0.667 | 0.580 | Unseen-batch reference |
| 11-22 | no-heading-b2 | H1 on unseen batch 2 | efc030cda704 | dev, batch 2 | 15 | 0.533 | 0.667 | 0.667 | 0.589 | 1 better, 0 worse, p=1.0 |
| 11-22 | heading-only-b2 | H2 on unseen batch 2 | efc030cda704 | dev, batch 2 | 15 | 0.533 | 0.667 | 0.733 | 0.602 | 2 better, 0 worse, p=0.5. Not adopted: effects too small |
| 11-22 | hybrid (H5) | BM25 + vector, RRF, 20 candidates | efc030cda704 | dev | 37 | 0.622 | 0.838 | 0.865 | 0.736 | 10 better, 2 worse, p=0.039. Prediction partly wrong (q005 improved) |
| 11-22 | rerank (H6) | MiniLM cross-encoder over top 20 | efc030cda704 | dev | 37 | 0.676 | 0.838 | 0.892 | 0.766 | 10 better, 2 worse, p=0.039. Prediction held |
| 11-22 | hybrid-rerank (H8) | BM25 fusion, then cross-encoder | efc030cda704 | dev | 37 | 0.649 | 0.892 | 0.946 | 0.770 | 12 better, 2 worse, p=0.013. Frozen as "Design A" |
| 11-23 | baseline-b3 | batch 3 only, unaudited | 1fa79eb2636f | dev, batch 3 | 12 | 0.333 | 0.500 | 0.500 | 0.417 | Fresh-question reference |
| 11-23 | designA-b3 | Design A on unseen batch 3 | 1fa79eb2636f | dev, batch 3 | 12 | 0.500 | 0.500 | 0.583 | 0.521 | 3 better, 0 worse, p=0.25. Pre-registered hit@3 gain of 0.10 NOT met |
| 11-23 | baseline-v3 | same system, full dev set (batches 1 to 3) | 1fa79eb2636f | dev | 49 | 0.490 | 0.673 | 0.735 | 0.588 | Reference. Median 18 ms |
| 11-23 | designA-v3 | hybrid + rerank, 20 candidates | 1fa79eb2636f | dev | 49 | 0.612 | 0.796 | 0.857 | 0.709 | 15 better, 2 worse, p=0.002. Median 786 ms |
| 11-23 | small-to-big (H9) | 60-word children returned as parents; hybrid + rerank, 40 candidates | 1fa79eb2636f | dev | 49 | 0.612 | 0.776 | 0.816 | 0.692 | 15 better, 7 worse, p=0.134. Rejected; q090, q091 still missed |
| 11-23 | designA-bge-base (H4) | Design A with bge-base embeddings | 1fa79eb2636f | dev | 49 | 0.612 | 0.816 | 0.898 | 0.720 | vs Design A: 2 better, 0 worse, p=0.5. Rule required net +4: not adopted. Prediction held |
| 11-23 | baseline-test | baseline on the test split | 1fa79eb2636f | test | 26 | 0.462 | 0.654 | 0.769 | 0.576 | Final-report reference (one run) |
| 11-23 | final-test | Design A on the test split | 1fa79eb2636f | test | 26 | 0.346 | 0.731 | 0.885 | 0.539 | vs baseline: 6 better, 8 worse, p=0.79. **Dev improvement did not replicate at top ranks** |

## What the evidence says

1. **Design A found the right passage somewhere in the top 5 more often than the baseline on every question set** (dev 0.735 to 0.857, batch 3 0.500 to 0.583, test 0.769 to 0.885), and it improved far more questions than it hurt on dev (p=0.002).
2. **On the independent test split it did not improve the ranking.** 6 questions improved and 8 got worse (p=0.79), hit@1 fell from 0.462 to 0.346 and MRR from 0.576 to 0.539. The gain is in recall at 3 and 5 (up by 2 and 3 questions of 26), not in putting the right passage first.
3. **Likely explanations, not tested:** the design was chosen after looking at dev failures; about ten comparisons were made on dev, so some "wins" are luck; the MS MARCO cross-encoder was trained for web passages and sometimes demotes the patient-language NIAMS passage behind a SOSORT passage that shares more words with the question.
4. **Dev numbers overstate real performance.** The baseline's hit@5 was 0.735 on dev and 0.769 on test, but Design A's was 0.857 on dev and 0.885 on test, with intervals of roughly plus or minus 0.15 on 26 questions.
5. **Cost.** Plain vector search takes about 18 ms per question; Design A about 0.8 s on a laptop CPU.
6. **Test split is spent.** It was run once for each of the baseline and Design A. It must not be used to choose between designs again; further confirmation needs new questions.

## Decision (2026-11-23)

Retrieval stays at **two candidates**: the baseline (fast, higher top-1 precision on test) and Design A (higher recall in the top 5, slower). Neither is shown to be better beyond doubt. The choice will be made with the end-to-end measure (is the final answer supported by the retrieved text, and are its citations correct) once answer generation exists, using the top 5 chunks as context.

## Hypotheses and their outcomes

| # | Idea | Prediction (written before running) | Outcome |
|---|---|---|---|
| H1 | embed text only | "What is X?" questions stop being pulled to Definitions; q018 improves | q018 got worse; ranking improved overall on dev, small on unseen data. Not adopted |
| H2 | heading, no title | small effect | Small, harmless; not adopted |
| H3 | ~120-word chunks | NIAMS treatment answers findable; some context lost | Worse (2 better, 7 worse). Rejected |
| H4 | bge-base embeddings | probably will not clear the bar | Net +2 vs Design A, below the +4 rule. Not adopted. Prediction held |
| H5 | hybrid keyword + vector | helps q071; will not fix q005; gain of 2 or fewer | q071 and q005 both improved; 10 better. Prediction partly wrong |
| H6 | cross-encoder rerank | raises hit@1; may rescue q066 | held on dev (hit@1 0.54 to 0.68); did not hold on test |
| H8 | hybrid + rerank | best of both | best on dev (p=0.013); not confirmed on test or batch 3 hit@3 |
| H9 | small-to-big | fixes q090, q091, q083 | Only q083; 7 questions worse. Rejected |

## How to read an experiment
1. Look at the comparison (better, worse, same, p), not only the average.
2. With a few dozen questions, only a large and consistent pattern is worth acting on.
3. Write the prediction and the decision rule before running.
4. Confirm on questions the design never saw. A result that only holds on the questions it was tuned on is not a result.
