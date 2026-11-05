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

The project phase is **development**. The stack is chosen: Python, FastAPI, Jinja2 HTML with HTMX,
and SQLite. `features/` is the working surface. A `features/` document holds the contract and the
implementation. `tech/` and `infra/` are open. `_design/` is a source.
[`_meta/phases.md`](./_meta/phases.md) is the switch.

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

### Features

| Document | What it is | Verified |
|---|---|---|
| [Balances and transactions](./features/balances.md) | The balance of each member, the transaction list grouped by day with the Mine filter, the member detail breakdown, and the Settled state. | 2026-11-05 |
| [Expenses](./features/expenses.md) | Add, edit and delete an expense with an equal split, the share preview, and the validation of description, amount, expense date, payer and participants. | 2026-11-05 |
| [Groups](./features/groups.md) | The groups home with the balance of the current user, search and filter, create a group, group settings, join with an invite code, the invite dialog and leave a group. | 2026-11-05 |
| [Members](./features/members.md) | The members panel of a group. Add a member from an existing user or a new user, remove, and the join order. | 2026-11-05 |
| [Payments](./features/payments.md) | Record, edit and delete a payment from a sender to a receiver, with amount, payment date and an optional note, and the validation of each field. | 2026-11-05 |
| [Sign in](./features/sign-in.md) | Simulated sign-in without a password. Pick or create a user, sign out, keep one user per browser tab, and return to the page in the `next` parameter. | 2026-11-05 |

### Tech

| Document | What it is | Verified |
|---|---|---|
| [Application architecture](./tech/architecture.md) | The shape of the Splitwise Lite application. Layers, request flow for pages and HTMX fragments, data access, the migration model, the simulated sign-in model, the JSON API position and the reasons for each choice. | 2026-11-05 |
| [Design guidelines and how to read the design](./tech/design-guidelines.md) | How to open and read the files in `_design/`, and the visual and interaction rules of the design. Tokens, themes, type, spacing, motion, icons, layout, component usage, responsive behaviour, accessibility and microcopy. | 2026-11-05 |
| [Design system and templates](./tech/design-system.md) | How the HTML design in `_design/site/` becomes the app. Which files are the source of truth, the page shell, the component macros, the HTMX model for fragments and dialogs, the accessibility rules and the reasons for these choices. | 2026-11-05 |
| [Guide: add an endpoint](./tech/guide-api.md) | Procedures to add a JSON endpoint under /api/v1 and an HTML mutation endpoint that serves htmx, with one short example for each. | 2026-11-05 |
| [Guide: simulated sign-in](./tech/guide-authentication.md) | How the simulated per-tab sign-in works from token to header, how to protect a new route, how to test as two users in two tabs, and the limits of the simulation. | 2026-11-05 |
| [Guide: change the schema](./tech/guide-migration.md) | How to add a schema change as a migration file, the rules for it, how it applies at start and with mise run migrate, how to reset the dev database and how to test a migration. | 2026-11-05 |
| [Guide: pages, fragments, dialogs and components](./tech/guide-navigation.md) | Procedures to add a page, an HTMX fragment, a dialog and a component macro. The URL naming rules, the route owners, the redirect rules and the side-by-side check against the design. | 2026-11-05 |
| [Engineering practices](./tech/practices.md) | The normative rules for code in Splitwise Lite. Settings, logging, error handling, money and dates, transactions, security basics, tests, code style and dependencies. | 2026-11-05 |
| [Project structure](./tech/project-structure.md) | Reference table of every folder and key file of the repository and of the app tree, and the rules for where a new route, template, migration, test or static file goes. | 2026-11-05 |

### Infra

| Document | What it is | Verified |
|---|---|---|
| [Development environment](./infra/dev-environment.md) | How to build and run Splitwise Lite on one machine. The mise tools and tasks, the .env files, the database file in _data/ and where the logs go. | 2026-11-05 |

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
| Architecture and layers | `tech/architecture.md` |
| Repository and app layout, placement rules | `tech/project-structure.md` |
| Settings, logging, errors, testing, code rules | `tech/practices.md` |
| Design system, templates, HTMX patterns | `tech/design-system.md` |
| Visual design rules and how to read `_design/` | `tech/design-guidelines.md` |
| Local run, `mise` app tasks, env files | `infra/dev-environment.md` |
| How-to guides | `tech/guide-*.md` |
| The contract of each bootstrap feature | `features/<slug>.md` |
| The plan of work in flight | `wip/` |
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
| Building or changing a feature in code | [`splitwise-fullstack` skill](../.claude/skills/splitwise-fullstack/SKILL.md), [`tech/architecture.md`](./tech/architecture.md), then the `features/` document of the feature |
| Adding a page or a fragment | [`tech/design-system.md`](./tech/design-system.md), then [`tech/guide-navigation.md`](./tech/guide-navigation.md) |
| Reading the design or styling a component | [`tech/design-guidelines.md`](./tech/design-guidelines.md), then [`tech/design-system.md`](./tech/design-system.md) |
| Adding an endpoint | [`tech/guide-api.md`](./tech/guide-api.md) |
| Changing the schema | [`tech/guide-migration.md`](./tech/guide-migration.md) |
| Protecting a route or working with users | [`tech/guide-authentication.md`](./tech/guide-authentication.md) |
| Running the app | [`infra/dev-environment.md`](./infra/dev-environment.md) |
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
