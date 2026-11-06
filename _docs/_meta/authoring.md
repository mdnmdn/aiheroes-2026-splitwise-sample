---
id: meta-authoring
title: Writing and updating docs
kind: meta
status: current
summary: The duty of every agent and human who changes a claim, and the small set of edits they can make without the librarian.
read_when: a change or a conversation touched a claim and you are not on a maintenance pass
updated: 2026-11-05
verified: 2026-11-05
depends_on: [meta-phases, meta-ste-writing]
review_cycle: quarterly
---

# Writing and updating docs

This document is for everyone who is **not** on a documentation maintenance pass. That includes
agents and humans who capture product thinking, and agents and humans who change code.

**This document is self-sufficient.** It holds the fields, the placement rule and the cases where you
can create a document. You do not need `librarian.md` for structure and maintenance passes.
You need `docs-guidelines.md` only to argue with a rule. [`phases.md`](./phases.md) names
the folders and skeletons in force. The create-tests below match the current phase, **development**.

**Writing duty.** Every document that you write or change follows [`ste-writing.md`](./ste-writing.md).
Use the mode that its table "Where STE applies" gives for that text. Use only the terms of
[`../product/glossary.md`](../product/glossary.md). If you are a Claude agent, load the `ste-writing`
skill before you write.

No tool checks this duty. A reader checks it (§5). Clear text prevents a wrong expense or a wrong
balance.

If you read nothing else:

1. If a change or a conversation touched a claim, update the owning document in the same session.
2. Put the document update in the same commit as the change.
3. Edit in place. Do not move, split, rename or reorganize anything.
4. Match the document you edit. Its shape is already correct.
5. Write in the present tense. Write no line numbers and no `TODO`.
6. Write in the STE dialect with glossary terms (§5).
7. If you cannot place something, put it in `inbox/`, `backlog.md` or `_meta/feedback.md` (§8).

A stale document is worse than a missing one. A missing document makes the reader look at the
source. The reader believes a stale document.

---

## 0. Find the documents this change touched

Use these three ways, in this order:

1. Read [`../Home.md`](../Home.md). Its catalogue names the owner of each document. Its
   fact-ownership registry names the owner of each kind of fact.
2. Search `_docs/` with grep for the claim, the term or the file you touched. If a document names
   it, check that document.
3. Run `mise run docs-touched` with the files you changed. It names the documents that list those files
   in `source_anchors`.

A contributor needs three commands:

- `mise run docs-touched` finds the documents you must update.
- `mise run docs-lint` tells you if your document is well-formed.
- `mise run docs-stamp` repairs an `updated` field that you forgot.

[`tools.md`](./tools.md) has the other commands. You need them only on a maintenance pass.

If you find no owner and a decided claim or a named capability has no home, go to §2.

---

## 1. Two verbs

You have two verbs: **amend** an existing document, and **append** a row or a bullet to one.

| You can | You cannot |
|---|---|
| Edit any section of an existing document | Move, split, merge or rename anything |
| Append a row to a register or a line to `backlog.md` | Reorganize sections or change the shape of a document |
| Add a bullet to `## Next steps` | Invent a product decision or a rule, or change one that exists |
| Stamp `verified` (§7) | Create a document, except in the cases of §2 |
| Put raw material in `inbox/` | Edit, move or delete an `inbox/` item |
| Add a row to the glossary for a new term (§5) | Leave a `TODO` or an `Open questions` heading in a document |

Content is yours. Structure belongs to the librarian. You know the claim that this change decided.
You do not have a view of the full library, so arrangement is not your decision.

---

## 2. When you can create a document

If a decided claim or a named capability has no document, write its document in this session. You
are the only one who knows it. A librarian who files it later can only guess. The tests are narrow.

> **Product. Open.** Is it a decided business claim with no home? Ask two questions. Is it
> business-only, with no implementation? If you delete that claim from the product, does the
> document go too? If both answers are yes, file it under `product/`.

> **Feature. Open, full skeleton.** Is a named capability that a member sees decided enough to have
> a contract? Ask: if you delete this capability from the product, does the document go too? If yes,
> file it under `features/`.

> **Tech. Open.** Is it a cross-cutting model, rule or convention inside the solution? Ask: if you
> delete one feature from the product, does the document stay? If yes, file it under `tech/`.

> **Infra. Open.** Is it about how the system is built, run, deployed or checked? Ask: if you
> delete one feature from the product, does the document stay? If yes, file it under `infra/`.

If you are not sure, the answer is "no". Use §8 instead. Never create a folder. Never create a second
document for a subject that has one. Extend the existing document.

Run `mise run docs-new <kind> <slug>` to scaffold the file. It writes the correct frontmatter and the
correct section order. Alternatively, copy the nearest sibling in the target folder and replace its
content.

A **feature** document in this phase uses the full skeleton, in this order:

```markdown
## Purpose                  2–4 sentences. The outcome that a member sees.
## Behaviour                The contract: rules, invariants, edge cases, what is forbidden.
## Data                     The records and fields that the capability reads and writes.
## Implementation           How the code does it. It yields to the source.
## Failure & idempotency    What happens on an error or a repeated request.
## Assumptions              What must stay true for this capability to hold.
## Related docs
## Next steps               Optional.
```

A **product** document is `## Purpose`, `## Scope`, `## Non-goals`, `## Related docs`. It has no
file paths, no function names and no code.

---

## 3. When you must update a document

Documentation is part of the change. It is not follow-up work.

| If this change… | Then… |
|---|---|
| Changed a behaviour that a reader acts on | Update the owning product or feature document |
| Touched a file in the `source_anchors` of a document | Check that document (§7) |
| Introduced or changed the meaning of a term | Update `product/glossary.md` first, then the documents that use the term |
| Distilled something from `inbox/` | Write it in the owning document. Do not edit, move or delete the inbox item |
| Made a reversible structural choice | Write one line in `backlog.md` |
| Left something open | Write one line in `backlog.md` that names the document it affects |

Do not invent a decision that the conversation did not make. Name the open question in `backlog.md`
and stop.

---

## 4. Frontmatter

Every document has a frontmatter block at the top. When you amend a document, do these steps:

1. Set `updated` to the day of the change.
2. If §7 applies, set `verified` to the same day.
3. If the document depends on a new source, add it to `source_anchors`.

Do not change the other fields. Never change `id`, because other documents cite it.

When you create a document (§2), write the full set:

```yaml
---
id: feat-example-capability   # stable forever. Prefix mirrors the folder: prod- feat- tech- infra- meta- wip-
title: Example capability
kind: feature                 # product | feature | tech | infra | meta | wip
status: current               # current | draft | superseded
summary: One line. The entry of this document in the Home.md catalogue.
read_when: you are changing how this capability behaves   # the task, not the subject
updated: 2026-11-05           # you changed the content
verified: 2026-11-05          # you compared it with its sources and it held
source_anchors: [inbox/2026-11-05-workshop.md]   # optional: the sources that carry the claims
depends_on: [prod-overview]   # ids, not paths
review_cycle: quarterly       # monthly | quarterly | yearly
---
```

Write `read_when` as the task of the reader: "you are changing how a payment is recorded", not
"payments". `summary` tells what is inside. `read_when` tells when to open it.

Omit `source_anchors` for `product/` and `_meta/`, unless a claim comes from one specific capture.

---

## 5. Language: STE and the glossary

Every document that you write or change follows [`ste-writing.md`](./ste-writing.md). Find the mode
for your text in the table "Where STE applies" of that document.

- Write procedures, agent rules, prompts and `## Behaviour` steps in the procedural mode.
- Write product text and rationale in the flavoured mode. The sentence rules are guidance. The
  vocabulary rules apply in full.
- Take every term from [`../product/glossary.md`](../product/glossary.md). The glossary owns the
  vocabulary.
- If you need a term that is not in the glossary, add a glossary row first. Then use the term.
- Use one word for one concept. Do not rotate synonyms.
- If you are a Claude agent, load the `ste-writing` skill before you write.
- Before you finish, read each sentence that you wrote. Check the sentence against `ste-writing.md`.
  Fix each violation. No linter does this for you.

A reader that picks the wrong meaning of a word builds the wrong rule. One word with one meaning
prevents that.

---

## 6. How to comply without the full rulebook

**Match the document you edit.** Its section order, heading depth, table style and level of detail
are already correct. Copy them.

Then apply six constraints:

1. **Present tense, current state.** Write what is true. Never write "now", "no longer", "used to"
   or "not yet". History belongs to git.
2. **Cite a source as a file path.** Add a symbol name if it helps. Never cite a line number.
3. **Keep implementation out of product documents.** Write no file paths, no function names and no
   code. Link to the owning feature document.
4. **State a fact once, in the document that owns it.** Everywhere else, link to it.
5. **Link to one target three times at most** in one document. One of them is in `## Related docs`.
6. **Update the frontmatter** as §4 tells you.

If your edit takes a document past about 500 lines, make the edit. Then file a split in
`_meta/feedback.md`. Do not split the document yourself.

---

## 7. Verification

`verified` means: someone compared this document with its sources and it held. The sources are a
capture in `inbox/`, a decision of a human, or the code. `verified` does not mean "edited". That
is `updated`.

The tool can repair `updated`, because `updated` is a fact about the file. The tool never writes
`verified`, because `verified` is a claim that a human or an agent looked.

There are three tiers:

1. **Per change. Required.** You changed a claim that this document owns, or a file in its
   `source_anchors`. Read the claims of the document. Fix what does not hold. Then stamp `verified`.
2. **Periodically.** A maintenance pass queues each document whose anchored sources changed after its
   `verified` field. This is a safety net, not the mechanism.
3. **At your discretion.** If you used a document for a task and it held, stamp it. If it did not
   hold, report it (§8).

**If a document and a source disagree, decide which one is authoritative before you edit either.**

- `product/`, a feature `## Behaviour` section and any decision **prescribe**. If the source
  disagrees, the source is wrong, or a human must decide.
- A feature `## Data` and `## Implementation` section, research notes, `wip/` and `inbox/`
  **describe**. The document yields to its source. Fix the document.

Do not edit a prescriptive document to match a later chat. That turns a guess into a specification.

---

## 8. When you cannot comply

Use one of three places. You need no permission for any of them.

- **Raw material that you did not distill.** A transcript, a meeting note or a draft goes to
  `inbox/`.
- **A structural problem.** A document needs a split, a document must not exist, or two documents
  contradict each other. Write one row in `_meta/feedback.md`. For a contradiction, state both sides.
  Do not pick a winner.
- **An open question.** A known gap or a deferred decision goes on one line in `backlog.md`. Never
  write it as a heading inside a document.

Humans have one more power: they change the rules in `_meta/`. Everything else in this document
applies to humans and agents equally.

---

## Related docs

- [`librarian.md`](./librarian.md): the full rulebook, for maintenance passes and structural changes
- [`phases.md`](./phases.md): the create-tests and skeletons in force
- [`ste-writing.md`](./ste-writing.md): the STE dialect that every document follows
- [`../product/glossary.md`](../product/glossary.md): the vocabulary owner
- [`../backlog.md`](../backlog.md): open questions, known gaps, deferred items
- [`docs-guidelines.md`](./docs-guidelines.md): why the rules are what they are
- [`../Home.md`](../Home.md): the catalogue and the fact-ownership registry
