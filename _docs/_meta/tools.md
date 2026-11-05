---
id: meta-tools
title: Docs tooling reference
kind: meta
status: current
summary: Every action of the documentation CLI, what each one checks or writes, and which rule it discharges.
read_when: you are running a maintenance pass, or you want to know whether a check can be automated
updated: 2026-11-05
verified: 2026-11-05
depends_on: [meta-librarian]
source_anchors: [_tools/docs.py, _tools/digest.py, mise.toml]
review_cycle: quarterly
---

# Docs tooling reference

Two Python scripts in `_tools/`, `docs.py` and `digest.py`. Each is a uv script with inline PEP 723
metadata. The tasks in `mise.toml` at the repository root wrap them. `mise install` installs Python and uv. `mise tasks`
lists the tasks. Use either form:

```bash
mise run docs-lint             # the task
uv run _tools/docs.py lint     # the same command
```

A task passes extra arguments to its script: `mise run docs-new feature uneven-splits`.

Nothing in this library depends on the tools. They make the mechanical half of
[`librarian.md`](./librarian.md) cheap. A reader owns the judgement half: L3, L6, L8 and L12. The rulebook
defines what the checks mean. This document is the lookup table for what to type.

## Which command you want

| If you are about to | Run |
|---|---|
| Commit a documentation change | `mise run docs-lint` |
| Add a document to the library | `mise run docs-new <kind> <slug>` |
| Find the documents that a code change affects | `mise run docs-touched` |
| Start a maintenance pass | `mise run docs-stats`, then `mise run docs-lint` |
| Find what fell out of date | `mise run docs-changed`, `mise run docs-drift`, `mise run docs-review` |
| Repair the dates that the tool can repair | `mise run docs-stamp` |
| Record that you checked a document yourself | `mise run docs-verify <paths>` |
| Clear the filing queue | `mise run docs-inbox` |
| Close a pass | `mise run docs-log` |

## The actions

### Reading the library

| Command | Does | Writes |
|---|---|---|
| `docs-lint [paths]` | Runs the mechanical checks L1, L2, L4, L5, L7, L9, L10, L11. `--json` gives machine-readable output. Exits 1 on any failure | nothing |
| `docs-stats` | Counts per folder, `status` breakdown, length bands, documents without anchors, oldest verification, inbox depth, last logged pass | nothing |
| `docs-graph` | The `depends_on` graph: roots, cycles, isolated documents, hubs with more than five inbound edges | nothing |
| `docs-inbox` | The filing queue: each capture with its age, its size, and whether any document names it. Flags a file older than 14 days, as L7 does | nothing |
| `docs-touched [paths]` | Inverts `source_anchors`: the documents that you owe an update. With no paths, it uses the working diff. When git is absent, it uses the files changed in the last two days | nothing |

### Finding what fell behind

Three different questions:

| Command | Asks | Check |
|---|---|---|
| `docs-changed [days]` | Has the file moved since its `updated` date? | L11 |
| `docs-drift` | Has an anchored file moved since the `verified` date of the document? | L3 |
| `docs-review` | Has the `review_cycle` of the document elapsed since its last verification? | none |

`docs-changed` is soft. It compares the `updated` date of each document with the date of the file.
The date of the file is its last git commit, or its mtime when git has no commit for it. A difference inside the tolerance counts as
current. The tolerance is 2 days by default. `mise run docs-changed 0` gives a strict answer.

`docs-review` consumes the `review_cycle` field: `monthly` is 30 days, `quarterly` is 91 days,
`yearly` is 365 days. A document without the field counts as quarterly. The command reports. The
reader decides whether the document still holds.

`docs-drift` detects the possibility of drift only. To judge whether a claim survived a change, a
reader must know what the change meant.

### Writing

Each command that writes is narrow on purpose.

| Command | Writes | Guard |
|---|---|---|
| `docs-index` | The generated catalogue between the `<!-- generated:begin catalogue -->` and `<!-- generated:end catalogue -->` markers in `Home.md` | `docs-index-check` fails instead of writing |
| `docs-stamp` | The `updated:` line of the documents that L11 flags | Rewrites that one line only. `docs-stamp-check` shows the plan first |
| `docs-verify <paths>` | The `verified:` line of the documents that you name | Refuses to run without paths. No flag stamps the whole library |
| `docs-log` | One row appended to [`review-log.md`](./review-log.md) | Append only. It never rewrites a row |
| `docs-new <kind> <slug>` | A new file with the frontmatter and the section order of its kind | Refuses to overwrite |

The catalogue lists the Product, Features, Tech and Infra documents. `Home.md` links the `_meta/`
documents by hand, so the catalogue leaves them out. When the source roots are set in
`_tools/docs.py`, the tool also builds the code-symbol checks and the code-map tree. Without source
roots, both do nothing.

`docs-log` takes `--scope`, `--checks`, `--counts` and `--notes`. The date is the date of the run.

`docs-sync` runs the index rebuild and the stamp in one pass. It takes the freshness snapshot before
the rebuild writes. Then the rebuild does not make `Home.md` look stale in the same run.

**`docs-stamp` never changes `verified`.** `updated` is a fact about the file. A machine can read it
from the filesystem and repair it. `verified` is a claim that a person looked, and no timestamp can
supply it. When a stamp leaves `updated` ahead of `verified`, the tool lists the document for
verification. To clear that list, read the document, then name it to `docs-verify`.

`docs-new` supplies these sections: product has Purpose, Scope, Non-goals and Related docs. A feature
has Purpose, Behaviour, Assumptions and Related docs. A tech or infra document has What it is, Rules,
Rationale and Related docs. The tool cannot add the new document to the reading paths of `Home.md`.
Do that by hand.

## Reading many files: `digest`

`mise run digest` reads many files in one call, with a size budget. It is not a docs check. It
is a reading tool for agents. A target is a file or a folder. The tool reads a folder recursively.

| To | Run |
|---|---|
| Peek: see each file with its lines, size and approximate tokens | `mise run digest --summary _docs` |
| See the outline: headings (Markdown) or `def` and `class` (Python), with line numbers | `mise run digest --headings _docs` |
| Find the lines about a topic, with 2 lines of context | `mise run digest --grep 'currency' -I -C 2 _docs` |
| Read the head of each file | `mise run digest --lines 1-15 _docs` |
| Read some lines of one file | `mise run digest _docs/backlog.md:20-40 AGENTS.md` |
| Read everything with fewer tokens | `mise run digest --compact --no-frontmatter _docs/product` |

- A range after a colon applies to that target only: `file:10-40`, `file:-20`, `file:100-`,
  `file:1-10,50-60`. `--lines` sets the range for the other targets. If you give the same file
  two times, the tool reads the union of the ranges. A bad range stops the tool with an error.
- `[...]` marks the lines that the tool skipped between two printed parts.
- `--grep` and `--headings` add line numbers. The tool lists the files with no match at the end.
- `--compact` removes trailing spaces, extra inner spaces, table padding and repeated blank lines.
  It keeps the indentation and the spacing inside code fences. `--no-blank` removes all blank
  lines. `-n` adds line numbers.
- `--max-file-size` (default 20k) cuts a long file. The cut line gives the range of the rest, for
  example `Rest: notes.md:5-10,15-17`. Give that target to the next call.
  `--max-size` (default 100k) stops the output. The tool lists the files that it did not print.
- `--include '*.md'` and `--exclude GLOB` filter the files of a folder. The tool skips binary
  files, dotfiles and folders such as `.git` and `.venv`.

First run `--summary`, then `--headings` or `--grep` for a large file. Then read only the files or
ranges that you need. On prose, `--compact` saves about 1–6% only. A range saves much more.

## Where the tool stops

The tool reads frontmatter, file timestamps, git history and markdown structure. It has no opinion on
whether a claim is true. A reader owes the library every check the tool cannot make:

- L6: a fact sits in its owning document.
- L8: no unresolved question hides inside a document instead of `backlog.md`.
- L3: a document still holds after a change to its source.
- L12: agent-facing text follows `ste-writing.md`.

A green `docs-lint` means that the library is well formed. It does not mean that the library is right.

Two mechanical limits apply. First, without git, or for an untracked file, the file date is the mtime.
The mtime reads as "changed on that day" until the first commit. Second, a document with no
`source_anchors` cannot be drift-checked, so `docs-stats` counts those documents.

## Related docs

- [`librarian.md`](./librarian.md): the checks that these commands run, and what to do when one fails
- [`authoring.md`](./authoring.md): the duty that a contributor discharges with `docs-touched` and `docs-lint`
- [`ste-writing.md`](./ste-writing.md): the dialect that check L12 applies
- [`../Home.md`](../Home.md): the map, and the catalogue that `docs-index` regenerates
