---
id: tech-architecture
title: Application architecture
kind: tech
status: current
summary: The shape of the Splitwise Lite application. Layers, request flow for pages and HTMX fragments, data access, the migration model, the simulated sign-in model, the JSON API position and the reasons for each choice.
read_when: you are adding a feature, moving code between layers, or questioning a stack choice
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/main.py, app/core/db.py, app/core/migrate.py, app/core/session.py, app/core/htmx.py, app/core/errors.py, app/core/ids.py, app/core/money.py, app/static/js/app.js, app/templates/base.html]
depends_on: [prod-overview, prod-glossary]
review_cycle: quarterly
---

# Application architecture

Splitwise Lite is one Python process. FastAPI receives HTTP requests, Jinja2 renders HTML, and the
`sqlite3` module reads and writes one SQLite file. The browser loads HTML pages. HTMX replaces
parts of a page with HTML fragments from the server. The app has no front-end build step and no
separate API server.

Business rules come from [`../product/overview.md`](../product/overview.md). This document owns
the structure that carries them. [`project-structure.md`](./project-structure.md) owns the file
placement. [`practices.md`](./practices.md) owns the coding rules.

## 1. Layers

Each feature is one package under `app/`. A feature has four layers. The shared code is in `app/core/`.

| Layer | File | Holds | Never holds |
|---|---|---|---|
| Route | `routes.py` | HTML pages and fragments. Reads the request, calls a service, picks a template | SQL, business rules |
| API | `api.py` | JSON endpoints under `/api/v1`. Same job as a route, JSON in and out | SQL, business rules |
| Service | `service.py` | Business rules. Opens each transaction. Raises domain errors | HTTP objects, HTML |
| Repository | `repo.py` | SQL statements. Takes a `sqlite3.Connection`. Returns rows | Rules, transactions |
| Schemas | `schemas.py` | Pydantic models for API input and output | Logic |

The dependency direction is one way:

```text
routes / api  ->  service  ->  repo  ->  sqlite3 connection
       \             \
        templates     core (money, errors, config, logging)
```

A layer imports only the layer on its right. One exception exists: `core/session.py` imports `users.repo.find_by_id` inside a function, because `users.repo` imports `User` from `core/session.py`. A repository never imports a service. A service never
imports a route. Templates never compute money. They format values that the service
computes. `core/money.py` owns minor units, formatting and the equal split.

A service can read the repo of another feature. A service writes to another feature only through the service of the owner. For example, `members.service` reads `users.repo`, and `groups.service` reads `members.repo`.

A path id has the type `Id` of `core/ids.py`. An id that no row can have becomes 0, so the route answers as for an unknown id. A service reads an id from a form field with `parse_id` of the same file.

Each rule has a reason. One owner for the business rules means that the HTML routes and the JSON
API cannot disagree about a balance. SQL in one layer means that a schema change touches one file
per feature.

## 2. Request flow

### 2.1 Full page

1. The browser sends `GET /groups/3`.
2. The middleware binds the request id and starts the timer.
3. A dependency in `core/session.py` resolves the current user. If none exists, the app redirects to `/login`.
4. The route opens a connection through a dependency and calls the service.
5. The service calls the repository and returns plain values.
6. The route renders `pages/<name>.html`. The page extends `base.html` and includes its fragments from `partials/`.
7. The middleware logs one `http.request` event with `status` and `duration_ms`.

### 2.2 HTMX fragment

The page markup marks regions with `hx-get`, `hx-post` or `hx-trigger`. The browser sends the
request with the header `HX-Request: true`.

1. The route runs the same steps 2 to 5 as a full page.
2. The route renders one template from `partials/<feature>/`. It does not extend `base.html`.
3. After a mutation, the route sets the `HX-Trigger` response header with events, for example `ledger-changed` and `toast`.
4. Other regions listen with `hx-trigger="ledger-changed from:body"` and reload themselves.

A fragment template is the single source of its markup. The full page includes the same template.
A route can serve both forms of one URL: it checks `is_htmx` from `core/htmx.py` and returns a full
page or a fragment. The body has `hx-boost="true"`, so ordinary links and forms also travel
through htmx. A boosted request carries the sign-in header (section 5).

## 3. Data access

- The app uses the standard `sqlite3` module and plain SQL. No ORM and no query builder.
- `core/db.py` opens one connection for each request. It sets `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL` and `row_factory=sqlite3.Row`.
- A repository function takes the connection as its first argument and runs one statement or a few related ones.
- Only a service opens a transaction. One service call is one transaction. [`practices.md`](./practices.md) has the rules.
- Money is stored as integer minor units with a currency code. Dates are ISO `TEXT`. Balances are computed from expenses and payments and never stored. The [glossary](../product/glossary.md) defines these terms.

## 4. Migrations

The schema changes only through migration files. The runner is `app/core/migrate.py`.

| Aspect | Rule |
|---|---|
| Files | `app/migrations/NNNN_slug.sql`. Four digits, then a snake case slug |
| Direction | Forward only. No down migrations |
| Record | Table `schema_migrations(version INTEGER PRIMARY KEY, name TEXT, applied_at TEXT)` |
| Unit | One file is one transaction. A failure rolls the file back and stops the start |
| Order | The runner applies pending files in ascending version order |
| Start | The FastAPI lifespan runs pending migrations before the app serves a request |
| Manual | `mise run migrate` runs the same runner without the server |
| Applied files | Never edit an applied file. A change is a new file |

[`guide-migration.md`](./guide-migration.md) holds the procedure.

## 5. Simulated sign-in

Splitwise Lite has no accounts and no passwords. The sign-in simulates many users on one machine,
so that one developer can test two users in two browser tabs. It is not security.

- The sign-in page lists the users. A new user needs only a name.
- The server signs the user id into a token. It sends the token as a cookie and the page keeps it in `sessionStorage` of the tab.
- `app.js` adds the header `X-Splitwise-User` with the token to every htmx request.
- The server resolves the user in this order: the header, then the cookie, then none.
- `sessionStorage` belongs to one tab. It is the source of truth of the user of the tab. The cookie belongs to the whole browser. It only carries the token of the tab that loaded a page last.
- A script at the top of `<head>` runs before the first paint. It compares the user of the page with the user of the tab. If they differ, it calls `POST /login/resume`, which sets the cookie to the token of the tab, and then reloads the page.
- A new tab has an empty `sessionStorage`. It starts signed out, even if the cookie holds a user.

[`guide-authentication.md`](./guide-authentication.md) holds the end-to-end procedure and the limits.

## 6. JSON API position

The JSON API lives under `/api/v1`. It exists for tests, scripts and a later client. It is not the
main way the browser talks to the server.

- The API calls the same services as the HTML routes. It adds no rule.
- Schemas are pydantic models. Errors use one envelope: `{"error": {"code", "message", "fields"}}`.
- A missing user gives status 401 JSON. An HTML route redirects instead.
- `GET /healthz` returns `{"status": "ok"}` and needs no sign-in.

[`guide-api.md`](./guide-api.md) holds the procedures for both API and HTML mutation endpoints.

## 7. Rationale

| Choice | Reason | Alternative that the design rejects |
|---|---|---|
| No ORM | The model has few tables. Money rules need exact SQL. Plain SQL is easy to read and to test | SQLAlchemy: a second model of the schema and hidden queries |
| Server-rendered HTML | Rules and formatting stay in one language and one place. No client state to keep in sync | A single-page app: a build step and a second copy of the rules |
| HTMX | It updates parts of a page with HTML from the server and adds no front-end framework | A client framework: more code than the product needs |
| Vendored `htmx.min.js` | The version is pinned and the app works offline | A CDN link |
| Own migration runner | Forward-only SQL files need about 50 lines of code | Alembic: it needs the ORM model |
| SQLite | One file, no server, fits the local persistence of the MVP | A database server |
| Services own transactions | One place decides what must succeed or fail together | Transactions in routes or repositories |
| Design files as source | `_design/site/assets` is the source of CSS and component JS. The app copies them | Edited copies that drift |

## Related docs

- [`project-structure.md`](./project-structure.md): where each file lives
- [`practices.md`](./practices.md): the rules for code, logs, errors and tests
- [`guide-authentication.md`](./guide-authentication.md): the simulated sign-in procedure
- [`guide-api.md`](./guide-api.md): how to add an endpoint
- [`guide-migration.md`](./guide-migration.md): how to change the schema
- [`../infra/dev-environment.md`](../infra/dev-environment.md): how to run the app
- [`../product/overview.md`](../product/overview.md): the business rules
- [`../product/glossary.md`](../product/glossary.md): the vocabulary
