---
id: infra-dev-environment
title: Development environment
kind: infra
status: current
summary: How to build and run Splitwise Lite on one machine. The mise tools and tasks, the .env files, the database file in _data/ and where the logs go.
read_when: you set up the project, run the app or its tests, reset the dev database, or change a mise task
updated: 2026-11-05
verified: 2026-11-06
source_anchors: [mise.toml, .env.example, pyproject.toml, app/core/config.py, app/core/db.py, app/core/migrate.py, _tools/design_sync.py, tests/conftest.py]
depends_on: [tech-architecture, tech-practices]
review_cycle: quarterly
---

# Development environment

The app runs on one machine with no container and no external service. `mise` installs the tools
and runs the tasks. `uv` manages the Python packages. The settings are in
[`../tech/practices.md`](../tech/practices.md).

## 1. Tools

| Tool | Version | Source |
|---|---|---|
| Python | 3.13 | `mise.toml` |
| `uv` | latest | `mise.toml` |
| Python packages | pinned | `pyproject.toml` and `uv.lock` |

`.python-version` holds `3.13`. `uv` reads it also outside `mise`. `mise.toml` sets `UV_PYTHON=3.13`, `UV_PYTHON_PREFERENCE=only-system` and `UV_PYTHON_DOWNLOADS=never`.
`uv` then uses the Python that `mise` installs. Keep `UV_PYTHON` and `.python-version` equal to
the Python version of `[tools]`. If `uv` picks a newer Python, for example from the Windows `py` launcher, a package with no
wheel for that version fails to build.

## 2. Tasks

Run a task with `mise run <task>`. `mise tasks` lists all tasks.

| Task | Does | Command behind it |
|---|---|---|
| `dev` | Starts the server with auto reload. Use it while you code | `uvicorn app.main:app --reload` |
| `start` | Starts the server without reload | `uvicorn app.main:app` |
| `migrate` | Applies pending migrations and exits | `app/core/migrate.py` runner |
| `test` | Runs all tests. Pass `pytest` arguments after the task name | `pytest` |
| `lint` | Checks style and formatting. Changes no file | `ruff check`, `ruff format --check` |
| `fmt` | Fixes lint findings and formats the code | `ruff check --fix`, `ruff format` |
| `design-sync` | Copies the CSS, the component JS and the favicon from `_design/site/assets/` to `app/static/` | copy script in `_tools/` |
| `db-reset` | Deletes the dev database and applies all migrations | delete file, then `migrate` |

The `docs-*` tasks and `digest` are in [`../_meta/tools.md`](../_meta/tools.md).

`dev` and `start` read `SPLITWISE_HOST` and `SPLITWISE_PORT`. Both apply pending migrations at
start, so `migrate` is optional before them.

## 3. Procedures

### 3.1 First run

1. Run `mise install`.
2. Run `cp .env.example .env`.
3. Run `uv sync`.
4. Run `mise run dev`.
5. Open `http://127.0.0.1:8000`. Check `http://127.0.0.1:8000/healthz`.

### 3.2 Reset the database

CAUTION: this step deletes every group, expense and payment in the dev database.

1. Stop the server.
2. Run `mise run db-reset`.
3. Start the server.

### 3.3 Sample data

In `dev`, the migration `0002_sample_data.sql` adds 4 users and 3 groups. `test` and `prod` skip it.
See [`../tech/guide-migration.md`](../tech/guide-migration.md).

1. Run `mise run db-reset`, or start the app on a new database.
2. Sign in as Alice, Bob, Carla or Dan.
3. Open a group.

| Group | Currency | Members | Content |
|---|---|---|---|
| Flat 12B | EUR | Alice, Bob, Carla | 6 expenses, 2 payments, open balances |
| Tokyo trip | JPY | Alice, Bob, Dan | 4 expenses, 1 payment, open balances |
| Ski weekend | EUR | Bob, Carla | 2 expenses, 1 payment, all balances zero |

An existing user with one of these names keeps its row and joins the sample groups.

### 3.4 Update the CSS or component JS

1. Change the file in `_design/site/assets/` and the storybook.
2. Run `mise run design-sync`.
3. Never edit the copies in `app/static/`. The next sync overwrites them.

## 4. Environment files

| File | In git | Purpose |
|---|---|---|
| `.env.example` | Yes | Lists every `SPLITWISE_*` variable with a safe dev value |
| `.env` | No | Your local values. Copy it from `.env.example` |

A real environment variable wins over the `.env` file. Tests set their own values in
`tests/conftest.py` and ignore `.env`.

## 5. Data and logs

| Item | Location | Note |
|---|---|---|
| Dev database | `_data/splitwise.db` | Set by `SPLITWISE_DATABASE_PATH`. Not in git |
| WAL files | `_data/splitwise.db-wal`, `_data/splitwise.db-shm` | SQLite makes them. Do not copy the database file while the server runs |
| Test database | A temp folder of `pytest` | Made and deleted for each test |
| Logs | Standard output of the server | No log file. Format set by `SPLITWISE_LOG_FORMAT` |

The server creates `_data/` if it does not exist. To keep logs, redirect standard output:
`mise run dev > tmp/dev/server.log 2>&1`.

## Related docs

- [`../tech/architecture.md`](../tech/architecture.md): what the app is made of
- [`../tech/practices.md`](../tech/practices.md): the settings table and the logging rules
- [`../tech/project-structure.md`](../tech/project-structure.md): where the files are
- [`../tech/guide-migration.md`](../tech/guide-migration.md): the migration procedure
- [`../_meta/tools.md`](../_meta/tools.md): the documentation tasks
