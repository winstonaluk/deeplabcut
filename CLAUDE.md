# CLAUDE.md — monorepo root

This repository contains two independent applications plus a shared schema
package that is the contract between them.

```
./
├── shared/schema/    contract: session_metadata.json, trials.csv, timestamp sidecars
├── acquisition/      behavioral video acquisition GUI — see acquisition/CLAUDE.md
└── analysis/         DeepLabCut analysis pipeline — see analysis/CLAUDE.md
```

Read `acquisition/CLAUDE.md` and `analysis/CLAUDE.md` before working in either
subdirectory — each carries its own domain context, architecture invariants,
and checkpoint list. Keep app-specific code inside its own subdirectory; the
only code shared between the two is `shared/schema/`.

`QUESTIONS.md` at repo root collects ambiguities logged during unattended runs.
`OVERNIGHT_REPORT.md` at repo root is the run summary for the current build.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- `graph.json`, `GRAPH_REPORT.md`, `wiki/` and `cache/semantic/` are tracked, so a fresh clone can query the graph immediately with no re-extraction. `graph.html` and the AST cache are not: regenerate them with `graphify export html` and `graphify update .`.
