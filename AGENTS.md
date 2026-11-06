# Splitwise Lite — agent guide

Splitwise Lite is an app in which a group records shared expenses and sees who owes whom.

Phase: **development**. The app is a web app: Python 3.13, FastAPI, Jinja2 HTML with HTMX, and
SQLite. Follow the tech docs. Do not invent an implementation that they do not describe.

## Where to look

| For | Read |
|---|---|
| Any task: the map of the docs | [`_docs/Home.md`](_docs/Home.md) |
| What the product is and does | [`_docs/product/overview.md`](_docs/product/overview.md) |
| The meaning of a term | [`_docs/product/glossary.md`](_docs/product/glossary.md) |
| Open questions | [`_docs/backlog.md`](_docs/backlog.md) |
| Code in `app/`: skill for a feature, a page or an endpoint | [`.claude/skills/splitwise-fullstack/SKILL.md`](.claude/skills/splitwise-fullstack/SKILL.md) |
| A task with many parts: how to coordinate subagents. Skill, or the agent that loads it as the main agent | [`.claude/skills/coordinator/SKILL.md`](.claude/skills/coordinator/SKILL.md), [`.claude/agents/coordinator.md`](.claude/agents/coordinator.md) |
| Keep `_docs/` in order: a maintenance pass, move or split a doc. Delegate to the librarian agent, or load the librarian skill | [`.claude/agents/librarian.md`](.claude/agents/librarian.md), [`.claude/skills/librarian/SKILL.md`](.claude/skills/librarian/SKILL.md) |
| Architecture and layers | [`_docs/tech/architecture.md`](_docs/tech/architecture.md) |
| Where a file goes | [`_docs/tech/project-structure.md`](_docs/tech/project-structure.md) |
| Settings, logging, errors, tests, code rules | [`_docs/tech/practices.md`](_docs/tech/practices.md) |
| Templates, components, HTMX patterns | [`_docs/tech/design-system.md`](_docs/tech/design-system.md) |
| Reading `_design/`, visual rules, styling | [`_docs/tech/design-guidelines.md`](_docs/tech/design-guidelines.md) |
| Run the app, `mise` app tasks, env files | [`_docs/infra/dev-environment.md`](_docs/infra/dev-environment.md) |
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
README.md   for humans: what the app is, quick start, links into _docs/
mise.toml   tools (Python, uv) and tasks. `mise install`, then `mise tasks`
pyproject.toml  Python project, dependencies and tool settings
.env.example    settings template. Copy it to `.env`. `.env` is not in git
app/        the application: FastAPI, templates, static files, migrations
tests/      unit and integration tests
_docs/      documentation library
_design/    web app design in HTML and the component storybook. A source for the app
_tools/     support scripts: Python, uv, PEP 723 inline metadata
_data/      local dev data, for example the database. Not in git
tmp/        spikes and temporary assets, one subfolder per task. Not in git. Notes go to _docs/wip/
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
- The main agent coordinates. If the user does not specify otherwise, never run more than 3
  subagents at the same time. Give each subagent the smallest model that can do its task.
- For one edit, use the Edit or Write tool, never a script. For a batch of edits, use a script in
  `_tools/` if the script is faster or uses fewer tokens. Tell each subagent the same rule.
- If a task is not clear, ask the user. Use the question tool of the session if it has one. If
  not, ask in the chat. Tell each subagent the same rule.
- Do not stash or revert a change that you did not make. Other agents can work in the same tree.
- Keep each change simple. Be brief.
