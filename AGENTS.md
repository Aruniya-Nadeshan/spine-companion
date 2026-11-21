# Project context for AI assistants

spine-companion: a RAG chatbot that answers scoliosis questions only from vetted sources, with citations. Not medical advice. See docs/scope.md, docs/decisions.md and docs/eval-plan.md.

## Rules
- Answers must come only from retrieved, licensed sources. Never add medical claims from model memory.
- Every source must have a row in data/sources.csv. Respect its licence and v1_use fields. Never ingest link-only or deferred sources.
- Raw and processed data are never committed.
- Build retrieval without a framework first. Only add a dependency if the author can explain what it replaces.
- Small diffs, with a test for every new behaviour. Explain non-obvious code in comments.
- Owner is a student on Windows/PowerShell using Python 3.11: give PowerShell commands, and one command at a time when an earlier step could fail.

## How we work (evaluation-driven)
1. **Spec first.** Before code, write the goal, the design choices, and how it will be measured. The owner approves the spec.
2. **Measure before and after.** A change to retrieval, prompts or settings is kept only if the evaluation says it helped, on the dev split, with the same dataset fingerprint. Record it in docs/experiments.md.
3. **Never edit the evaluation set to make a number go up.** If a question or label is wrong, fix it in its own commit and note why, then re-run the baseline.
4. **The test split is for final reporting only.** Do not tune on it.
5. **One change at a time**, one commit per verified step, with conventional commit messages (feat, fix, docs, test, chore).
6. **Explain-back before commit.** The owner must be able to explain the change in her own words. Add the answers to docs/log.md.
7. **Log decisions** in docs/decisions.md with the reason and what else was considered.
8. **Check the data directly** when a diagnostic and reality disagree; do not stack guesses.
9. **CV claims** only for features that are built, measured and explained.

## Definition of done for a task
Tests pass, the evaluation was re-run if behaviour changed, docs/decisions.md and docs/experiments.md are updated, the owner has explained it back, and the change is committed.
