---
id: meta-librarian
title: Librarian rulebook
kind: meta
status: current
summary: How `_docs/` is organized, and how a bookkeeper agent keeps it that way.
read_when: you are creating, moving, splitting or deleting a document, or you run a maintenance pass
updated: 2026-11-05
verified: 2026-11-05
review_cycle: quarterly
---

# Librarian

This is the rulebook for the documentation, not for the product. Read it before you create, move,
split or delete anything under `_docs/`. It has two audiences. One is a human who decides where a document
belongs. The other is a **bookkeeper agent** on a maintenance pass (§8). If a claim you distilled touched a
document, read [`authoring.md`](./authoring.md) instead. It is the full duty of a contributor.

The library serves agents that arrive with no memory of previous work. Every rule below makes one
thing cheap: find the two or three documents a task needs, and trust them.

**[`phases.md`](./phases.md) selects the clauses in force.** The folders mean the same thing in every
phase. What is allowed, required and empty changes. Read the current phase before a maintenance pass.
Do not apply development checks to an ideation library, or the reverse.

**Before a maintenance pass, read these files:**

1. This file.
2. `authoring.md`, so that you do not "fix" what contributors were told to do.
3. `phases.md`, for the clauses in force.
4. `../Home.md`, for the catalogue and the fact-ownership registry.
5. `feedback.md` and `review-log.md`, so that you do not repeat a rejected proposal or redo work.

If a rule itself looks wrong, also read [`docs-guidelines.md`](./docs-guidelines.md). It holds the
reasons, and it is the only place to argue with a rule.

The mechanical checks run from one CLI: `mise run docs-lint` and its siblings. [`tools.md`](./tools.md)
is the command reference. It tells which action runs which check, and which actions write.

## 1. The library

Folders encode **kind of knowledge**. Frontmatter encodes **stability**. Never mix the two. A
`drafts/` folder only duplicates `status: draft`.

| Path | Holds | Written for |
|---|---|---|
| `Home.md` | The map: catalogue, fact-ownership registry, reading paths | Every agent, first |
| `backlog.md` | Every open question, known gap and deferred item of the project | Whoever plans the next work |
| `product/` | Why Splitwise Lite exists, in business terms. **No code references.** | Product decisions |
| `features/` | One document per named capability. Contract on top, implementation below | Building or changing a capability |
| `tech/` | Cross-cutting models, rules and conventions inside the solution | Any modelling or implementation task |
| `infra/` | Build, deploy, environments, quality gates | Changing how the system is built or run |
| `wip/` | Notes for the task in flight. Deleted when the task closes | The task in flight |
| `inbox/` | Raw input: transcripts, dumps, pasted drafts. Preserved, never edited | Nobody yet. To be filed |
| `_meta/` | How this library works. The underscore means "not project knowledge" | The bookkeeper |

`tech/` and `infra/` split on the deployment boundary. A rule that constrains code inside the
solution is `tech/`. A rule about the machinery that builds, ships or runs the solution is `infra/`.

Only `wip/`, `inbox/` and `_meta/` documents can talk about time: before and after states, deltas,
maintenance cycles. For every other folder, see §5.

**`_design/` is outside the library.** It holds design artifacts: the web app design in HTML and the
component storybook. These are not documents and carry no frontmatter. A future `tech/` document
points into `_design/` through its `source_anchors`. It does not copy the design into prose.

Every file is plain markdown and stays valid on any renderer. Links are relative markdown links,
never wikilinks.

## 2. Where a document goes

The placement rule decides the business-versus-technical question without a third category:

> **If you delete the capability from the product and the document goes too, it belongs in
> `features/`. If the document survives, it belongs in `tech/` or `infra/`.**

Applied:

- A named capability that a member sees goes to `features/`. Delete the capability, and the document
  goes.
- A cross-cutting model, for example how money is stored in minor units, goes to `tech/`. It survives
  the deletion of one capability.
- A build, release or environment procedure goes to `infra/`. It survives the deletion of every
  feature.
- A business invariant ("the app never moves money") goes to `product/`. If it is an architecture
  rule, it goes to `tech/`.
- A raw transcript goes to `inbox/`.
- Exploration notes for the task in flight go to `wip/`.

Then, in order:

1. If it is unprocessed input, put it in `inbox/` and stop.
2. If it is notes for the task in flight, put it in `wip/` and stop.
3. If it is about the documentation, put it in `_meta/`.
4. If it is open, write an entry in `backlog.md`. Do not create a document.
5. If it is business-only, with no code, put it in `product/`.
6. Otherwise, apply the placement rule.

**Prefer to extend an existing document.** A new file needs a reader who cannot find the material
where it is. If that is not obvious, say so in the `summary`.

## 3. Document anatomy

Each kind has a fixed section order. An agent skims to the part it needs and stops reading.

### 3.1 Feature document

```markdown
## Purpose               2–4 sentences. The outcome that a member sees.
## Behaviour             The contract: rules, invariants, edge cases, what is forbidden.
## Data                  The shapes the capability reads and writes.
## Implementation        Where it is in the tree, and how the pieces fit. Describes, not prescribes.
## Failure & idempotency What happens when it breaks, and what is safe to retry.
## Assumptions           What must stay true for the behaviour to hold.
## Related docs          One list. The only place where a link can repeat.
## Next steps            Optional, 8 bullets at most, no dates.
```

`phases.md` selects which of these sections are in force. In product ideation, a feature document is
the contract only: `## Purpose`, `## Behaviour`, `## Assumptions`, `## Related docs`.

A reader who has not seen the source must be able to check `## Behaviour`. `## Behaviour` follows the
STE dialect of [`ste-writing.md`](./ste-writing.md). The seam between *Behaviour* and
*Implementation* is where the document stops prescribing and starts describing. The drift check
(**L3**) and the mismatch rule in §8 turn on that seam.

### 3.2 Technical or infrastructure document

```markdown
## <what it is>       One paragraph: the shape of the thing.
## <rules or model>   The substance: normative rules, the model, or reference tables.
## <rationale>        Why it is this way, where a reader would propose the alternative.
## Related docs
```

Write rationale only where it stops someone from "fixing" the design.

### 3.3 Product document

```markdown
## Purpose
## Scope
## Non-goals
## Related docs
```

No file paths, no function names, no code. If a product document needs one, the sentence belongs in
a feature document. The glossary is a register and has its own table shape.

Every skeleton ends with *Related docs*. A `_meta/` document takes the technical shape. A `wip/` note
takes the shape its task needs. Its only obligations are frontmatter and a heading that names the task.

## 4. Balance

### 4.1 Length

The target is **150–400 lines**. The ceiling is **500**.

- If a document is longer than 500 lines, split it **by reader intent**. Never slice by topic into
  `part-2` files.
- If a document is shorter than 80 lines and has no independent reader, fold it into its parent.

`Home.md`, `backlog.md`, the glossary and flat reference registers are exempt from both bounds. A
reader looks them up and does not read them through.

### 4.2 Content type

There are five types: **rationale · normative rules · reference tables · procedures · catalogue**.

At most **two** types dominate one document.

**A procedure never lives inside an architecture document.** They have different readers, different
half-lives and different failure modes when stale.

### 4.3 Fenced material

Fences hold what prose cannot carry: a frontmatter example, a skeleton, a sketch.

- Fenced blocks take at most **15%** of the lines of a document. Each fence has at most **20 lines**.
- Beyond that, name the source file and delete the block.
- **Never cite line numbers.** They rot. A path plus a symbol is stable, and grep finds it.

## 5. Timelessness

Documents in `product/`, `features/`, `tech/` and `infra/` use the present tense. They describe only
what is true. A reader must never reconstruct a timeline to know the state of things.

**Banned phrases** (grep for these):

```
now  already  no longer  used to  previously  currently  not yet
will be  has been added  was changed  after task  in the old
```

A status banner that says a document disagrees with another document is banned. That condition is a
`wip/` note or a `backlog.md` entry, never a header.

History has three homes:

- **git**, once it exists: what changed and when.
- **A decision register in `tech/`**, once one is filed: why this and not the alternative. A decision
  can name what it replaced, because the rationale stays true.
- **`_meta/review-log.md`**: what the bookkeeper did.

Forward-looking content has two places: the final `## Next steps` of a document (capped, no dates, no
promises), and `backlog.md`.

## 6. Frontmatter

Every document under `_docs/` has frontmatter. [`authoring.md`](./authoring.md) owns the field list
and the meaning of each field. This section holds only the reasons for the fields.

`id` prefixes mirror the folder: `prod-`, `feat-`, `tech-`, `infra-`, `meta-`, `wip-`. Never change
an `id`. `depends_on` cites ids so that a renamed or moved file does not break the graph. A file
rename is free. An `id` rename is not.

**`read_when` is the field that gets a document opened.** Reject a lazy one. `summary` tells what a
document contains. `read_when` names the task that must lead a reader to it: "you are changing how a
balance is computed", not "balances". `Home.md` builds its reading paths from these lines.

A register that is read only in some conditions opens with a short trigger table: "if you are about to
do X, read row Y". Its `read_when` points at the table. A register is read before you change a
constraint, not before you follow one.

**`updated` versus `verified` carries the weight.** File history records when a file was touched. It
cannot record when someone last compared the document with reality. `verified` plus `source_anchors`
answers the maintenance question: did an anchored source change after the last comparison? That turns
upkeep from a judgement call into a queue.

The tool maintains `updated` and never `verified`. `updated` is a fact about the file, so a machine
reads the file timestamp and repairs the field (check **L11**). `verified` is a claim that someone
looked. No timestamp can supply it, so it moves only when somebody names the document.

**The freshness comparison is soft.** A delta inside the tolerance of 2 days counts as fresh. A hard
comparison flags every document edited a minute after its stamp, and nobody runs a check that cries
wolf. If a new `updated` passes `verified`, queue the document for a check. Do not bless it.

`review_cycle` drives the third freshness question: did this document go unchecked longer than its
cadence? Use `monthly` for an area that changes often. Otherwise, use `quarterly`.

`source_anchors` names the two or three sources a reader opens next. These are code files, design
files in `_design/`, or the inbox capture of a claim. Omit it for `product/` and `_meta/` unless a claim
comes from one specific capture.

## 7. Cross-references

- **One fact, one owner.** Each class of fact has exactly one owning document. Everyone else links.
  `Home.md` holds the ownership registry. `product/glossary.md` owns the vocabulary.
- **Derived content is generated or linked, never copied.** Script output between markers or a pointer
  replaces document listings and command tables. Copies made by hand drift. Run `mise run docs-index` to
  regenerate the catalogue.
- **A link target appears at most three times in one document.** One of them is in `## Related docs`.
  Two inline mentions are the budget for a load-bearing dependency.
- **Cite across documents by title, not by section number.** Section numbers break when a document is
  reorganized. Write "see the balance rules in `product/overview.md`", not "§2.7".
- **Cite a source by path, plus a symbol where it helps.** Never a line number (§4.3).

## 8. The bookkeeper

### 8.1 Powers and limits

> **The bookkeeper rewrites form and proposes substance.**

**The bookkeeper can act directly:**

- Fix frontmatter.
- Regenerate the `Home.md` catalogue.
- Stamp an `updated` field that the file timestamp outran (§6).
- Move, split or merge documents per §2 and §4.
- Repair broken links and `source_anchors` paths.
- Rewrite transient phrases into the present tense.
- Move open questions into `backlog.md`.
- Delete `wip/` documents whose task closed. Keep `wip/.gitkeep`: it keeps the empty folder in git.
- File `inbox/` items, that is, distill them into the library.

**The bookkeeper never edits an inbox file.** The library preserves the inbox raw.

**The bookkeeper never stamps `verified`** on a document it did not check.

**The bookkeeper proposes and does not act** on these:

- A change to a normative rule, a product decision or a domain invariant.
- A new rule.
- A resolution or a new priority for a backlog item.
- A judgement that a documented behaviour is wrong.
- A change of the project phase.

Without that line, a documentation agent becomes an architect. Then the library stops being a true
record of what humans decided. When in doubt, the material is substance.

**On a mismatch, apply the direction rule.** Some documents describe a source and yield to it.
Others prescribe and outrank it. `authoring.md` owns that rule. `phases.md` says what counts as a
source in this phase.

**The bookkeeper detects drift and does not resolve it.** It finds mechanically that an anchored
source changed after `verified`. It cannot judge whether the document still holds. Fix a descriptive
mismatch only when the change is unambiguous. Queue everything else for the owner of the claim. A
`verified` stamp on a document nobody read is the worst outcome. It turns "unknown" into "confirmed".

**Record contradictions. Do not resolve them silently.** If two documents disagree, write the
disagreement down with both sides. Put a project question in `backlog.md`. Put a documentation
question in `_meta/feedback.md`. A winner picked quietly destroys the evidence of a real question.

### 8.2 Triggers

| Trigger | Scope |
|---|---|
| A task changed a product claim, and later code | The documents that own those claims: check them or record drift |
| `inbox/` has a file other than `.gitkeep` | Classify and file, or propose a new document. Never edit inbox items |
| A workshop or a meeting note lands | Distill into `product/`, `features/` or `backlog.md`. Do not keep the only copy in a capture |
| Weekly | Light pass: L1, L4, L5, L7, L9, L11, L12 |
| Monthly | Deep pass: the drift queue (L3) plus the light pass |
| Quarterly | Full pass: L1–L12, `backlog.md` triage, and a check that the taxonomy and bands still fit |
| On request | As asked |
| A human changes the phase | Align `AGENTS.md`, `Home.md` and the feature skeletons per `phases.md` |

### 8.3 The revision checklist

Cite these ids in reports and feedback entries.

| id | Check | Failure action |
|---|---|---|
| **L1** | Frontmatter parses. `id` is unique. `depends_on` resolves | Fix |
| **L2** | Every markdown link resolves. Every `source_anchors` path exists | Fix the reference, or record drift if the source moved |
| **L3** | No `source_anchors` file changed after `verified` | Read the change. Fix only what is unambiguous. Queue the rest for the owner of the claim |
| **L4** | Length is 150–400 lines (ceiling 500, fold under 80). Fences take at most 15% of lines and 20 lines each | Split, fold, or propose |
| **L5** | No banned phrase in a `status: current` document outside `wip/`, `inbox/` and `_meta/` (§5) | Rewrite in the present tense |
| **L6** | No fact outside its owning document (§7) | Replace the copy with a link |
| **L7** | No orphans: not in the `Home.md` catalogue, `wip/` older than 30 days, `inbox/` older than 14 days | File, list, or delete. Filing an inbox item means distill it. Never delete or rewrite the inbox file |
| **L8** | No `Open questions` or `Known gap` heading in a `current` document | Move the content to `backlog.md` |
| **L9** | No link target appears more than three times in one document | Delete the surplus. Keep the `## Related docs` entry |
| **L10** | The duty pointer to `_meta/authoring.md` is present in `AGENTS.md` and `Home.md` | Restore it before anything else (§8.5) |
| **L11** | No file timestamp outruns its `updated` field by more than 2 days | Stamp it. If `updated` passes `verified`, queue the document for a check |
| **L12** | Each document follows `ste-writing.md` | Rewrite the sentence per `ste-writing.md`. Advisory |

`mise run docs-lint` runs the mechanical checks L1, L2, L4, L5, L7, L9, L10 and L11. L3, L6, L8 and
L12 need judgement about meaning. The reader does these checks. They stay with a capable model.

### 8.4 Reporting

Every pass ends with these three items:

1. A short report: what you checked, what you fixed, what you found and left alone.
2. One row in `_meta/review-log.md`: date, scope, checks run, counts. `mise run docs-log` writes the row.
3. At most **three** new entries in `_meta/feedback.md`.

Never make a silent pass. "Nothing to change" is a result and gets its row.

### 8.5 Keeping the duty discoverable

**A duty that nobody is pointed at does not exist.** Most documents are updated by agents whose job
is the product. They never open this file. They comply only if something that they already read
tells them to, at the moment it applies. These channels are the job of the bookkeeper, and they rank above
tidy prose.

| Channel | Carries | Why it matters |
|---|---|---|
| `AGENTS.md` | The duty in one sentence, and a pointer to `authoring.md` | Always loaded, so it is the only guaranteed channel. It works because it is short |
| `Home.md` | The same pointer, next to the reading paths | Read at the start of a task, by an agent that can skim the preamble |
| `CLAUDE.md` | `@AGENTS.md` | Both tool preambles load the same rules |
| `.claude/skills/ste-writing/` | The STE dialect as a skill | Agents that write procedures or `## Behaviour` find the dialect when they need it |

`mise run docs-touched` is an optional channel. A pre-commit hook and role files can join later, when
they earn their keep. **L10** does not require them.

The two required channels fail independently, so the redundancy is deliberate. The preamble is the
most fragile channel.

**Check L10 on every pass.** A reorganization can drop the pointer from `AGENTS.md`. Then the
upkeep of the library breaks, and every document stays intact.

## 9. Proposing a change

`_meta/feedback.md` is the channel for everything the bookkeeper cannot do itself (§8.1). It is an
append-only table: `id · date · target · kind · rationale · status`. The *kind* is one of
`split · merge · move · rename · rule-change · gap · drift`.

Three rules keep it useful to agents with no memory of previous passes:

- **At most five open entries.** When the ledger is full, report the finding instead of appending.
- **A rejection keeps its reason permanently.** The next bookkeeper does not raise it again.
- **The bookkeeper executes an accepted proposal,** then closes it with what it did.

Write one sentence of rationale per entry. If it needs a paragraph, it is substance. Discuss it with a
human.

## Related docs

- [`phases.md`](./phases.md) — which clauses of this rulebook are in force
- [`authoring.md`](./authoring.md) — the duty of a contributor, and the field list
- [`docs-guidelines.md`](./docs-guidelines.md) — the principles behind these rules
- [`tools.md`](./tools.md) — the `mise run docs-*` command reference
- [`ste-writing.md`](./ste-writing.md) — the STE dialect that L12 checks
- [`feedback.md`](./feedback.md) — the open proposal ledger
- [`review-log.md`](./review-log.md) — what past passes did
- [`../Home.md`](../Home.md) — the catalogue, the fact-ownership registry, and the reading paths
- [`../../AGENTS.md`](../../AGENTS.md) — the always-loaded preamble
