---
id: feat-members
title: Members
kind: feature
status: current
summary: The members panel of a group. Add a member from an existing user or a new user, remove, and the join order.
read_when: you are changing how a member is added or removed, or how join order is kept
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [_design/site/group.html, app/members/routes.py, app/members/service.py, app/members/repo.py, app/members/api.py, app/members/schemas.py, app/templates/components/rows.html, app/templates/partials/members/panel.html, app/templates/partials/members/detail_dialog.html]
depends_on: [prod-overview, prod-glossary, tech-architecture, feat-sign-in, feat-groups]
review_cycle: quarterly
---

# Members

## Purpose

A group lists its members in join order. A member can add another member and
remove a member who has no transaction. In the bootstrap, a member is a user inside a group. The
member name is the user name.

## Behaviour

### Members and users

1. A member is the link between one user and one group.
2. The member name is the user name. A member has no name of its own.
3. The same user can be a member of many groups.
4. User names are unique across the app, without case. [Sign in](./sign-in.md) owns the name rules.
5. The members panel lists the members in join order, oldest first.
6. The row of the current user shows the chip "You".
7. The creator of a group, and each user who joins with the invite code, becomes a member.
8. Every member has the same rights. The app has no owner and no permissions.

### Add a member

1. The user selects "Add" in the members panel. The dialog "Add member" opens.
2. The list "User" holds each user who is not a member of this group, sorted by name. It adds "New user…" at the end.
3. If every user is a member, or no other user exists, the dialog preselects "New user…".
4. If the user picks "New user…", the field "Name" appears. It follows the name rules of sign-in.
5. If the user picks an existing user, the app adds a member for that user.
6. If the user picks "New user…" and the name is valid, the app creates the user and adds a member for it.
7. If the user picked no option, or an unknown user id, the error is "Choose a user."
8. The dialog shows the note "To let someone join on their own, share the invite code instead."
9. The new member gets the last place in join order.
10. The app shows "NAME added to GROUP" and redraws the members panel and the balances.

### Remove a member

1. The member detail shows the button "Remove from group". For the current user, the label is "Leave group".
2. If the member has a transaction in this group, the button is disabled. The detail shows "Members with transactions in this group cannot be removed."
3. A member has a transaction if the member is the payer or a participant of an expense of this group.
4. A member has a transaction if the member is the sender or the receiver of a payment of this group.
5. If the member has no transaction, the user can remove the member. This satisfies MVP-03.
6. A confirmation opens: "Remove NAME?", "The app removes NAME from GROUP. NAME can rejoin with the invite code.", ok "Remove member".
7. For the current user, the confirmation is the one of [Leave a group](./groups.md).
8. On confirm, the app deletes the member. It keeps the user.
9. The app shows "NAME removed" and redraws the panel.
10. The server enforces rule 2. A direct request to remove a member with a transaction fails.
11. The server refuses a request to remove the member of the current user. The app shows "You cannot remove yourself. Use Leave." The user must use Leave.

### Join order

1. Join order is the order of the `id` of the member rows in the group.
2. The members panel, the participant lists and the equal split use join order.
3. A user who leaves and joins again gets a new row and the last place.

### Member detail

The member detail dialog shows the balance and its breakdown. [Balances](./balances.md) owns it.
This document owns its buttons "Remove from group" and "Leave group".

## Data

The feature owns the table `members`. It reads and writes `users` only to create a user.

| Column | Type | Rule |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Assigned by SQLite. Order of `id` is join order |
| `group_id` | INTEGER NOT NULL | References `groups(id)` ON DELETE CASCADE |
| `user_id` | INTEGER NOT NULL | References `users(id)` ON DELETE RESTRICT |
| `joined_at` | TEXT NOT NULL | Entry time, UTC ISO 8601 |

- `UNIQUE (group_id, user_id)`: a user is a member of a group once.
- `expenses.payer_id`, `expense_shares.member_id`, `payments.sender_id` and `payments.receiver_id` reference `members(id)` ON DELETE RESTRICT. The database blocks the removal of a member that has a transaction.
- The name of a member is `users.name`, read through a join.
- `AUTOINCREMENT` makes sure that an `id` is never reused. A removed member never changes the order of the others.

## Implementation

| Item | Place |
|---|---|
| Routes, rules, SQL | `app/members/routes.py`, `service.py`, `repo.py`, `schemas.py`, `api.py` |
| Check "has a transaction" | `service.py`, one query in `repo.py` |
| Remove rule | `remove_member` in `service.py`. It refuses the member of the current user |
| Leave rule | `leave_group` in `service.py`. `POST /groups/{id}/leave` of [groups](./groups.md) calls it |
| Fragments | `app/templates/partials/members/`: `panel.html` (root `#members-region`), `add_dialog.html` and `add_form.html`, `detail_dialog.html` |
| Macros | `member_row` in `rows.html` |

| Method and URL | Returns |
|---|---|
| `GET /groups/{id}/members` | Fragment: the members panel. It is the balances card: the stats, the member rows and the footer |
| `GET /groups/{id}/members/new` | Fragment: the dialog "Add member" |
| `GET /groups/{id}/members/{mid}` | Fragment: the member detail dialog with the balance, the breakdown and the buttons "Remove from group" or "Leave group". Status 404 if the member does not exist |
| `POST /groups/{id}/members` | Empty swap (`HX-Reswap: none`). Events `members-changed`, `toast`, `close-dialog`. Status 422 and the form fragment on error |
| `POST /groups/{id}/members/{mid}/delete` | Empty swap. Events `members-changed`, `toast`, `close-dialog`. Status 409 if the member has a transaction or is the member of the current user, status 404 if the member does not exist. Both statuses send the same events, so the panel redraws |
| `GET /api/v1/groups/{id}/members` | JSON: the members `{id, user_id, name}` in join order. Status 404 if the user is not a member of the group |
| `POST /api/v1/groups/{id}/members` | Status 201, JSON: the member. Body `{"user_id": 3}` or `{"name": "Eve"}`. `user_id` wins if both are present. `user_id` must be an integer. Status 422 with `fields` on error |
| `DELETE /api/v1/groups/{id}/members/{mid}` | Status 204. Status 409 if the member has a transaction or is the member of the current user. Status 404 if the member does not exist |

The panel listens to `members-changed` and `ledger-changed` and reloads itself. A mutation does not return the panel, so the panel loads once.

The member detail dialog shows the balance and the breakdown of [balances](./balances.md). `detail` in `service.py` calls `breakdown` of the balances service.

## Failure & idempotency

- If the name is invalid or taken, the app answers with status 422 and the form with the field error. It writes nothing.
- If two requests add the same user, the `UNIQUE (group_id, user_id)` index rejects the second. The app answers "NAME is a member of this group." and adds no row.
- If two requests create a user with the same name, the unique name index rejects the second. The app answers with the name error.
- If another member adds a transaction for a member while a user removes that member, the foreign key rejects the delete. The app answers status 409 and redraws the panel.
- If a request removes the member of the current user, the app answers status 409 and does not delete the member.
- If another member removed the member first, a second remove answers status 404 and redraws the panel. It is safe to retry.

## Assumptions

- Every member can act on every member. The product has no owner until F9.
- One user name means one person across all groups.
- A transaction blocks the removal of its members. Deleting the transaction lifts the block.

## Related docs

- [`sign-in.md`](./sign-in.md): the name rules and the user table
- [`groups.md`](./groups.md): create, join, leave, invite code
- [`balances.md`](./balances.md): the member detail and the balances in the panel
- [`expenses.md`](./expenses.md), [`payments.md`](./payments.md): the transactions that block a removal
- [`../product/overview.md`](../product/overview.md): MVP-02 and MVP-03
- [`../product/glossary.md`](../product/glossary.md): Member, User, Join order
- [`../tech/guide-navigation.md`](../tech/guide-navigation.md): URL naming rules, dialogs and fragments
- [`../tech/design-system.md`](../tech/design-system.md): regions, dialogs and events
- [`../backlog.md`](../backlog.md): User and member in the bootstrap
