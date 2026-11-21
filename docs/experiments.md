# Experiment log

One row per measured change. Metrics are on the dev split unless stated. Change one thing at a time, and record decisions even when the answer is "no improvement".

| Date | Label | What changed | Dataset | Split | n | hit@1 | hit@3 | hit@5 | MRR | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| | baseline | bge-small, 250/40 words, merge under 40 | | dev | | | | | | |

## How to fill a row
- Copy the numbers from the printed report (or from the JSON in `data/eval/runs/`).
- `Dataset` is the fingerprint printed in the run file. If it changed, earlier rows are not comparable.
- Compare a change with the baseline only when both used the same dataset fingerprint and split.
- Write the decision in plain words ("keep", "revert", "needs a larger question set") and the reason.
