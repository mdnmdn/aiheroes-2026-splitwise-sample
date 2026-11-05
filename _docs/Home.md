---
id: index
title: Documentation home
kind: meta
status: current
summary: The map of `_docs/`. How it is organized, the catalogue, which document owns which fact, and which to read for a given task.
read_when: you start any task and need to know which two or three documents it needs
updated: 2026-11-05
verified: 2026-11-05
---

# Splitwise Lite — documentation home

**Read this first. Then read the two or three documents it sends you to, and no more.** Every rule
in this library exists to make that cheap.

This library is the working memory of **Splitwise Lite**: an app where a group records shared
expenses and sees who owes whom. If your change touched a document, update that document. Do it in
the same session and in the same commit. [`_meta/authoring.md`](./_meta/authoring.md)
says which documents and how. It is the only meta document a contributor needs. Every document that
you write or change follows [`_meta/ste-writing.md`](./_meta/ste-writing.md). To reorganize the
library itself, read [`_meta/librarian.md`](./_meta/librarian.md).

Raw captures live in `inbox/`. They stay there until a librarian pass files them.

---

## 1. How the library is organized

Folders encode **kind of knowledge**. Frontmatter encodes **stability**. A `status: draft`
document sits beside a `current` one, in the same folder.

| Path | Holds |
|---|---|
| `Home.md` | This map |
| `backlog.md` | Every open question, known gap and deferred item, project-wide |
| `product/` | Why the product exists, in business terms. No code references |
| `features/` | One document per named capability: the business contract, then the implementation |
| `tech/` | Cross-cutting models, rules and conventions inside the solution |
| `infra/` | How the system is built, deployed and operated |
| `wip/` | Notes for the task in flight. Deleted when the task closes |
| `inbox/` | Raw input, preserved, waiting to be filed |
| `_meta/` | How this library works. The underscore means *not project knowledge* |

The project phase is **product ideation**. No application code exists and the stack is not chosen.
`product/` is the working surface. A `features/` document holds the contract only. `tech/` and
`infra/` stay empty. [`_meta/phases.md`](./_meta/phases.md) is the switch.

The placement rule: **if deleting the feature from the product deletes the document, it belongs in
`features/`. If the document survives, it belongs in `tech/` or `infra/`.**

Two conventions apply everywhere. First, documents outside `wip/`, `inbox/` and `_meta/` use the
**present tense** and describe the state that holds today. Second, **every fact has one owning
document**. Every other document links to it. Section 3 is that registry.

Words have one meaning. The [glossary](./product/glossary.md) is the dictionary. The writing
dialect of [`_meta/ste-writing.md`](./_meta/ste-writing.md) applies to every document. The mode
depends on the text: procedures, agent rules and `## Behaviour` sections follow it in full.

## 2. Catalogue

<!-- generated:begin catalogue -->

### Product

| Document | What it is | Verified |
|---|---|---|
| [Backlog](./backlog.md) | Every open question, known gap and deferred item, project-wide. | 2026-11-05 |
| [Glossary](./product/glossary.md) | The product vocabulary. One definition per term, and the words that are not used for it. The dictionary of the STE dialect. | 2026-11-05 |
| [Product overview and specification](./product/overview.md) | The vision and users of Splitwise Lite, the MVP contract, the roadmap F1–F9, quality requirements and success metrics. | 2026-11-05 |

<!-- generated:end catalogue -->

### Meta

| Document | What it is |
|---|---|
| [Writing and updating docs](./_meta/authoring.md) | The duty every contributor owes the library, and the edits they may make |
| [Librarian rulebook](./_meta/librarian.md) | How the library is organized and how a maintenance pass keeps it so |
| [Documentation phases](./_meta/phases.md) | Which rules are in force in the current phase |
| [Documentation guidelines](./_meta/docs-guidelines.md) | The principles behind the rules |
| [Docs tooling reference](./_meta/tools.md) | Every `mise run docs-*` command, what it checks and what it writes |
| [STE writing dialect](./_meta/ste-writing.md) | The controlled-English rules for every document |
| [ASD-STE100 reference](./_meta/asd-ste-100.md) | A map of the external standard the dialect adapts |
| [Proposal ledger](./_meta/feedback.md) | Structural changes proposed, accepted and rejected |
| [Review log](./_meta/review-log.md) | What each maintenance pass did |

## 3. Who owns which fact

| Fact | Owner |
|---|---|
| Vision, target users, goals, non-goals | `product/overview.md` |
| MVP scope, user stories, requirements, business rules, acceptance examples | `product/overview.md` |
| Roadmap order F1–F9 and the contract of each feature | `product/overview.md`, until a feature gets its own `features/` document |
| Quality requirements and success metrics | `product/overview.md` |
| Term definitions, the balance invariant, the words not to use | `product/glossary.md` |
| Open questions, known gaps, deferred items | `backlog.md` |
| Repository layout, agent directives | `AGENTS.md` at the repository root |
| Contributor duty | `_meta/authoring.md` |
| Documentation rules and the revision checklist | `_meta/librarian.md` |
| Which rules apply in this phase | `_meta/phases.md` |
| Why the documentation rules are what they are | `_meta/docs-guidelines.md` |
| What the docs CLI does, and which command to run | `_meta/tools.md` |
| Writing rules for every document | `_meta/ste-writing.md` |

Add a row here when a new class of fact gets an owning document. Do not restate the fact.

## 4. Which documents your task needs

Assembled from each document's `read_when`. Read the path, not the library.

| Your task | Read, in order |
|---|---|
| Any task | this file |
| Deciding whether something is in scope | [`product/overview.md`](./product/overview.md) |
| Changing what the MVP or a roadmap feature does | [`product/overview.md`](./product/overview.md), then the [glossary](./product/glossary.md) |
| Writing any text that uses a product term | [`product/glossary.md`](./product/glossary.md) |
| Writing or changing any document, including a procedure, an agent rule, a prompt or a `## Behaviour` section | [`_meta/ste-writing.md`](./_meta/ste-writing.md) |
| Planning the next piece of work | [`backlog.md`](./backlog.md) |
| Capturing a transcript, a meeting note or a dump | drop it in `inbox/` |
| Leaving documentation in order after a change | `_meta/authoring.md` |
| Reorganizing the documentation itself | `_meta/librarian.md` |
| Running a maintenance pass, or automating a check | `_meta/tools.md` |
| Questioning a documentation rule | `_meta/docs-guidelines.md` |
| Checking which phase rules apply | `_meta/phases.md` |

Extend this table when a new document's `read_when` names a task this list does not cover.

## Related docs

- [`_meta/authoring.md`](./_meta/authoring.md): the duty every contributor owes this library
- [`_meta/librarian.md`](./_meta/librarian.md): the rulebook behind how this map is built
- [`_meta/phases.md`](./_meta/phases.md): which clauses of that rulebook are in force
- [`backlog.md`](./backlog.md): everything unresolved, project-wide
