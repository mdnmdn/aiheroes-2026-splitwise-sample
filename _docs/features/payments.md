---
id: feat-payments
title: Payments
kind: feature
status: current
summary: Record, edit and delete a payment from a sender to a receiver, with amount, payment date and an optional note, and the validation of each field.
read_when: you are changing how a payment is recorded, validated or deleted
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [_design/site/group.html, app/payments/service.py, app/payments/repo.py, app/payments/routes.py, app/payments/api.py, app/payments/schemas.py, app/migrations/0001_init.sql, app/templates/partials/payments/form.html, app/templates/partials/payments/form_dialog.html]
depends_on: [prod-overview, prod-glossary, tech-architecture, feat-expenses, feat-members]
review_cycle: quarterly
---

# Payments

## Purpose

A member records that one member gave money to another member to settle debts. The balances then
include that payment. The app records payments and never moves money.

## Behaviour

### Record a payment

1. The member selects "Add payment". It is in the head of the transactions panel, and in the bottom bar on a narrow screen.
2. If the group has fewer than 2 members, the app shows "Add one more member first." It opens the invite dialog and does not open the payment dialog.
3. The dialog "Add payment" opens with the note "Records money that one member gave to another member. Splitwise never moves money itself."
4. The defaults are: sender is the member of the current user, receiver is the first other member in join order, payment date is the server date (UTC).
5. The member fills the fields below and selects "Save payment".
6. If all fields are valid, the app saves the payment.
7. The app closes the dialog and shows "Payment recorded".
8. The app redraws the transactions and the balances.

### Fields

| Field | Rule | Error |
|---|---|---|
| Sender | One member of this group | "Choose the sender." |
| Receiver | One member of this group, not the sender | "Sender and receiver must be different members." The error shows on the receiver field |
| Amount | Same rules as an expense amount, in the base currency of the group | See [Amount input](./expenses.md) |
| Payment date | A calendar date, `YYYY-MM-DD`, not after the server date (UTC) | "Pick a payment date." / "The payment date cannot be in the future." |
| Note | Optional. 0–100 characters after trim | "Use at most 100 characters." |

These fields satisfy MVP-06 and MVP-05.

### Effect on balances

1. A payment adds its amount to the balance of the sender.
2. A payment subtracts its amount from the balance of the receiver.
3. A payment never changes the balance of another member.
4. The payment has no participants and no shares.
5. Example: Bob records a payment of `30.00 EUR` to Alice. Bob changes by `+30.00 EUR` and Alice changes by `−30.00 EUR`. The [overview](../product/overview.md) gives the full acceptance example.

### Edit a payment

1. The member selects the row of a payment. The dialog "Edit payment" opens with the stored values.
2. The same rules as "Record a payment" apply.
3. On save, the app keeps the id and the entry time of the first save.
4. The app shows "Payment updated".
5. A member can edit any payment of the group.

### Delete a payment

1. The edit dialog shows the button "Delete". The add dialog does not.
2. A confirmation opens: "Delete this payment?", "SENDER → RECEIVER, 30.00 EUR. The app recalculates the balances.", ok "Delete payment".
3. Focus starts on "Cancel". The key Esc cancels. A click outside the dialog does not close it.
4. On confirm, the app deletes the payment and shows "Payment deleted".
5. This satisfies MVP-08.

### Row in the transaction list

1. The row shows the title "SENDER → RECEIVER", the tag "Payment" and the amount.
2. If the payment has a note, the row shows the note as its meta text.
3. [Balances](./balances.md) owns the order and the grouping of the rows.

## Data

The feature owns the table `payments`.

| Column | Type | Rule |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `group_id` | INTEGER NOT NULL | References `groups(id)` |
| `sender_id` | INTEGER NOT NULL | References `members(id)` ON DELETE RESTRICT |
| `receiver_id` | INTEGER NOT NULL | References `members(id)` ON DELETE RESTRICT |
| `amount` | INTEGER NOT NULL | Minor units of the base currency. `CHECK (amount > 0)` |
| `payment_date` | TEXT NOT NULL | ISO `YYYY-MM-DD` |
| `note` | TEXT NOT NULL DEFAULT '' | `CHECK (length(note) <= 100)` |
| `created_at` | TEXT NOT NULL | Entry time, UTC ISO 8601 |
| `updated_at` | TEXT NOT NULL | Entry time of the last change |

- `CHECK (sender_id <> receiver_id)` holds at the database level.
- The sender and the receiver belong to the group of the payment. The service checks it.
- The note is defined for an expense only in the glossary. See [backlog](../backlog.md).

## Implementation

| Item | Place |
|---|---|
| Routes, rules, SQL | `app/payments/routes.py`, `service.py`, `repo.py`, `schemas.py`, `api.py` |
| Amount parse and format | `app/core/money.py` |
| Amount and date checks | `validate_amount` and `validate_date` in `app/expenses/service.py` |
| Fragments | `app/templates/partials/payments/`: `form_dialog.html` (the dialog) and `form.html` (the form, also the 422 answer) |

| Method and URL | Returns |
|---|---|
| `GET /groups/{id}/payments/new` | Fragment: the dialog "Add payment", or the invite dialog if the group has one member |
| `POST /groups/{id}/payments` | Empty body, header `HX-Reswap: none`, events `ledger-changed`, `toast`, `close-dialog`. Status 422 and the form fragment on error |
| `GET /groups/{id}/payments/{pid}/edit` | Fragment: the dialog "Edit payment". Status 404 if deleted |
| `POST /groups/{id}/payments/{pid}` | Same as the create route |
| `POST /groups/{id}/payments/{pid}/delete` | Empty body with events `ledger-changed`, `toast`, `close-dialog`. Status 404 if deleted |
| `GET /api/v1/groups/{id}/payments` | JSON: the payments, newest date first. Each has `id`, `group_id`, `sender_id`, `receiver_id`, `amount`, `currency`, `payment_date`, `note` |
| `POST /api/v1/groups/{id}/payments` | Status 201, JSON: the payment. Body `sender_id`, `receiver_id`, `amount` (minor units, an integer), `payment_date`, `note`. Status 422 with `fields` on error |
| `PUT /api/v1/groups/{id}/payments/{pid}` | JSON: the payment. The body is the same as for create. Status 404 if deleted |
| `DELETE /api/v1/groups/{id}/payments/{pid}` | Status 204. Status 404 if deleted |

The service function `record_payment` serves the form and the JSON API. One rule set covers
both callers. Each takes a `PaymentForm` of text values. A caller with minor units builds the amount text with `to_input` in `app/core/money.py`.

The confirmation of a delete is not a route. The button "Delete" in the edit dialog carries the
attributes `data-confirm-*`, as in [expenses](./expenses.md). A missing payment raises
`PaymentNotFound`. The route answers 404 with the events `toast`, `close-dialog` and `ledger-changed`.

## Failure & idempotency

- If a field is invalid, the app answers with status 422 and the dialog with all field errors. It writes nothing.
- If the sender equals the receiver, the form error and the database `CHECK` both reject it.
- If a member opens a payment that another member deleted, the app answers status 404 and shows "That payment does not exist." It sends `ledger-changed`.
- If another member deletes the payment while a member saves it, the answer is 404, also when a field is invalid.
- If another member leaves the group while a member saves, the app checks the sender and the receiver inside the write transaction. The app answers 422. It never answers 500.
- If a member deletes a payment twice, the second request answers 404. No data changes.
- If a member selects "Save payment" twice, the app records two payments. The client disables the button after the first click to prevent it.
- If two members edit the same payment, the last save wins.

## Assumptions

- A payment has the base currency of its group.
- A payment can be larger than the debt between the two members. The app does not check it.
- A payment never moves money. The members move it outside the app.

## Related docs

- [`expenses.md`](./expenses.md): the amount and date rules, and the confirmation pattern
- [`balances.md`](./balances.md): the list of transactions and the balances
- [`members.md`](./members.md): the sender and the receiver block the removal of a member
- [`../product/overview.md`](../product/overview.md): MVP-05, MVP-06, MVP-08 and the acceptance examples
- [`../product/glossary.md`](../product/glossary.md): Payment, Sender / receiver, Payment date
- [`../tech/guide-navigation.md`](../tech/guide-navigation.md): URL naming rules, dialogs and fragments
- [`../tech/design-system.md`](../tech/design-system.md): regions, dialogs and events
- [`../backlog.md`](../backlog.md): Note on a payment, Design vocabulary
