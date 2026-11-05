---
id: tech-practices
title: Engineering practices
kind: tech
status: current
summary: The normative rules for code in Splitwise Lite. Settings, logging, error handling, money and dates, transactions, security basics, tests, code style and dependencies.
read_when: you write or review application code and need the rule for settings, logs, errors, money, transactions, tests or style
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/core/config.py, app/core/logging.py, app/core/errors.py, app/core/db.py, app/core/clock.py, app/core/money.py, app/core/session.py, tests/conftest.py, .env.example, pyproject.toml]
depends_on: [tech-architecture, prod-glossary]
review_cycle: quarterly
---

# Engineering practices

Each rule is a command. The sentence after it gives the reason. The structure that these rules
serve is in [`architecture.md`](./architecture.md).

## 1. Configuration

Read every setting through `get_settings()` in `app/core/config.py`. Never read `os.environ` in
other code. One reader makes the settings easy to find and to override in tests.

The `Settings` class uses `pydantic-settings`. It reads the environment and the `.env` file.
`.env` is not in git. `.env.example` is in git and lists every variable.

| Name | Default | Meaning |
|---|---|---|
| `SPLITWISE_ENV` | `dev` | Run mode: `dev`, `test` or `prod` |
| `SPLITWISE_DATABASE_PATH` | `_data/splitwise.db` | Path of the SQLite file |
| `SPLITWISE_SECRET_KEY` | dev placeholder in `dev` and `test` | Key that signs sign-in tokens. Required when `SPLITWISE_ENV` is `prod` |
| `SPLITWISE_LOG_LEVEL` | `INFO` | Minimum log level |
| `SPLITWISE_LOG_FORMAT` | `console` in `dev`, `json` otherwise | Log renderer: `console` or `json` |
| `SPLITWISE_HOST` | `127.0.0.1` | Address that the server binds to |
| `SPLITWISE_PORT` | `8000` | Port that the server binds to |

When you add a setting, add it to `Settings`, to `.env.example` and to this table in one change.
If `SPLITWISE_ENV` is `prod` and the secret key is missing, the app fails at start.

## 2. Structured logging

The app uses `structlog` over the standard `logging` module.

- Write an event name as `noun.verb` in snake case: `expense.created`, `migration.applied`, `http.request`.
- Pass data as key-value fields. Never build the message with an f-string. Fields are searchable and a string is not.
- Use these levels: `debug` for developer detail, `info` for a normal business event, `warning` for a handled problem, `error` for a failure that needs a fix.
- Log one event for each business change, after the transaction commits. Include the ids that identify the change.
- Never log the secret key, a token, a cookie or a full request body. A log file is not a safe place.
- Never log an amount without its currency code.

A middleware binds `request_id`, `method`, `path` and `user_id` into context variables. Every log
line in the request carries them. The middleware reads `X-Request-ID` or makes a new `uuid4` hex
string, and it returns the value in the response header `X-Request-ID`. At the end it logs one
`http.request` event with `status` and `duration_ms`.

| Format | Used when | Output |
|---|---|---|
| `console` | `SPLITWISE_ENV` is `dev` | Colored, one line for each event |
| `json` | Any other mode, or when you set it | One JSON object for each line, to standard output |

## 3. Error handling

Services raise domain errors from `app/core/errors.py`. Routes do not catch them. One set of
handlers maps each error to a response, so every route fails the same way.

| Domain error | Status | `code` |
|---|---|---|
| `ValidationFailed` (has `fields`) | 422 | `validation_failed` |
| `NotFound` | 404 | `not_found` |
| `Conflict` | 409 | `conflict` |
| `NotSignedIn` | 401 for the API. For HTML, a 303 redirect to `/login?next=...`. For an htmx request, status 200 with the header `HX-Redirect` | `not_signed_in` |
| An HTTP error such as an unknown route | The status of the error | `not_found` for 404, else `http_error` |
| Any other exception | 500 | `internal_error` |

The handler picks the response form from the request:

| Request | Response |
|---|---|
| Path starts with `/api/` | JSON envelope `{"error": {"code", "message", "fields"}}` |
| Request has `HX-Request` | An HTML fragment. For 422, the form with the field errors. Status 422 so that htmx swaps it |
| Other | A full error page |

Never show a stack trace to the browser. Log it with the `error` level and the request id. A
500 response shows only the request id, so a developer can find the log.

## 4. Money and dates

Business rules for money, splits and balances are in the
[product overview](../product/overview.md). The vocabulary is in the [glossary](../product/glossary.md).
These rules cover the code only.

- Store and compute money as an `int` in minor units with a currency code. Never use `float`. A float cannot hold `0.10` exactly.
- Convert between minor units and text only in `app/core/money.py`. Templates call its filters and never compute.
- Put the equal split in `app/core/money.py`. It is a pure function with no database access.
- Store the expense date and payment date as `TEXT` in the form `YYYY-MM-DD`.
- Store the entry time as `TEXT` in UTC ISO 8601, for example `2026-11-05T10:00:00Z`.
- Never store a balance. Compute it from expenses and payments on each read.
- Read the clock only through `app/core/clock.py` (`utc_now`, `now_iso`, `today_iso`). Tests then fix the time.

## 5. Transactions

- Open a transaction only in `service.py`. Repositories never commit.
- Make one service call that changes data one transaction. Everything in it succeeds or nothing does.
- Roll back when the service raises. The `transaction` helper in `app/core/db.py` does this.
- Keep a transaction short. Do not render a template or call the network inside one.
- Check the balance invariant in tests after each change. The total of all balances in a group is zero.

## 6. Security basics

The app is a local development tool. These rules still hold.

- Rely on the Jinja2 autoescape for HTML. Never use the `|safe` filter on user input and never build HTML by string concatenation.
- Pass values to SQL as parameters (`?`). Never format a value into a SQL string.
- Sign tokens with `itsdangerous` and `SPLITWISE_SECRET_KEY`. Never put the key in code for `prod`.
- Set the cookie with `HttpOnly` and `SameSite=Lax`. Add `Secure` when `SPLITWISE_ENV` is `prod`.
- CSRF: the app does not add CSRF tokens. The sign-in is a simulation and the app is for local use. `SameSite=Lax` blocks cross-site form posts that carry the cookie. A real deployment needs real accounts and a CSRF token first.
- Never describe the simulated sign-in as security. [`guide-authentication.md`](./guide-authentication.md) lists its limits.

## 7. Testing

Tests use `pytest`. Integration tests use `httpx` through the FastAPI `TestClient`.

| Kind | Folder | Uses | Tests |
|---|---|---|---|
| Unit | `tests/unit/` | No database, no HTTP | Pure functions: money, split, balance rules |
| Integration | `tests/integration/` | A temp database file and the `TestClient` | Routes, API, services, migrations |

- Create a fresh temp database for each test. Run all migrations on it. Never touch `_data/`.
- Set `SPLITWISE_ENV=test` and point `SPLITWISE_DATABASE_PATH` to the temp file in `conftest.py`.
- Write a test for each of these. A bug in them gives a member a wrong balance:
  - money: parse, format and minor-unit conversion
  - split: the equal split, including the remainder in join order
  - balance: the acceptance examples of the product overview and the zero total
- Test each endpoint for success, validation failure (422) and not signed in.
- Test through the public interface. Do not assert on private functions of other layers.

## 8. Code style

- Use `ruff` for lint and format. `mise run lint` checks and `mise run fmt` fixes.
- Write type hints on every function signature. Use built-in generics such as `list[int]` and `X | None`.
- Keep a function short and single-purpose. A name tells what the function does.
- Write names in English. Use the glossary terms in names: `expense`, `payer`, `participant`, `share`, `payment`.
- Write a comment only for a reason that the code cannot show.

## 9. Dependencies

Use `uv` for every dependency change.

- Add a package with `uv add <name>`. Add a development package with `uv add --dev <name>`.
- Commit `pyproject.toml` and `uv.lock` together. The lock file makes every machine install the same versions.
- Run commands with `uv run`, or through a `mise run` task.
- Add a dependency only when the standard library does not cover the need. Fewer packages mean fewer upgrades.
- Vendor front-end files in `app/static/vendor/`. Never add a Node build.

## Related docs

- [`architecture.md`](./architecture.md): layers, flow and rationale
- [`project-structure.md`](./project-structure.md): where each file lives
- [`guide-api.md`](./guide-api.md): endpoint procedures that apply these rules
- [`guide-authentication.md`](./guide-authentication.md): the sign-in simulation
- [`../infra/dev-environment.md`](../infra/dev-environment.md): the `mise` tasks
- [`../product/overview.md`](../product/overview.md): the business rules
- [`../product/glossary.md`](../product/glossary.md): the vocabulary
