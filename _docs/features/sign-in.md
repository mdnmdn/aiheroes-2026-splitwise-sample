---
id: feat-sign-in
title: Sign in
kind: feature
status: current
summary: Simulated sign-in without a password. Pick or create a user, sign out, keep one user per browser tab, and return to the page in the `next` parameter.
read_when: you are changing how a person picks a user, how the app knows the current user, or how a route is protected
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [_design/site/login.html, app/users/service.py, app/users/routes.py, app/users/repo.py, app/users/api.py, app/users/schemas.py, app/core/session.py, app/core/htmx.py, app/core/errors.py, app/templates/base.html, app/templates/pages/login.html, app/templates/partials/users/login_form.html, app/templates/components/navigation.html, app/static/js/app.js]
depends_on: [prod-overview, prod-glossary, tech-architecture]
review_cycle: quarterly
---

# Sign in

## Purpose

A person picks a user, or creates a user by name, and then operates the app as that user. Each
browser tab can have its own current user, so one developer can test two users side by side. The
sign-in is a simulation. It has no password and gives no security.

## Behaviour

### Sign-in page

1. The app shows the page `/login` to a person without a current user.
2. The page lists every user by name, sorted by name without case. It adds the option "New user…" at the end.
3. If at least one user exists, the first option is "Select your name…" with an empty value.
4. If no user exists, the page preselects "New user…".
5. If the person picks "New user…", the page shows the field "Your name" and moves the focus to it.
6. The field "Your name" holds 1–30 characters. The hint reads "Up to 30 characters. You become a new user."
7. The page shows the note "Simulated sign-in: no password needed."

### Submit

1. The person selects "Continue".
2. If the person picked no option, the app rejects the form: "Choose your name, or pick “New user…”."
3. If the person picked an id that is not a user, the app gives the same error.
4. If the person picked "New user…", the app trims the name and validates it. See the name rules below.
5. If the name is valid, the app creates the user.
6. The app makes the user the current user of this tab.
7. The app redirects to the `next` path, or to `/` if `next` is missing or unsafe.
8. The next page shows the message "Signed in as NAME."

### Name rules

These rules hold for every user name in the app. The members feature uses them too.

1. A user name has 1–30 characters after the app trims it. A name of 30 characters is valid.
2. If the name is empty, the error is "Enter a name."
3. If the name is longer than 30 characters, the error is "Use at most 30 characters."
4. User names are unique across the app, without case. This satisfies MVP-02.
5. If the name exists, the error is "NAME is a user. Pick that user from the list or use a different name."

### The `next` parameter

1. A `next` value is safe if it is a path on this app. It starts with one `/`.
2. A `next` value is safe if it holds only letters, digits and the characters `_ - . / ? = & %`.
3. A `next` value that starts with `//`, or that holds a scheme, is unsafe.
4. The app ignores an unsafe `next` and goes to `/`.

### Current user per tab

1. After a sign-in, the server sends a signed token as the cookie `sw_user`.
2. The page also stores the token in `sessionStorage` under the key `sw_user`. `sessionStorage` is the source of truth of the user of the tab.
3. `app.js` adds the header `X-Splitwise-User` with that token to every htmx request.
4. The server resolves the current user in this order: the header, then the cookie, then none.
5. A full page load sends only the cookie. The cookie is only a transport. It holds the token of the tab that loaded a page last.
6. A new tab starts signed out. If it has no token in `sessionStorage`, it goes to `/login?next=PATH`, even if the cookie holds a user.
7. A reload keeps the user of the tab. A script at the top of `<head>` compares the user of the page with the user of the tab. If they differ, it hides the page and asks the server to set the cookie to the token of the tab. Then it reloads the page. The person sees no page of another user.
8. A tab that signs in again does not change the other tabs. Their `sessionStorage` keeps their token.
9. A token that is not valid, or that names an unknown user, counts as no token. The tab then clears its `sessionStorage` and shows the login page.
10. If the resume repeats for the same path within 5 seconds, the tab stops. It clears its `sessionStorage` and shows the login page.

### Protected routes

1. If an HTML route finds no current user, the app redirects to `/login?next=PATH`. PATH is the requested path and query.
2. If an htmx request finds no current user, the app answers with the header `HX-Redirect` to the same URL.
3. If a JSON route finds no current user, the app answers with status 401.
4. The routes `/login`, `/healthz` and `/static/…` need no current user.
5. A signed-in person who opens `/login` sees the page and can switch user. The cookie does not redirect the person away.

### Sign out

1. The topbar shows the name and the avatar of the current user. The menu shows "Signed in · N groups" and the button "Sign out".
2. N is the number of groups in which the current user is a member.
3. If the person selects "Sign out", the server clears the cookie `sw_user`.
4. `app.js` clears `sessionStorage` of this tab.
5. The app redirects to `/login`. The users and groups stay unchanged.
6. Other tabs keep their user. They resume it on their next full page load.

## Data

The feature owns the table `users`.

| Column | Type | Rule |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Assigned by SQLite |
| `name` | TEXT NOT NULL | `COLLATE NOCASE`, `UNIQUE`, `CHECK (length(name) BETWEEN 1 AND 30)` |
| `created_at` | TEXT NOT NULL | Entry time, UTC ISO 8601: `2026-11-05T10:00:00Z` |

- The app never deletes a user.
- The session holds no table. The token is `itsdangerous` `URLSafeSerializer` data with the user id.
- `sessionStorage` of a tab holds `sw_user` (token), `sw_user_id` (user id) and `sw_resume` (path and time of the last resume).
- The migration `app/migrations/0001_init.sql` creates the table. It creates the tables of the other features too.
- `created_at` has no default. The service gives `now_iso()` to `repo.insert`, which writes it.
- The name is unique through the `NOCASE` collation of the column. No second index exists.

## Implementation

| Item | Place |
|---|---|
| Routes | `app/users/routes.py` |
| API | `app/users/api.py` |
| Rules | `app/users/service.py`: name validation, `next` check, sign-in. `app/core/session.py`: token issue and check |
| SQL | `app/users/repo.py` |
| Form model | `app/users/schemas.py` |
| Current user dependency | `app/core/session.py` |
| Header and `sessionStorage` glue | `app/static/js/app.js` |
| Head script (resume guard) | `app/templates/base.html`. It reads `data-user-id` and `data-public` on `<html>` |
| Templates | `app/templates/pages/login.html`, `app/templates/partials/users/login_form.html`. The user menu is in the macro `topbar` of `app/templates/components/navigation.html` |

| Method and URL | Returns |
|---|---|
| `GET /login?next=PATH` | Page |
| `POST /login` | Redirect (303, or `HX-Redirect`) on success. Status 422 and the form fragment on error |
| `POST /logout` | Redirect to `/login`. The cookie is cleared |
| `POST /login/resume` | Reads only the header `X-Splitwise-User`. If the token is valid and the user exists: status 204 and the cookie is set to the token. Otherwise: status 401 and the cookie is cleared. The app logs `session.resumed` |
| `GET /api/v1/users` | JSON: the list of users `{id, name}`. Status 401 if none |
| `POST /api/v1/users` | Status 201, JSON: the new user `{id, name, token}`. Body `{"name": "Eve"}`. This is the only open JSON endpoint, because a client has no token before its first user. Status 422 on a name error |
| `GET /api/v1/me` | JSON: the current user `{id, name}`. Status 401 if none |

On success, an htmx request gets status 200 with `HX-Redirect` and the event `session-start`. The event detail holds `token` and `user_id`, and `app.js` stores them in `sessionStorage` under the keys `sw_user` (token) and `sw_user_id` (user id). The sign-in also sets the flash cookie `sw_flash`, which holds the message "Signed in as NAME.".

The form `POST /login` carries `user_id` (a user id or `__new`), `name` and `next`.
[`guide-authentication.md`](../tech/guide-authentication.md) holds the procedure to protect a route.

## Failure & idempotency

- If two requests create the same name at the same time, the `UNIQUE` index rejects the second request. The app answers with the name-exists error. No user is duplicated.
- If a person submits the form twice, the second request signs in as the user that the first request created.
- The sign-in never changes data other than `users`.
- If the cookie is blocked, the header still works inside the tab that signed in. A full page load then gets no user from the server, and the resume call cannot keep the cookie.

## Assumptions

- The app runs on one machine for development. Anyone can pick any user. This is not security.
- `SPLITWISE_SECRET_KEY` signs the token. Anyone who knows the key can forge a token.
- The browser supports `sessionStorage`.

## Related docs

- [`../tech/architecture.md`](../tech/architecture.md): the simulated sign-in model and the request flow
- [`../tech/guide-authentication.md`](../tech/guide-authentication.md): the procedure to protect a route
- [`../tech/guide-navigation.md`](../tech/guide-navigation.md): URL naming rules
- [`../product/glossary.md`](../product/glossary.md): Sign in, Current user, User
- [`groups.md`](./groups.md): the page that opens after the sign-in
- [`members.md`](./members.md): a member has the name of a user
- [`../backlog.md`](../backlog.md): User and member in the bootstrap
