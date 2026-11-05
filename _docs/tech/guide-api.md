---
id: tech-guide-api
title: "Guide: add an endpoint"
kind: tech
status: current
summary: Procedures to add a JSON endpoint under /api/v1 and an HTML mutation endpoint that serves htmx, with one short example for each.
read_when: you add a JSON API endpoint or an HTML form action that htmx submits
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/core/api.py, app/core/htmx.py, app/core/errors.py, app/core/session.py, app/expenses/api.py, app/expenses/routes.py, app/static/js/app.js]
depends_on: [tech-architecture, tech-practices, tech-guide-authentication]
review_cycle: quarterly
---

# Guide: add an endpoint

Both kinds of endpoint call the same service function. The service holds the rules and the
transaction. The endpoint only converts HTTP to a service call and back. The layers are in
[`architecture.md`](./architecture.md). The error rules are in [`practices.md`](./practices.md).

## 1. Add a JSON endpoint

1. Put the business rule in `app/<feature>/service.py`. Skip this step if the function exists.
2. Define the input and output models in `app/<feature>/schemas.py`. Use pydantic.
3. Add the endpoint in `app/<feature>/api.py` under the prefix `/api/v1`. Write the full path in the route, for example `/groups/{group_id}/expenses`. Use the verbs and paths that the feature document lists. A JSON endpoint can use `GET`, `POST`, `PUT`, `PATCH` and `DELETE`.
4. Add the user dependency `current_user_api`. Never leave an endpoint open, except `GET /healthz`.
5. Call the service. Return the output model. Never return a database row.
6. Set the status code. Use 201 for create, 200 for read and update, 204 for delete.
7. Raise no `HTTPException`. Let the service raise a domain error. The handler builds the envelope.
8. Write an integration test for success, 422, 401 and 404.

A body field that holds money is `Minor` of `app/core/api.py`. It accepts an integer only. If a service takes text, the endpoint turns the integer into text with `to_input`. The endpoint never copies a rule.

Money in a schema is an integer in minor units with a `currency` field. Never use a float. A date
is a `YYYY-MM-DD` string.

```python
@router.post("/groups/{group_id}/expenses", status_code=201)
def create_expense(group_id: Id, body: ExpenseIn, user: CurrentUser, conn: Conn) -> ExpenseOut:
    ...  # turn `body` into the service form, call service.add_expense, return the output model
```

`Id` is the path type of `app/core/ids.py`. Each `api.py` defines `CurrentUser` and `Conn` as
`Annotated` types with `Depends(current_user_api)` and `Depends(get_conn)`. `service.add_expense`
returns the new id, so the endpoint reads the stored expense and returns it.

The error envelope for status 422 has this form. `fields` maps each field name to its message.
`{"error": {"code": "validation_failed", "message": "...", "fields": {"shares": "..."}}}`

| Status | Code | When |
|---|---|---|
| 401 | `not_signed_in` | No valid user |
| 404 | `not_found` | The id does not exist |
| 409 | `conflict` | The request clashes with the stored state |
| 422 | `validation_failed` | The input breaks a rule. `fields` names each field |

## 2. Add an HTML mutation endpoint

An HTML mutation takes a form post from htmx, changes data and returns a fragment.

1. Put the business rule in the service. Share it with the API.
2. Add the fragment template of the form in `app/templates/partials/<feature>/`.
3. Add the form with `hx-post`, `hx-target` and `hx-swap` in the fragment.
4. Add the `POST` route in `app/<feature>/routes.py` with `current_user_html`. Every HTML change is a `POST`: create `POST /<collection>`, update `POST /<collection>/{id}`, delete `POST /<collection>/{id}/delete`. The feature document owns the exact route.
5. Read the fields into a form model with `Annotated[Model, Form()]`. Call the service.
6. On success, return `mutation_response` of `core/htmx.py` with a toast message and the events that other regions need. The body is empty. Each region reloads itself.
7. On `ValidationFailed`, render the same form with the errors and status 422. The htmx config swaps 422 responses.
8. Make each region that shows the data listen: `hx-trigger="ledger-changed from:body"`.
9. Write an integration test with the header `HX-Request: true`. Check the status, the fragment and the `HX-Trigger` header.

```python
@router.post("/groups/{group_id}/expenses")
def add(group_id: Id, request: Request, form: Annotated[ExpenseForm, Form()],
        user: User = Depends(current_user_html),
        conn: sqlite3.Connection = Depends(get_conn)) -> Response:
    try:
        service.add_expense(conn, user, group_id, form)
    except ValidationFailed as err:
        view = service.form_view(conn, user, group_id, form, err.fields)
        return _fragment(request, "partials/expenses/form.html", view, 422)
    return mutation_response(message="Expense added", events=LEDGER_CHANGED)
```

The example is simplified. `mutation_response` returns an empty body with the header
`HX-Reswap: none`. It sets the events `toast` and `close-dialog` and the events that you pass.

The `toast` event shows its `message` in the toast area that `app.js` owns. The error handlers
cover 404 and 409, so the route does not catch them.

## 3. Events and responses

| Event | Fired when | Listeners |
|---|---|---|
| `ledger-changed` | An expense or a payment is created, changed or deleted | The transaction list (`#expenses-region`) and the members panel (`#members-region`) |
| `members-changed` | A member is added or removed | The members panel and the transaction list |
| `toast` | The user needs feedback. Field `message` holds the text | The toast area of `app.js` |
| `close-dialog` | A mutation in a dialog succeeds | `app.js` closes the open dialog |

Name a new event as `noun-changed`. A region reloads on the event and reads the data again from the
server. This keeps the server as the only owner of balances.

| Result | HTML response | JSON response |
|---|---|---|
| Created, changed or deleted | Empty body, status 200, `HX-Trigger` | Output model with 201 (created) or 200, or status 204 (deleted) |
| Invalid input | Form fragment, status 422 | Envelope, status 422 |

Never put a rule in the response step. If a fragment needs a computed value, the service returns
it. The template only shows it. The same applies to the API: the output model carries the final
values, so a client never recomputes a balance.

## 4. Checklist

Check each item before you finish.

- The endpoint has no SQL and no rule.
- The user dependency is present.
- The test covers success, 422 and no user.
- No money value is a float.
- The API and the HTML route call the same service function.
- A new log event follows the `noun.verb` rule of [`practices.md`](./practices.md).

## Related docs

- [`architecture.md`](./architecture.md): layers and request flow
- [`practices.md`](./practices.md): errors, money and testing rules
- [`guide-authentication.md`](./guide-authentication.md): the user dependencies
- [`project-structure.md`](./project-structure.md): where each file goes
