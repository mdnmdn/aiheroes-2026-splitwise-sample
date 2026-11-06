---
id: feat-balances
title: Balances and transactions
kind: feature
status: current
summary: The balance of each member, the transaction list grouped by day with the Mine filter, the member detail breakdown, and the Settled state.
read_when: you are changing how a balance is computed or shown, how the transaction list is ordered, or when the card shows the Settled state
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [_design/site/group.html, app/balances/routes.py, app/balances/api.py, app/balances/service.py, app/balances/repo.py, app/balances/schemas.py, app/core/money.py, app/static/js/app.js, app/templates/partials/balances/transactions.html, app/templates/partials/members/panel.html, app/templates/partials/members/detail_dialog.html]
depends_on: [prod-overview, prod-glossary, tech-architecture, feat-expenses, feat-payments, feat-members]
review_cycle: quarterly
---

# Balances and transactions

## Purpose

A member sees who is owed money and who owes money in a group. The member sees the transactions
behind each balance, newest first. The app
computes every figure from the expenses and the payments. It stores no balance.

## Behaviour

### Balance

1. The balance of a member is: the sum of the expense amounts that the member paid, minus the sum of the shares of the member, plus the sum of the payments that the member sent, minus the sum of the payments that the member received.
2. All figures are in minor units of the base currency of the group.
3. A positive balance means the member is owed money. A negative balance means the member owes money.
4. The app shows a balance with a sign and the currency: `+60.00 EUR`, `−30.00 EUR`, `0.00 EUR`. The minus sign is U+2212.
5. The label under the amount is "is owed", "owes" or "settled". The sign and the label carry the meaning. Colour never carries it alone.
6. The app recomputes the balances from all expenses and payments for each request. This satisfies MVP-07.
7. The total of all balances of a group is zero. If it is not, the app logs the event `balance.invariant_violated` with the group id. It still shows the page.
8. The [overview](../product/overview.md) gives the acceptance examples. Alice pays `90.00 EUR` for Alice, Bob and Carla. Then Bob pays `30.00 EUR` to Alice. Then the first expense is deleted. Each step must give the balances of the overview.

### Balances card

1. The card sits in the members panel of the page `/groups/ID`.
2. The stat "Total of the expenses" is the sum of the expense amounts of the group in the base currency. Payments do not count.
3. The stat "Your balance" is the balance of the current user, with the label.
4. Each member has a row in join order: avatar, name, the chip "You" for the current user, the balance and the label.
5. The avatar colour comes from the position of the member in join order.
6. If the member is the current user, the row shows "You" next to the name.
7. A click on a row opens the member detail.
8. The card footer shows one of two states, or nothing.

| State of the group | Footer |
|---|---|
| No transaction | "Add a payment to see who owes whom." |
| Transactions exist and every balance is zero | The badge "All settled up" |
| At least one balance is not zero | Nothing |

### Transaction list

1. The transactions panel lists the expenses and the payments of the group together.
2. The list groups the rows by date. The heading is the expense date or payment date, for example "16 Oct 2026".
3. The groups run from the newest date to the oldest date.
4. Inside one date, the newest entry time comes first. If two entry times are equal, the higher `id` comes first.
5. An expense row shows an icon, the description, the tag "Expense", the amount and the meta text "PAYER paid · for everyone (N)".
6. If the participants are all members, the meta text says "for everyone (N)". Otherwise it lists the participant names in join order.
7. A payment row shows an icon, "SENDER → RECEIVER", the tag "Payment", the amount and the note. [Payments](./payments.md) owns it.
8. A click on a row opens its edit dialog.
9. The filter has two options: All (default) and Mine. The counter reads "SHOWN of TOTAL".
10. The Mine filter shows an expense if the member of the current user is the payer or a participant.
11. The Mine filter shows a payment if the member of the current user is the sender or the receiver.
12. If the filter is Mine and the group has transactions but none involve the user, the list shows "Nothing involves you yet."
13. If the group has no transaction, the list shows "No transactions yet", "Add what someone paid for the group. It is split equally between the members you choose." and the button "Add expense".
14. The app does not keep the filter after a reload.

### Member detail

1. A click on a member row opens the dialog. The title is the member name.
2. The dialog shows the balance with its sign and the label: "NAME is owed", "NAME owes" or "Settled".
3. The note reads "Paid minus share for each expense, plus payments sent, minus payments received."
4. The dialog lists lines, newest date first, then newest entry time first.
5. An expense gives a line if the member paid it or has a share of it. The delta is the amount paid minus the share. The delta can be zero.
6. A payment gives a line if the member is the sender or the receiver. The sender line is `+amount`. The receiver line is `−amount`.
7. A line shows the date, a meta text and the signed delta.
8. The last line "Balance" shows the sum of the deltas. It equals the balance of the member.
9. If the member has no line, the dialog shows "NAME is not part of any transaction in this group yet."
10. The button "Remove from group" (or "Leave group") belongs to [members](./members.md).

## Data

The feature owns no table. It reads these tables:

| Table | Columns read |
|---|---|
| `members`, `users` | `members.id`, `members.group_id`, `users.name`, join order from `members.id` |
| `expenses` | `id`, `amount`, `expense_date`, `payer_id`, `description`, `created_at` |
| `expense_shares` | `expense_id`, `member_id`, `share` |
| `payments` | `id`, `amount`, `payment_date`, `sender_id`, `receiver_id`, `note`, `created_at` |
| `groups` | `currency` |

- The balance of a member comes from four row queries: members, expenses, shares and payments. The service adds the rows in Python and returns a map from member id to minor units.
- The service merges the rows of `expenses` and the rows of `payments` into the list of transactions. Each row has a `kind`, a date and an entry time.
- The app never stores a balance.

## Implementation

| Item | Place |
|---|---|
| Routes, rules, SQL | `app/balances/routes.py` (HTML), `api.py` (JSON), `service.py`, `repo.py`, `schemas.py` |
| Balances | `compute_balances`, `balances_of_groups` and `group_balances` in `service.py`. Only `balances_of_groups` logs `balance.invariant_violated` if the sum is not zero (through `_check_invariant`). |
| Card figures and breakdown | `summary` and `breakdown` in `service.py` |
| Money format with sign | `app/core/money.py` |
| Fragments | `partials/balances/`: `transactions.html`. The card is `partials/members/panel.html`. The member detail is `partials/members/detail_dialog.html` |

| Method and URL | Returns |
|---|---|
| `GET /groups/{id}/members` | Fragment: the balances card, the region `#members-region`. The members feature owns the route. The card has no route of its own |
| `GET /groups/{id}/transactions?filter=all` | Fragment `partials/balances/transactions.html`: the region `#expenses-region` with the filter, the counter and the list. The value `mine` selects the Mine filter. Any other value means `all`. A request that is not HTMX goes to the group page |
| `GET /groups/{id}/members/{mid}` | Fragment: the member detail dialog with the breakdown. The members feature owns the route. Status 404 if the member does not exist |
| `GET /api/v1/groups/{id}/balances` | JSON: `[{"member_id", "balance", "currency"}]`, one row for each member in join order. Amounts are in minor units |
| `GET /api/v1/groups/{id}/transactions` | JSON: `[{"kind", "id", "date", "amount", "currency", "title", "meta"}]`, the rows of all days, newest first. `kind` is `expense` or `payment`. No filter. Amounts are in minor units |

The card and the list reload on the events `ledger-changed` and `members-changed`. The macros `stat` and `balance_amount` (`money.html`) and `settled_badge` (`feedback.html`) draw the card.

The service function `transaction_list` in
`app/balances/service.py` builds the days and the rows. The region also reloads when the member
selects a filter option. The request carries the selected option, so a reload keeps the filter.
The route calls `require_member` of the groups feature, because the balances service cannot
import the groups service (the groups service imports the balances service).

## Failure & idempotency

- The app never writes a balance. A wrong balance is a bug in a rule, not stored data.
- If the balances do not add up to zero, the app logs `balance.invariant_violated` and still renders.
- If the group has no member for an id in the request, the app answers status 404.
- A list that another member changed is stale until the next event. A reload shows the new state.

## Assumptions

- All amounts in a group have the base currency of the group.
- A member can record any payment with the payments feature.
- A group has few members, so a full recompute for each request is cheap.

## Related docs

- [`../product/overview.md`](../product/overview.md): MVP-07, the balance rules and the acceptance examples
- [`../product/glossary.md`](../product/glossary.md): Balance, Settled, Transaction, Mine filter
- [`expenses.md`](./expenses.md), [`payments.md`](./payments.md): the rows behind the balances
- [`members.md`](./members.md): the member buttons in the detail dialog
- [`groups.md`](./groups.md): the balance of the current user in the groups list
- [`../tech/architecture.md`](../tech/architecture.md): fragments and events
- [`../tech/guide-navigation.md`](../tech/guide-navigation.md): URL naming rules, dialogs and fragments
- [`../tech/design-system.md`](../tech/design-system.md): regions, dialogs and events
- [`../backlog.md`](../backlog.md): Greedy settlement plan (F2), Balance labels

## Next steps

- The settle-up dialog of the design is the contract source for F2. See F2 in [`../product/overview.md`](../product/overview.md) and the backlog line on the greedy method.
