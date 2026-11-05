---
id: tech-project-structure
title: Project structure
kind: tech
status: current
summary: Reference table of every folder and key file of the repository and of the app tree, and the rules for where a new route, template, migration, test or static file goes.
read_when: you create a file and need to know where it goes, or you look for the place of a thing
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/main.py, mise.toml, pyproject.toml, .env.example, app/core/config.py, app/core/clock.py, app/core/api.py, app/core/ids.py, app/core/htmx.py, tests/conftest.py, _tools/design_sync.py]
depends_on: [tech-architecture]
review_cycle: quarterly
---

# Project structure

This document lists the places in the repository and the rules for new files. The
[architecture](./architecture.md) explains why the app tree has this shape.

## 1. Repository root

| Path | Holds | In git |
|---|---|---|
| `AGENTS.md` | The agent guide. `CLAUDE.md` loads it | Yes |
| `mise.toml` | Tools (Python, uv) and tasks | Yes |
| `pyproject.toml` | Project metadata, dependencies, `ruff` and `pytest` settings | Yes |
| `uv.lock` | Pinned dependency versions | Yes |
| `.env.example` | Every `SPLITWISE_*` setting with a safe dev value | Yes |
| `.env` | Local settings of one developer | No |
| `app/` | The application | Yes |
| `tests/` | The tests | Yes |
| `_docs/` | The documentation library | Yes |
| `_design/` | Web app design in HTML and the component storybook. Source of the CSS and component JS | Yes |
| `_tools/` | Support scripts. Python, uv, PEP 723 inline metadata | Yes |
| `_data/` | Local dev data, for example `splitwise.db` | No |
| `tmp/` | Spikes and temporary assets, one subfolder for each task. Notes go to `_docs/wip/` | No |
| `refs/` | Temporary samples from other projects. Never a source of project facts | No |

## 2. App tree

| Path | Holds |
|---|---|
| `app/main.py` | `create_app()`: settings, logging, middleware, routers, static files, lifespan that runs migrations |
| `app/core/config.py` | `Settings` and the cached `get_settings()`. The only reader of the environment |
| `app/core/logging.py` | `structlog` set-up and the request middleware |
| `app/core/db.py` | Connection factory and the per-request connection dependency |
| `app/core/migrate.py` | The migration runner |
| `app/core/clock.py` | The clock helpers `utc_now`, `now_iso` and `today_iso` |
| `app/core/api.py` | Shared types of the JSON API, for example `Minor` |
| `app/core/templating.py` | The `Jinja2Templates` instance and the template filters |
| `app/core/errors.py` | Domain error classes and the handlers that map them to HTTP |
| `app/core/ids.py` | The `Id` path type and `parse_id`. An out-of-range id becomes 0 |
| `app/core/limits.py` | Text length limits that services check and templates use for `maxlength` |
| `app/core/money.py` | Minor units, formatting and the equal split |
| `app/core/session.py` | Token signing and the current-user dependencies |
| `app/core/htmx.py` | `is_htmx`, `HX-Trigger` helpers, the toast helper, `mutation_response`, `redirect_to` and `fragment_only` |
| `app/<feature>/routes.py` | HTML pages and fragments of the feature |
| `app/<feature>/api.py` | JSON endpoints of the feature under `/api/v1` |
| `app/<feature>/service.py` | Business rules and transactions |
| `app/<feature>/repo.py` | SQL only |
| `app/<feature>/schemas.py` | Pydantic models for the API |
| `app/migrations/` | `NNNN_slug.sql` files, for example `0001_init.sql` |
| `app/templates/base.html` | The master template. Built from the page shell in `_design/site/` |
| `app/templates/components/` | Jinja macros, one file for each storybook component group |
| `app/templates/pages/` | Full pages. Each extends `base.html` |
| `app/templates/partials/<feature>/` | HTMX fragments. Pages also include them |
| `app/static/css/splitwise.css` | Copy of `_design/site/assets/splitwise.css` |
| `app/static/js/splitwise.js` | Copy of `_design/site/assets/splitwise.js` |
| `app/static/js/app.js` | App glue: htmx config, user header, toasts, dialogs |
| `app/static/favicon.svg` | Copy of `_design/site/assets/favicon.svg` |
| `app/static/vendor/htmx.min.js` | Pinned HTMX 2.x file. No CDN |
| `tests/unit/` | Tests with no database and no HTTP |
| `tests/integration/` | Tests with a temp database and the `TestClient` |
| `tests/conftest.py` | Shared fixtures: temp database, client, signed-in users |

The prototype file `_design/site/assets/splitwise-app.js` (a fake store in `localStorage`) is not
copied. The app replaces it.

## 3. Placement rules

| New thing | Place | Rule |
|---|---|---|
| Feature | `app/<feature>/` | One package for each feature. Add the router in `app/main.py` |
| HTML route | `app/<feature>/routes.py` | The route calls a service and renders a template. No SQL |
| JSON endpoint | `app/<feature>/api.py` | Path under `/api/v1/<feature>` |
| Business rule | `app/<feature>/service.py` | A rule shared by two features goes to `app/core/` only if it has no SQL |
| SQL statement | `app/<feature>/repo.py` | A repository reads and writes the tables of its own feature |
| Full page | `app/templates/pages/<name>.html` | Extends `base.html` |
| Fragment | `app/templates/partials/<feature>/<name>.html` | A fragment never extends `base.html` |
| Macro | `app/templates/components/<group>.html` | Match the storybook group |
| Schema change | `app/migrations/NNNN_slug.sql` | Next free number. [Guide](./guide-migration.md) |
| Unit test | `tests/unit/test_<module>.py` | No database |
| Integration test | `tests/integration/test_<feature>_<topic>.py` | Uses the temp database |
| App JavaScript | `app/static/js/app.js` | Keep it small. No build step |
| CSS, component JS and favicon | `_design/site/assets/` | Then run `mise run design-sync`. Never edit the copies in `app/static/` |
| Third-party static file | `app/static/vendor/` | Pin the version in the file name or a header comment |
| Setting | `app/core/config.py` and `.env.example` | Update the table in [practices](./practices.md) |
| Support script | `_tools/` | Python with PEP 723 metadata. Add a `mise` task |
| Spikes and temporary assets | `tmp/<task>/` | Never in git |
| Task notes and small text data | `_docs/wip/` | Delete them when the task closes |

## Related docs

- [`architecture.md`](./architecture.md): the layers and the reasons
- [`practices.md`](./practices.md): the rules for the code in these files
- [`../infra/dev-environment.md`](../infra/dev-environment.md): the tasks that run the tree
- [`../../AGENTS.md`](../../AGENTS.md): the repository guide
