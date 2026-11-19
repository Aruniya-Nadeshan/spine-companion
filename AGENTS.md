# Project context for AI assistants

spine-companion: a RAG chatbot that answers scoliosis questions only from vetted sources, with citations. Not medical advice. See docs/scope.md.

## Rules
- Answers must come only from retrieved, licensed sources. Never add medical claims from model memory.
- Every source must have a row in data/sources.csv. Respect its licence and v1_use fields. Never ingest link-only or deferred sources.
- Raw and processed data are never committed.
- Build retrieval without a framework first. Only add a dependency if the author can explain what it replaces.
- Small diffs, with a test for every new behaviour. Explain non-obvious code in comments.
- Owner is a student on Windows/PowerShell: give PowerShell commands.