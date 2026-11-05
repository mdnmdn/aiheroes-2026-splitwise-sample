---
id: tech-guide-authentication
title: "Guide: simulated sign-in"
kind: tech
status: current
summary: How the simulated per-tab sign-in works from token to header, how to protect a new route, how to test as two users in two tabs, and the limits of the simulation.
read_when: you protect a route, change the sign-in, or test the app as two users
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/core/session.py, app/users/routes.py, app/users/api.py, app/static/js/app.js, app/templates/base.html, tests/conftest.py]
depends_on: [tech-architecture, tech-practices]
review_cycle: quarterly
---

# Guide: simulated sign-in

The sign-in simulates many users on one machine. Each browser tab can act as a different user. It
is a development tool and it is not security. The model is in
[`architecture.md`](./architecture.md).

## 1. How it works

| Part | Where | Role |
|---|---|---|
| Token | `core/session.py` | Signed user id. `itsdangerous` `URLSafeSerializer` with `SPLITWISE_SECRET_KEY` |
| Cookie `sw_user` | Browser | Transport for full page loads. Holds the token of the tab that loaded a page last |
| `sessionStorage['sw_user']` | One tab | Source of truth. Holds the token for this tab only |
| `sessionStorage['sw_user_id']` | One tab | Holds the user id that goes with the token |
| Header `X-Splitwise-User` | htmx requests | Carries the token of the tab |
| `data-user-id` on `<html>` | Rendered page | Tells the head script which user the server used |
| `data-public` on `<html>` | Login page | Tells the head script that the page needs no user |
| `sessionStorage['sw_resume']` | One tab | Marker of the last resume: path and time. It stops a reload loop |
| `POST /login/resume` | Server | Reads the header only. Sets the cookie to the token of the tab. Status 204, or 401 and the cookie is cleared |

### 1.1 Sign in

1. The user opens `/login`. The page lists the users.
2. The user picks a user or creates one with a name of 1 to 30 characters.
3. The server signs the user id into a token.
4. The server sets the cookie `sw_user` and redirects to `next` or to the home page.
5. For an htmx request, the response carries the event `session-start`. `app.js` stores the token and the user id in `sessionStorage` before the redirect. The response also carries `HX-Redirect`.

### 1.2 Each request

1. `app.js` listens to `htmx:configRequest` and adds `X-Splitwise-User` from `sessionStorage`.
2. `<body hx-boost="true">` sends links and forms through htmx, so they carry the header.
3. The server resolves the user in this order: header, then cookie, then none.
4. A bad signature counts as none.

### 1.3 Full page load

A full page load sends no header, because the browser makes it. The server then renders the page
for the cookie user, which can be the user of another tab. A script at the top of `<head>` in
`base.html` fixes this before the first paint.

1. The server writes the user id into `data-user-id` on `<html>`. On the login page it also writes `data-public`.
2. If the tab has no token and the page is not public, the script goes to `/login?next=PATH`. The cookie never signs a new tab in.
3. If the tab has a token and `sw_user_id` equals `data-user-id`, the script does nothing.
4. Otherwise the script hides the page with the class `sw-resuming` and posts the token to `POST /login/resume`.
5. On status 204, the script reloads the page. On the login page it goes to `next`, or to `/`.
6. On status 401, the script clears `sessionStorage`. It shows the login page, or goes to `/login?next=PATH`.
7. If a resume for the same path ran less than 5 seconds ago, the script does not resume again. It clears `sessionStorage` and goes to the login page. This stops a loop.

### 1.4 Sign out

Sign out clears `sessionStorage` of the tab and posts `/logout`, which clears the cookie. Other
tabs keep their own token in `sessionStorage`. They resume their user on their next full load.

## 2. Protect a route

Use a dependency from `core/session.py`. Never read the header or the cookie in a route.

| Need | Dependency | Result when no user |
|---|---|---|
| HTML route | `current_user_html` | Redirect to `/login?next=<path>` (`HX-Redirect` for htmx) |
| JSON endpoint | `current_user_api` | Status 401 with the error envelope, code `not_signed_in` |
| User or none | `optional_user` | Returns `None` |

```python
@router.get("/groups/{group_id}")
def group_page(
    group_id: int,
    request: Request,
    user: User = Depends(current_user_html),
    conn: Connection = Depends(get_conn),
):
    group = service.get_group(conn, user, group_id)
    return templates.TemplateResponse(request, "pages/group.html", {"group": group})
```

The dependency also binds `user_id` into the log context. Pass `user` to the service when a rule
depends on the user.

## 3. Test as two users

### 3.1 By hand

1. Run `mise run dev`.
2. In tab 1, open `/login` and sign in as Alice.
3. In tab 2, open `/login` and sign in as Bob.
4. Act in each tab. Each tab keeps its own user.
5. Reload tab 1. The page shows Alice, because the head script resumes the token of the tab.
6. Open a new tab. It shows the login page, not a user.

Do not use a private window for the second user. Two tabs prove the per-tab model.

### 3.2 In a test

A test client sends the header directly. The `conftest.py` fixture `sign_in(name)` makes a user and
returns the headers.

```python
def test_two_users(client, sign_in):
    alice = sign_in("Alice")
    bob = sign_in("Bob")
    assert client.get("/", headers=alice).status_code == 200
    assert client.get("/api/v1/me", headers=bob).json()["name"] == "Bob"
    assert client.get("/api/v1/me").status_code == 401
```

## 4. Limits

- There is no password. Anyone who can reach the port can pick any user.
- A token has no expiry and no revocation. Anyone with a copy acts as that user.
- The signature only stops a typed user id. It does not prove who the person is.
- `sessionStorage` is readable by any script on the page.
- A user sees only the groups where the user is a member. Anyone can still pick any user, so anyone can see any group.
- A real deployment needs accounts, password hashing, token expiry and a CSRF token first.

## Related docs

- [`architecture.md`](./architecture.md): where the sign-in sits in the request flow
- [`practices.md`](./practices.md): cookie flags, secret key and CSRF position
- [`guide-api.md`](./guide-api.md): the 401 envelope and endpoint procedures
- [`../infra/dev-environment.md`](../infra/dev-environment.md): how to run the app
