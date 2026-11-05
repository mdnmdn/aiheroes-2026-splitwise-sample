---
id: meta-review-log
title: Review log
kind: meta
status: current
summary: Append-only record of what each documentation maintenance pass checked, fixed and left alone.
read_when: you are about to start a maintenance pass and need to know what the last one did
updated: 2026-11-05
verified: 2026-11-05
depends_on: [meta-librarian]
review_cycle: quarterly
---

# Review log

Write one row per pass. Never make a silent pass. "Nothing to change" is a result and gets its row.

Read this log before a maintenance pass, so that you do not repeat the work of the previous pass. Cite
checks by their ids from the revision checklist in [`librarian.md`](./librarian.md). Run
`mise run docs-log` to append a row.

| date | scope | checks run | counts | notes |
|---|---|---|---|---|
| 2026-11-05 | setup | L1–L12 | — | library created from the sample scheme, phase product ideation |
| 2026-11-05 | phase change | L1–L12 | — | phase changed from product ideation to development: `phases.md`, `authoring.md`, `AGENTS.md`, `Home.md` and `backlog.md` aligned |

## Related docs

- [`librarian.md`](./librarian.md) — the checklist these rows cite, and the reporting duty
- [`feedback.md`](./feedback.md) — proposals raised by these passes
- [`phases.md`](./phases.md) — a phase change is a maintenance event and gets a row here
