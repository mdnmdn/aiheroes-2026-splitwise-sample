---
id: meta-docs-guidelines
title: Documentation guidelines
kind: meta
status: current
summary: The principles and goals behind how `_docs/` is organized. The why beneath the rulebook.
read_when: you are questioning a documentation rule, proposing a new one, or deciding what this library is for
updated: 2026-11-05
verified: 2026-11-05
depends_on: [meta-librarian, meta-phases]
review_cycle: quarterly
---

# Documentation guidelines

This document states what the documentation is *for*, and the principles that produce the rules. It
contains no procedures. Every principle here has an operative counterpart in
[`librarian.md`](./librarian.md). The mapping is in §6. Neither document restates the other.
[`phases.md`](./phases.md) selects which operative clauses are in force. The principles do not change
with the phase. The checks and the skeletons do.

Read this when a rule feels wrong or when you want to add a rule. Also read it when you decide what
belongs in this library.

The approach comes from the *LLM wiki* pattern: a plain-markdown knowledge base that a model queries
and a model maintains. Sources are in §7.

---

## 1. The premise

An agent arrives with no memory. In the first minute of a task, everything it knows about this
project comes from files. Conversations are ephemeral. The library is the durable working memory. It
compounds: every pass that distills something into it makes the next task cheaper.

These documents are first **the working memory of every agent that touches the repository**. The same
agents maintain them. That makes a strict scheme affordable. An agent does not tire of bookkeeping,
does not skip the fifteenth file, and does not forget the index.

Humans are the second audience, and a real one. A human who opens any document must be able to trust
it. Where the two audiences pull the rules apart, the agent wins. In practice they rarely conflict.
A stated purpose, one fact in one place, a current-state description and an explicit *read this
when* also help a human who arrives cold. Onboarding prose, tutorials and narrative flow are not goals
here. A document never gets longer to be more welcoming.

## 2. Three layers

| Layer | What it is | Who writes it |
|---|---|---|
| **Sources** | Conversations, workshop notes and captures in `inbox/`. Later the application tree and `_design/` | Humans, and the work itself |
| **The library** | `_docs/`: compiled, cross-referenced, kept current | Whoever does the work, amending in place. Only the librarian reshapes it |
| **The schema** | `AGENTS.md`, `CLAUDE.md` and `_meta/`: how the library is shaped and maintained | Humans, deliberately |

The layers must not blur. A raw transcript does not become a document when it moves into `product/`.
It becomes one when someone reads it and distills it, and the raw source stays in `inbox/`. The schema
is small and changes rarely. If it starts to change weekly, the shape is wrong. More rules do not fix
that.

**Phases sit in the schema.** The folders are stable. `phases.md` selects what a contributor can
create and whether a feature document describes code. A phase change is a human rewrite of that file.
An agent never infers it.

**Each role reads one part of the schema.** No role reads the part of another:

| Role | Reads | Never needs |
|---|---|---|
| Contributor, any change of thinking or code | `AGENTS.md`, then `Home.md` to find its documents. `authoring.md` once a change touches one. `phases.md` if a create-test looks wrong | This file, `librarian.md` |
| Librarian, on a maintenance pass | `librarian.md`, `authoring.md`, `phases.md`, `Home.md`, `feedback.md`, `review-log.md`. This file when a rule looks wrong | Nothing excluded |
| Human who sets direction | This file, `phases.md`, and the ledger under triage | The mechanics of `authoring.md`, unless writing docs |

A design constraint follows from this.

The file `authoring.md` must be self-sufficient. A contributor who reads
only that file must be able to place a document, fill its frontmatter, and know what not to touch.
Otherwise the rules are out of reach exactly where they matter most. Then the library decays through
diligence rather than neglect.

## 3. Goals

What this library optimizes for, in priority order:

1. **Time to context.** A fresh agent reaches the two or three documents its task needs within one
   read of `Home.md`. Everything else is subordinate to this.
2. **Trust.** A reader can believe a document without a look at its source. Without trust, agents
   read the source anyway and the library is dead weight.
3. **Coverage without sprawl.** Every part of the system has a document, and the reader can find it.
   That puts a ceiling on document count, not only on document length.
4. **Low maintenance cost.** Upkeep is mechanical enough for a cheap model or a script. Nobody
   maintains a scheme that only a careful human can maintain.

## 4. Principles

**G1. The library is compiled, not looked up again.** Knowledge is processed once, when it arrives,
into the document that owns it. Agents do not derive it again from raw material on every task. An
`inbox/` item is work in progress until someone distills it.

**G2. Write for a reader with no memory.** No "as discussed". No dependence on another document read
first. No assumption that the reader was in the meeting. Every document says what it is about in its
first two sentences.

**G3. Organize for lookup, not for reading through.** A model reads three files and stops. It does
not browse. So the library uses predictable folders, one-line summaries, fixed section orders, stable
ids and explicit *read this when* triggers. This applies to the rules too. A duty that nobody is
pointed at does not exist. The schema must be reachable from what an agent already reads.

**G4. Know which side is the source of truth.** Intent versus evidence. Product claims, invariants,
`tech/` rules, a feature *Behaviour* section and decisions **prescribe**. If the code or a later chat
disagrees, the code or the chat is wrong, or a human must decide. The *Implementation* and *Data*
sections, research notes and `inbox/` **describe**. They yield when the source changes. If you get
this backwards, the library quietly ratifies whatever the code does.

**G5. One fact, one home.** A claim stated twice soon disagrees with itself. The second copy is the
stale one, and the reader cannot tell which copy they read. Links replace copies. A script generates
derived material, or the library does not keep it.

**G6. Present tense, current state.** A document describes what is true. A reader never reconstructs
a timeline to know the state of things. History has value, but it lives in git, in decision rationale
and in the review log. It does not live in prose.

**G7. Record contradictions. Do not resolve them silently.** If two documents disagree, write an entry with both sides named. Do the same if a compiled
claim disagrees with its capture. An agent that quietly picks a
winner destroys the only evidence of a real question. The next agent picks differently.

**G8. Everyone writes. Only the librarian reshapes. Only humans decide.** Whoever changes thinking or
code amends the documents it touched, in the same session. Only that contributor knows what changed.
The librarian owns structure: placement, splits, indexes, drift queues. Humans own substance: what
the product is, what the rules are, and which phase is current. An agent never turns a guess into a
permanent product fact. That is the one failure this library cannot recover from.

**G9. Documentation is part of the change, not follow-up work.** Distill in the same session as the
change. Once git exists, commit the update in the same commit as the change. Deferred documentation is
never written. A stale document is worse than a missing one. Absence leads the reader to the source.
A reader believes a stale document. Whoever made the change is the cheapest competent checker of what
it anchors.

**G10. A document earns its tokens.** The measure of a document is what it saves the next task.
Length, repetition, restated links and ceremonial prose are costs on every read. When a document stops
earning its tokens, cut it. Do not grow it.

**G11. Plain files, no tooling required.** The library is markdown in the repository. Any editor reads it,
grep searches it, and a diff shows its changes. Obsidian and `_tools/docs.py` make the work easier.
Nothing essential depends on either of them.

**G12. Controlled language.** One word has one meaning, and one meaning has one word. The project
uses a dialect of ASD-STE100 Simplified Technical English for procedures, agent rules and feature
*Behaviour*. `product/glossary.md` is the dictionary. A term that is not in the glossary does not
exist until a row defines it. An agent that reads "balance" with the wrong sign builds the wrong rule.
A human who reads a synonym assumes a second concept. Controlled language removes both errors at the
cost of some style.

## 5. Non-goals

- **Not a handbook.** Onboarding paths, tutorials, walkthroughs and tone belong to a different kind of
  document.
- **Not an API reference.** Documents name the source (a file, a symbol, a design) and stop.
- **Not a history.** Git holds history. The only narrative kept is *why a decision was made*.
- **Not project management.** `backlog.md` records what is open. This library does not track sprints,
  assignees or estimates.
- **Not exhaustive.** A document that must list everything is wrong everywhere. State the rule and one
  example.
- **Not a pitch deck.** This library records what is true and what humans decided. It does not
  persuade.

## 6. How these become rules

Each principle has an operative home, and the rules live there. Where two documents appear against one
principle, they carry different halves of it. `authoring.md` says what a contributor must do.
`librarian.md` says what a maintenance pass does. `phases.md` adds no principles. It selects which
skeletons and checks are live.

| Principle | Enforced by |
|---|---|
| G1, G2 | `librarian.md`: placement rules, document anatomy, `inbox/` handling |
| G3 | `Home.md` reading paths · `read_when` and `summary` · fixed section orders · check **L10** |
| G4 | The mismatch rule in `authoring.md` · `source_anchors` and `verified` · `phases.md` for what counts as a source |
| G5 | The fact-ownership registry in `Home.md` · check **L6** |
| G6 | The timelessness rules in `librarian.md` · check **L5** |
| G7 | `backlog.md` and `_meta/feedback.md` · check **L8** |
| G8 | `authoring.md`: the two verbs · `librarian.md`: the powers of the bookkeeper · `phases.md`: humans name the phase |
| G9 | `authoring.md`: the same-session duty · check **L11**, which finds the date left behind |
| G10 | The length, content-type and fence bands · checks **L4** and **L9** |
| G11 | The shape of the repository: plain markdown, no generator, no database |
| G12 | `ste-writing.md` and `product/glossary.md` · check **L12**, a judgement check by the reader |

If a rule has no principle here, it is a preference, and you can drop it. If a principle here has no
rule, it is decoration.

## 7. Lineage, and one deliberate difference

The pattern comes from the LLM-wiki notes of Andrej Karpathy
([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f),
[summary](https://www.mindstudio.ai/blog/andrej-karpathy-llm-wiki-knowledge-base-claude-code)). It
has markdown pages with frontmatter, an index regenerated on every ingest, an append-only log, and a
schema file that describes the arrangement. It has three workflows: **ingest, query, lint**. The model
does the bookkeeping that normally makes humans abandon a wiki. This library adopts all of that.
`inbox/` is ingest. The reading paths of `Home.md` are query. Checks L1–L12 are lint.

**The difference worth knowing.** That pattern compiles a library from *immutable* raw sources, so a
correct page stays correct. Here the sources are changing thinking, and later a changing codebase.
Drift is the dominant failure mode, not an edge case. So documents carry `source_anchors` and a
`verified` field, and a reader can compare a claim with the file that carries it. In a research wiki,
the source is always right. Here, product claims and decisions outrank a later chat, and half the
library outranks the code it describes.

## 8. Renderers, one file

The library has the shape of a vault by construction: markdown, YAML frontmatter, folders by kind,
links between files. Three things read it:

| Renderer | What it adds | What it constrains |
|---|---|---|
| Plain markdown (editor, GitHub, grep) | The baseline. Every file reads correctly here | Relative markdown links only |
| Obsidian (optional) | Graph view for orphans and clusters, backlinks, queries over `kind`, `status` and `verified` | Nothing, if links stay relative markdown |
| `_tools/docs.py` | The mechanical checks, the catalogue, the drift queue | Frontmatter parses, and `source_anchors` name real files |

If you use Obsidian, open the repository as the vault, not `_docs/`. Then a backlink from a document
to its anchors stays inside one graph.

One constraint holds for all three. Every file stays valid on a plain markdown renderer. Nothing
essential depends on a plugin or on the tool (G11). So use **relative markdown links, never
wikilinks**. A `[[wikilink]]` renders as literal text outside Obsidian.

---

## Related docs

- [`authoring.md`](./authoring.md) — the duty of everyone who is not the librarian
- [`librarian.md`](./librarian.md) — the operative rules that these principles produce
- [`phases.md`](./phases.md) — which of those rules are in force
- [`ste-writing.md`](./ste-writing.md) — the STE dialect behind G12
- [`../product/glossary.md`](../product/glossary.md) — the dictionary
