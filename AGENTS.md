# Splitwise Lite — agent guide

Splitwise Lite is an app in which a group records shared expenses and sees who owes whom.

Phase: **product ideation**. No application code exists, and the stack is not chosen. Do not
invent an implementation.

## Where to look

| For | Read |
|---|---|
| Any task: the map of the docs | [`_docs/Home.md`](_docs/Home.md) |
| What the product is and does | [`_docs/product/overview.md`](_docs/product/overview.md) |
| The meaning of a term | [`_docs/product/glossary.md`](_docs/product/glossary.md) |
| Open questions | [`_docs/backlog.md`](_docs/backlog.md) |
| Your duty after a change | [`_docs/_meta/authoring.md`](_docs/_meta/authoring.md) |
| How to write any document | [`_docs/_meta/ste-writing.md`](_docs/_meta/ste-writing.md) |
| The `mise` tasks for docs and tools | [`_docs/_meta/tools.md`](_docs/_meta/tools.md) |
| Which rules apply in this phase | [`_docs/_meta/phases.md`](_docs/_meta/phases.md) |

## Read many files at once

To explore a folder or many files, use `mise run digest`. Do not read the files one at a time.

1. Peek first: `mise run digest --summary _docs` shows the lines, size and tokens of each file.
2. For a large file, see its outline or find a topic: `--headings`, or `--grep 'currency' -C 2`.
3. Then read only what you need: `mise run digest --compact _docs/product AGENTS.md:1-20`.

A range after a colon limits one target. `--max-size` and `--max-file-size` limit the output.
`_docs/_meta/tools.md` gives all the options.

## Repository

```
AGENTS.md   this file. CLAUDE.md loads it
mise.toml   tools (Python, uv) and tasks. `mise install`, then `mise tasks`
_docs/      documentation library
_design/    web app design in HTML and the component storybook (not started)
_tools/     support scripts: Python, uv, PEP 723 inline metadata
_data/      local dev data, for example the database. Not in git
tmp/        scratch space, one subfolder per task. Not in git
refs/       temporary samples from other projects. Not in git. Never a source of project facts
```

## Rules

- If your change touched a document, update it in the same session and in the same commit.
  `_docs/_meta/authoring.md` says how.
- Before you commit a documentation change, run `mise run docs-lint`.
- Write every document in STE. Before you write in `_docs/` or this file, read
  `_docs/_meta/ste-writing.md`. A Claude agent loads the `ste-writing` skill. Tell each subagent
  that writes a document the same rule.
- Use the terms of the glossary. If a term has no row, add the row first.
- If two documents disagree, write it in `_docs/backlog.md`. Do not pick a winner.
- The main agent coordinates. Never run more than 3 subagents at the same time. Give each subagent
  the smallest model that can do its task.
- For one edit, use the Edit or Write tool, never a script. For many repeated edits, use a script in
  `_tools/`. Tell each subagent the same rule.
- Do not stash or revert a change that you did not make. Other agents can work in the same tree.
- Keep each change simple. Be brief.
