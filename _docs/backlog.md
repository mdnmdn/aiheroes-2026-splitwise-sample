---
id: backlog
title: Backlog
kind: product
status: current
summary: Every open question, known gap and deferred item, project-wide.
read_when: you plan the next piece of work, or you hit something this project has not decided
updated: 2026-11-05
verified: 2026-11-05
review_cycle: monthly
---

# Backlog

Each line names the document it affects. An empty section is a valid state. This file records what
the project has not decided. It is not a task tracker: it holds no assignees, estimates or dates.

A human resolves an item. Then the answer goes into the owning document, and the line is deleted.

## Open questions

- **Platform for the MVP.** Web app, mobile app or CLI first. The answer opens the development phase
  and the first `tech/` documents. Affects `product/overview.md`, `_meta/phases.md`.
- **Payer outside the participants.** Can a payer pay for an expense without being a participant,
  for example a gift? The specification assumes yes. Affects `product/overview.md`,
  `product/glossary.md` (Payer).
- **Exchange-rate source (F3).** Which source supplies the rate, and what happens offline. Affects
  `product/overview.md`.
- **Base currency change (F3).** Can a group change its base currency later, and how are past
  balances converted. Affects `product/overview.md`, `product/glossary.md` (Base currency).
- **Undo depth (F6).** Is undo limited to the last change, or a full history. Affects
  `product/overview.md`, `product/glossary.md` (Undo).
- **Member who leaves (F9).** What happens to the data of a member who leaves a shared group.
  Affects `product/overview.md`.
- **Product name.** The specification says *Splitwise*. The project says *Splitwise Lite*. A human
  picks one name for the product text. Affects `product/overview.md`, `Home.md`, `AGENTS.md`.

## Known gaps

- **Feature contracts.** The MVP and F1–F9 contracts live inside `product/overview.md`. Each becomes
  a `features/` document when a human has decided enough of it to have its own contract. See `_meta/feedback.md`.

## Deferred

- **Design artifacts.** `_design/` holds the web app design in HTML and the component storybook. Not
  started. A `tech/` document points into it once it exists.
- **Tech stack.** Not chosen. `tech/` and `infra/` stay empty until the development phase.
