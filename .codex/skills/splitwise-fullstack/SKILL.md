---
name: splitwise-fullstack
description: Build or change the backend or fullstack code of the Splitwise Lite app (Python 3.13, FastAPI, Jinja2, HTMX, SQLite with plain SQL, uv, mise). Use to implement or change a feature, a page, an HTMX fragment, an endpoint, a migration, sign-in, or tests in the app. Not for docs-only work. Use ste-writing for that.
---

# Splitwise Lite fullstack code

Use this skill to write app code. The docs own the design. Do not invent a design.

## 1. Before you code

1. Read `../../../_docs/Home.md`. Follow the reading path for your task.
2. Read the feature doc for your task. The folder is `../../../_docs/features/`.
3. Read the guide for your task. Use this table.

| Task | Read |
|---|---|
| Page or HTMX fragment | [design-system](../../../_docs/tech/design-system.md), [guide-navigation](../../../_docs/tech/guide-navigation.md) |
| Dialog or component macro | [design-system](../../../_docs/tech/design-system.md), [guide-navigation](../../../_docs/tech/guide-navigation.md) |
| Read the design, style a page or a component | [design-guidelines](../../../_docs/tech/design-guidelines.md) |
| Endpoint (JSON or HTML mutation) | [guide-api](../../../_docs/tech/guide-api.md) |
| Schema or migration | [guide-migration](../../../_docs/tech/guide-migration.md) |
| Protected route, users | [guide-authentication](../../../_docs/tech/guide-authentication.md) |
| Settings, logging, errors, tests | [practices](../../../_docs/tech/practices.md) |
| Layers and request flow | [architecture](../../../_docs/tech/architecture.md) |
| Where a new file goes | [project-structure](../../../_docs/tech/project-structure.md) |
| Run the app | [dev-environment](../../../_docs/infra/dev-environment.md) |
| Meaning of a term | [glossary](../../../_docs/product/glossary.md) |

## 2. Hard rules

- Call the layers in this order: routes or api, then service, then repo, then the database. Do not skip a layer. See [architecture](../../../_docs/tech/architecture.md).
- Write SQL in `repo.py` only. See [architecture](../../../_docs/tech/architecture.md).
- Store money as an integer in minor units with a currency code. Never use `float`. See [practices](../../../_docs/tech/practices.md).
- Convert money in `app/core/money.py` only. Templates format values. They never compute money.
- Never store a balance. Compute it on each read.
- Read settings through `get_settings()` only. See [practices](../../../_docs/tech/practices.md).
- Write structlog events as `noun.verb` with key-value fields. See [practices](../../../_docs/tech/practices.md).
- Never edit the copies `app/static/css/splitwise.*` or `app/static/js/splitwise.*`. Change `_design/site/assets/`, then run `mise run design-sync`. See [design-system](../../../_docs/tech/design-system.md).
- Never edit a migration that is applied. Add a new migration. See [guide-migration](../../../_docs/tech/guide-migration.md).
- Use glossary terms in code, UI text and docs. An expense and a payment are different things. See [glossary](../../../_docs/product/glossary.md).
- Build templates from the component macros. The macros mirror the storybook. Do not add a `<style>` block to a template.
- If two docs disagree, write it in `_docs/backlog.md`. Do not pick a winner.

## 3. Change the code

1. Read the feature doc. Make the smallest change that meets it.
2. Write or change the tests with the code. See [practices](../../../_docs/tech/practices.md).
3. Run the app and check the change. See [dev-environment](../../../_docs/infra/dev-environment.md).

## 4. Done means

1. Run `mise run lint`. It passes.
2. Run `mise run test`. It passes.
3. Run `mise run dev`. Open the page or call the endpoint. Check the result.
4. Update the feature doc in the same session:
   - If the behaviour changed, update its Behaviour section.
   - Make the Data and Implementation sections match the code.
5. Run `mise run docs-verify <paths>` for each doc you checked. This stamps `verified`. See [authoring](../../../_docs/_meta/authoring.md).
6. Run `mise run docs-lint`. It passes.
7. Commit the code and the doc in one commit.

## 5. Subagents

1. If the user does not specify otherwise, run at most 3 subagents at the same time.
2. Give each subagent the smallest model that can do its task.
3. Tell each subagent that writes a document to follow [ste-writing](../../../_docs/_meta/ste-writing.md).
4. Tell each subagent to use the Edit or Write tool for one edit. For a batch of edits, write a script in `_tools/` if the script is faster or uses fewer tokens.
5. Do not stash or revert a change that you did not make.
