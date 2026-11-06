---
id: meta-feedback
title: Proposal ledger
kind: meta
status: current
summary: Append-only ledger of documentation changes that the librarian cannot make alone.
read_when: you are proposing a split, merge, move, rename or rule change, or you look for a proposal that was already rejected
updated: 2026-11-05
verified: 2026-11-05
depends_on: [meta-librarian]
review_cycle: quarterly
---

# Proposal ledger

This ledger is the channel for everything the librarian cannot do itself. Three rules keep it useful
to an agent with no memory of previous passes:

- **At most five open entries.** When the ledger is full, report the finding instead of appending.
- **A rejection keeps its reason permanently.** The next pass does not raise it again.
- **The librarian executes an accepted proposal,** then closes it with what it did.

Write one sentence of rationale per entry. A proposal that needs a paragraph is substance. Discuss it
with a human.

`kind` is one of `split · merge · move · rename · rule-change · gap · drift`.

| id | date | target | kind | rationale | status |
|---|---|---|---|---|---|
| F1 | 2026-11-05 | `product/overview.md` | split | The document holds the MVP specification and the contracts of F1–F9, which can later move into one `features/` document per capability. | open |
| F2 | 2026-11-05 | the STE linter (deleted), check L12 | rule-change | Remove the STE linter script ste_lint.py. L12 becomes a judgement check. The cost and the noise of the linter are higher than its value. The rules document and the `ste-writing` skill are the lever. | closed: accepted. The linter, its tasks and its references are removed. L12 now reads "each document follows `ste-writing.md`" |
| F3 | 2026-11-05 | `tech/design-guidelines.md` | split | The document has 470 lines, above the 150 to 400 target. Split it by reader intent: how to read `_design/` (section 1), visual tokens (sections 2 to 7), component usage rules (section 8), and responsive, accessibility and microcopy rules (sections 9 to 11). | open |
| F4 | 2026-11-05 | `tech/` and `infra/dev-environment.md` | merge | L6: four facts have copies with no clear owner in `Home.md`: the design-sync steps (`design-system.md`, `project-structure.md`, `dev-environment.md`, `guide-navigation.md`), the `db-reset` steps (`dev-environment.md`, `guide-migration.md`), the error table (`practices.md`, `guide-api.md`) and the HTMX events table (`design-system.md`, `guide-api.md`). A human names each owner, then the librarian replaces the copies with links. | open |
| F5 | 2026-11-05 | `product/glossary.md` | gap | L12: tech and feature documents use the terms toast, dialog, fragment, empty state, breakdown and preview, and the glossary has no row for them. The glossary row "Payment" also uses the words "settles debts", which the dialect forbids. | open |
| F6 | 2026-11-05 | `.agents/agents/`, `librarian.md` duty channels | gap | `.agents/agents/coordinator.md` and `.agents/agents/librarian.md` copy the `.claude/agents/` files without the `model`, `skills` and `tools` lines. The duty-channel table does not name them, so nobody keeps the copies in sync. | open |

## Related docs

- [`librarian.md`](./librarian.md) — the rulebook, and what the librarian cannot do alone
- [`review-log.md`](./review-log.md) — what each maintenance pass did
- [`authoring.md`](./authoring.md) — the route of a contributor into this ledger
