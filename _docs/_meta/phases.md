---
id: meta-phases
title: Documentation phases
kind: meta
status: current
summary: Which documentation rules are in force. They change when the project phase changes.
read_when: you need to know which folders, skeletons and checks apply, or you are changing the project phase
updated: 2026-11-05
verified: 2026-11-05
depends_on: [meta-librarian]
review_cycle: quarterly
---

# Documentation phases

The folders stay the same for the life of the project. The rules do not.
`librarian.md` is the rulebook. This file selects the clauses in force.

A human names the phase. An agent never moves the project to the next phase because the
conversation sounds like the next phase.

---

## Current phase

**Development.** A human chose the stack: Python, FastAPI, Jinja2 HTML with HTMX, and SQLite. Git is
initialized. `features/` is the primary working surface. Its documents hold the contract and the
implementation. `tech/` and `infra/` are open. `_design/` is a source. The application tree is
`app/` and `tests/`.

---

## What never changes

These rules hold in every phase. They are the reason the library stays trustworthy.

- Folders encode **kind of knowledge**. Frontmatter encodes **stability**.
- One fact has one owning document. Everyone else links.
- `product/glossary.md` owns the vocabulary. A new term gets a glossary row first.
- `inbox/` is raw and preserved. To file an item means to distill it, not to rewrite the capture.
- Contributors amend. The librarian reshapes. Humans decide substance and rules.
- A change updates the documents it touched in the same session. Once git exists, the update goes
  in the same commit as the change.
- Contradictions go to `backlog.md` or `_meta/feedback.md`. Nobody silently picks a winner.
- `AGENTS.md` stays short. A domain invariant goes there only after a human decides it.

---

## Product ideation

The project decides what it is. Conversations and captures are the source. The library is the
compiled memory. There is no application tree.

| Surface | In this phase |
|---|---|
| `product/` | The primary working surface. Decided business claims only. No code, no paths. |
| `features/` | Open for contract-only documents. One document per named capability. |
| `tech/`, `infra/` | Empty. A technical question goes to `backlog.md` until a human decides it. |
| `inbox/` | Raw, preserved. Workshop notes and transcripts land here. |
| `wip/` | Notes for the task in flight. Deleted when the task closes. |
| `_design/` | Out of scope in this phase. |
| Application code | Out of scope. Never invent an implementation. |

**Feature anatomy.** A feature document is the contract only:

```markdown
## Purpose
## Behaviour
## Assumptions
## Related docs
```

*Data*, *Implementation* and *Failure & idempotency* come in the development phase, when there is
code to describe. `## Behaviour` follows the STE dialect in [`ste-writing.md`](./ste-writing.md).

**Anchors.** `source_anchors` name an `inbox/` capture, if a claim comes from one. Most product and
feature documents have no anchors in this phase.

**Checks.** L1 to L12 apply. L2 requires that links and anchors resolve. It does not require code
symbols, because there are none. L3 applies only to documents with anchors. L10 is `AGENTS.md`
plus `Home.md`. L12 is a judgement check. The reader compares each document with
[`ste-writing.md`](./ste-writing.md). No tool does it.

**Mismatch.** Product claims and a feature `## Behaviour` section prescribe. A later chat that
disagrees is a question for a human. Write it in `backlog.md`. `inbox/` and `wip/` describe.

**Authoring limit.** The product and feature create-tests in `authoring.md` are open. The tech and
infra create-tests answer "not in this phase, file to backlog".

---

## Development

A human starts this phase when the tech stack is chosen.

The project builds. The library compiles claims, and it also stays true of the tree.

| Surface | In that phase |
|---|---|
| `product/` | Business-only. No file paths, no function names, no code. |
| `features/` | The primary surface for named capabilities. Contract on top, implementation below. |
| `tech/` | Open: cross-cutting models, rules and conventions inside the solution. |
| `infra/` | Open: build, deploy, environments, quality gates. |
| `_design/` | A source. `tech/` documents point into it through `source_anchors`. |
| Application code | In scope. The application tree, once the stack is chosen, is a source the library tracks. |

**Feature anatomy.** A feature document uses the full skeleton of `librarian.md`. It adds `## Data`,
`## Implementation` and `## Failure & idempotency` to the contract. `## Next steps` is optional.

*Behaviour* prescribes. *Implementation* describes. The drift check (L3) and the mismatch rule in
`authoring.md` turn on that seam.

**Anchors.** `source_anchors` name the code files, design files or configuration that carry the
claim. A document without anchors cannot get a drift check.

**Checks.** L2 requires that referenced files and symbols exist. L3 compares `verified` with those
files. A pre-commit hook and role files can join L10 when they earn their keep.

**Mismatch.** If the code disagrees with a prescriptive document, the code is wrong or a
human decides. *Implementation* and *Data* yield to the source.

**Authoring limit.** All four create-tests in `authoring.md` are open: product, feature, tech, infra.

---

## Changing phase

A phase change is a human decision. The librarian never infers it from a lively chat or a first
commit.

1. A human rewrites **Current phase** above.
2. Align the create-tests in `authoring.md` with the new phase.
3. Align `AGENTS.md`. Its opening paragraph names the phase.
4. Align `Home.md`: the working-surface sentence and the reading paths that assume an empty folder.
5. Open the skeletons that the new phase requires. Add the sections that now have a source.
6. Write one row in `_meta/review-log.md`. A phase change is a maintenance event.

Do not rewrite history. Documents from an earlier phase stay in the present tense. Do not add
a preface such as "written during ideation".

---

## Related docs

- [`librarian.md`](./librarian.md): the rulebook that these phases select from
- [`authoring.md`](./authoring.md): the create-tests, which open or close with the phase
- [`docs-guidelines.md`](./docs-guidelines.md): the principles, which do not change
- [`../../AGENTS.md`](../../AGENTS.md): names the current phase in one paragraph
