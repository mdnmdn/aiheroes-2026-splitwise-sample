---
id: feat-expenses
title: Expenses
kind: feature
status: current
summary: Add, edit and delete an expense with an equal split, the share preview, and the validation of description, amount, expense date, payer and participants.
read_when: you are changing how an expense is entered, validated, split or deleted
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [_design/site/group.html, app/expenses/service.py, app/expenses/repo.py, app/expenses/routes.py, app/expenses/api.py, app/expenses/schemas.py, app/core/money.py, app/core/clock.py, app/migrations/0001_init.sql, app/static/js/app.js, app/templates/partials/expenses/form.html, app/templates/partials/expenses/form_dialog.html, app/templates/partials/expenses/preview.html, app/templates/components/forms.html]
depends_on: [prod-overview, prod-glossary, tech-architecture, feat-members]
review_cycle: quarterly
---

# Expenses

## Purpose

A member records what one member paid for some or all members. The app divides the expense amount
equally between the participants and shows the share of each participant before the member saves.
A member can correct or delete an expense. This document also owns the rules for amount input and
dates, which the [payments](./payments.md) feature reuses.

## Behaviour

### Add an expense

1. The member selects "Add expense". It is in the head of the transactions panel, and in the bottom bar on a narrow screen.
2. The dialog "Add expense" opens with these defaults: payer is the member of the current user, expense date is the server date (UTC), every member is a participant.
3. The member fills the fields below and selects "Save expense".
4. If all fields are valid, the app saves the expense and its shares in one transaction.
5. The app closes the dialog and shows "Expense added".
6. The app redraws the transactions and the balances.

### Fields

| Field | Rule | Error |
|---|---|---|
| Description | 1–100 characters after trim | "Add a short description." / "Use at most 100 characters." |
| Amount | A decimal number in the base currency of the group. See "Amount input" | See "Amount input" |
| Expense date | A calendar date, `YYYY-MM-DD`, not after the server date (UTC) | "Pick an expense date." / "The expense date cannot be in the future." |
| Payer | One member of this group | "Choose who paid." |
| Participants | One or more members of this group | "Pick at least one participant." |

These fields satisfy MVP-04 and MVP-05. A payer can be outside the participants.

### Amount input

1. The app trims the text and removes all white space.
2. The app changes the first comma into a point.
3. The text must match digits, then an optional point and digits. Anything else gives "Use digits only, for example 12.50."
4. The text can have at most as many decimals as the base currency. `EUR` has 2 and `JPY` has 0.
5. If the text has more decimals, the error is "Use at most N decimals." For `JPY` the error is "This currency has no decimals."
6. The integer part must be less than 100000000. If it is not, the error is "The amount is too large."
7. The amount must be more than zero. If it is zero, the error is "The amount must be more than zero."
8. If the text is empty, the error is "Enter an amount."
9. The app converts the text to an integer in minor units with no floating-point step. `12.50` for `EUR` is `1250`.
10. The edit dialog shows the stored amount again as text with the decimals of the currency.

### Equal split

1. The app divides the expense amount in minor units by the number of participants N. The base share is the integer quotient.
2. The remainder R is the amount in minor units modulo N.
3. The app sorts the participants in join order. The selection order does not count.
4. The first R participants get the base share plus one minor unit. The others get the base share.
5. The shares add up exactly to the expense amount. Example: `10.00 EUR` for 3 participants gives `3.34 EUR`, `3.33 EUR`, `3.33 EUR`. The [overview](../product/overview.md) defines the rule.
6. The app computes the shares on the server. `core/money.py` owns the function.
7. The app stores the shares, so a later change of join order does not change an old expense.

### Share preview

1. Each participant tile shows the share of that participant. The tile of a member who is not a participant shows no share.
2. The hint under the list reads "N participants · X each" if all shares are equal.
3. If the shares differ, the hint reads "N participants · the first R in join order get one minor unit more". X is the base share.
4. If no participant is selected, the hint reads "Choose who shares this expense."
5. The preview refreshes when the amount or a participant changes. The server computes it. An invalid amount shows no shares.
6. "Select all" selects every member. If all are selected, the link reads "Clear all" and clears every box.

### Edit an expense

1. The member selects the row of an expense. The dialog "Edit expense" opens with the stored values.
2. The same rules as "Add an expense" apply.
3. On save, the app replaces the shares and keeps the id and the entry time of the first save.
4. The app shows "Expense updated".
5. A member can edit any expense of the group. The product has no owner until F9.

### Delete an expense

1. The edit dialog shows the button "Delete". The add dialog does not.
2. A confirmation opens: "Delete this expense?", "The app deletes DESCRIPTION (90.00 EUR) and recalculates the balances.", ok "Delete expense".
3. Focus starts on "Cancel". The key Esc cancels. A click outside the dialog does not close it.
4. On confirm, the app deletes the expense and its shares.
5. The app shows "Expense deleted".
6. This satisfies MVP-08.

## Data

The feature owns the tables `expenses` and `expense_shares`.

| Table | Column | Type | Rule |
|---|---|---|---|
| `expenses` | `id` | INTEGER PRIMARY KEY | |
| | `group_id` | INTEGER NOT NULL | References `groups(id)` |
| | `description` | TEXT NOT NULL | `CHECK (length(description) BETWEEN 1 AND 100)` |
| | `amount` | INTEGER NOT NULL | Minor units of the base currency. `CHECK (amount > 0)` |
| | `expense_date` | TEXT NOT NULL | ISO `YYYY-MM-DD` |
| | `payer_id` | INTEGER NOT NULL | References `members(id)` ON DELETE RESTRICT |
| | `created_at` | TEXT NOT NULL | Entry time, UTC ISO 8601 |
| | `updated_at` | TEXT NOT NULL | Entry time of the last change |
| `expense_shares` | `expense_id` | INTEGER NOT NULL | References `expenses(id)` ON DELETE CASCADE |
| | `member_id` | INTEGER NOT NULL | References `members(id)` ON DELETE RESTRICT. A row means the member is a participant |
| | `share` | INTEGER NOT NULL | Minor units. `CHECK (share >= 0)` |

- The primary key of `expense_shares` is `(expense_id, member_id)`.
- The sum of `share` for an expense equals `expenses.amount`. The service checks the sum before the commit.
- The payer and the participants belong to the group of the expense. The service checks it.
- A balance is never stored. [Balances](./balances.md) computes it.

## Implementation

| Item | Place |
|---|---|
| Routes, rules, SQL | `app/expenses/routes.py`, `service.py`, `repo.py`, `schemas.py`, `api.py` |
| Amount parse, format, equal split | `app/core/money.py`: `parse_amount`, `to_input`, `split_equal` |
| Date check | `app/expenses/service.py`: `validate_date`. It reads the server date from `app/core/clock.py` |
| Fragments | `app/templates/partials/expenses/`: `form_dialog.html` (the dialog), `form.html` (the form, also the 422 answer), `preview.html` |
| Macros | `money_field` and `check_tiles` in `components/forms.html` |
| Client glue for "Select all" | `app/static/js/app.js`. The preview trigger is `hx-trigger` on the participants fieldset |

| Method and URL | Returns |
|---|---|
| `GET /groups/{id}/expenses/new` | Fragment: the dialog "Add expense" |
| `GET /groups/{id}/expenses/preview?amount=TEXT&p=MID&p=MID` | Fragment: out-of-band parts that replace the share of each tile, the hint and the link "Select all". The request swaps nothing else |
| `POST /groups/{id}/expenses` | Empty body, header `HX-Reswap: none`, events `ledger-changed`, `toast`, `close-dialog`. Status 422 and the form fragment on error |
| `GET /groups/{id}/expenses/{eid}/edit` | Fragment: the dialog "Edit expense". Status 404 if deleted |
| `POST /groups/{id}/expenses/{eid}` | Same as the create route |
| `POST /groups/{id}/expenses/{eid}/delete` | Empty body with events `ledger-changed`, `toast`, `close-dialog`. Status 404 if deleted |
| `GET /api/v1/groups/{id}/expenses` | JSON: the expenses, newest date first. Each has `id`, `group_id`, `description`, `amount`, `currency`, `expense_date`, `payer_id` and `shares` (a list of `{member_id, amount}`) |
| `POST /api/v1/groups/{id}/expenses` | Status 201, JSON: the expense. Body `description`, `amount` (minor units, an integer), `expense_date`, `payer_id`, `participant_ids`. Status 422 with `fields` on error |
| `PUT /api/v1/groups/{id}/expenses/{eid}` | JSON: the expense. The body is the same as for create. Status 404 if deleted |
| `DELETE /api/v1/groups/{id}/expenses/{eid}` | Status 204. Status 404 if deleted |

The JSON API takes the amount in minor units, as an integer. A float, a string or a boolean gives status 422. The form takes text. `api.py` turns the integer into text with `to_input` and calls the same service function. The field errors use the same keys as the form, except `participants`: the API names it `participant_ids`, like the body. An id in the body must be an integer. A string, a float or a boolean gives status 422.

The confirmation of a delete is not a route. The button "Delete" in the edit dialog carries the
attributes `data-confirm-title`, `data-confirm-body` and `data-confirm-ok`. `app.js` shows the
confirmation of `splitwise.js` and sends the `POST` only after the member confirms.

A missing expense raises `ExpenseNotFound`. The route answers 404 with the events `toast`, `close-dialog` and
`ledger-changed`.

## Failure & idempotency

- If a field is invalid, the app answers with status 422 and the dialog with all field errors. It writes nothing.
- If the payer or a participant is not a member of the group, the app answers status 422. It never ignores the id.
- If the sum of the shares differs from the amount, the app raises an internal error and rolls back. This is a bug.
- If a member opens an expense that another member deleted, the app answers status 404 and shows "That expense does not exist." It sends `ledger-changed`.
- If another member deletes the expense while a member saves it, the answer is 404, also when a field is invalid.
- The app checks the payer and the participants inside the write transaction. A member who leaves meanwhile gives 422, never 500.
- If a member deletes an expense twice, the second request answers 404 and shows the same message. No data changes.
- If a member selects "Save expense" twice, the app creates two expenses. The client disables the button after the first click to prevent it.
- If two members edit the same expense, the last save wins.

## Assumptions

- A group has one base currency. An expense has no currency of its own.
- A transaction in the list belongs to the group in the URL. The service verifies it.
- The server date in UTC defines "not in the future". A member far from UTC can see a one-day difference.

## Related docs

- [`../product/overview.md`](../product/overview.md): MVP-04, MVP-05, MVP-08 and the rounding rule
- [`../product/glossary.md`](../product/glossary.md): Expense, Payer, Participant, Share, Remainder, Join order
- [`members.md`](./members.md): the members and join order
- [`payments.md`](./payments.md): reuses the amount and date rules
- [`balances.md`](./balances.md): the balance after each change
- [`../tech/architecture.md`](../tech/architecture.md): layers, fragments and events
- [`../tech/guide-api.md`](../tech/guide-api.md): the JSON conventions
- [`../tech/guide-navigation.md`](../tech/guide-navigation.md): URL naming rules, dialogs and fragments
- [`../tech/design-system.md`](../tech/design-system.md): regions, dialogs and events

## Next steps

- Uneven split modes (F1).
- A note on an expense (F5).
