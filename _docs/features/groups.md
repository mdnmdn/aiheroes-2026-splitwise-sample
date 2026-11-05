---
id: feat-groups
title: Groups
kind: feature
status: current
summary: The groups home with the balance of the current user, search and filter, create a group, group settings, join with an invite code, the invite dialog and leave a group.
read_when: you are changing how a group is listed, created, renamed, joined or left, or how the invite code works
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [_design/site/index.html, _design/site/group.html, app/groups/routes.py, app/groups/service.py, app/groups/repo.py, app/groups/api.py, app/groups/schemas.py, app/core/money.py, app/core/htmx.py, app/templates/pages/groups_home.html, app/templates/pages/group.html]
depends_on: [prod-overview, prod-glossary, tech-architecture, feat-sign-in]
review_cycle: quarterly
---

# Groups

## Purpose

The current user sees every group in which the user is a member, and the balance of the user in
each group. The user creates a group, joins a group with an invite code, renames a group and leaves
a group. The base currency of a group is set once.

## Behaviour

### Groups home

1. The page `/` lists the groups in which the current user is a member.
2. Each row links to `/groups/ID`. It shows the group name, "N members · N transactions · CUR", the balance of the current user and a label.
3. N transactions counts the expenses and the payments of the group. CUR is the base currency code.
4. The balance is in the base currency of the group. It has a sign: `+12.00 EUR`, `−5.00 EUR`, `0.00 EUR`.
5. The label is "is owed" for a positive balance, "owes" for a negative balance and "settled" for zero.
6. The list is sorted by group name, without case. The user cannot change the sort.
7. The page shows a counter: "SHOWN of TOTAL groups".
8. The page shows no cross-group total. Balances in different base currencies never add up.
9. If the user has no group, the page shows "You are not in any group yet" and the button "Create group". The list is hidden.

### Search and filter

1. The search field "Search groups" matches a substring of the group name, without case.
2. The filter has three options: All (default), "You owe" and "You're owed".
3. "You owe" shows the groups where the balance of the current user is below zero.
4. "You're owed" shows the groups where the balance is above zero.
5. A group with a zero balance shows only under All.
6. The list updates while the user types, and when the user changes the filter.
7. The app does not keep the search and the filter after a reload.
8. If no group matches, the page shows "No groups match", "Try another name or show all groups." and the button "Clear filters".
9. "Clear filters" empties the search, selects All and moves the focus to the search field.

### Create a group

1. The user selects "Create a new group". A dialog "New group" opens with empty fields.
2. The field "Name" holds 1–50 characters after trim. If it is empty, the error is "Give the group a name."
3. If the name is longer than 50 characters, the error is "Use at most 50 characters."
4. Group names need not be unique.
5. The field "Base currency" is a list of 15 currency codes, shown as "CODE — symbol". The default is `EUR`.
6. The list holds: `EUR USD GBP CHF JPY CAD AUD SEK NOK DKK PLN CZK INR BRL MXN`.
7. The hint reads "Set once when the group is created."
8. On submit, the app creates the group and an invite code. The current user becomes the first member.
9. The app redirects to `/groups/ID` and shows "NAME created. Invite people with its code."

### Invite code

1. The code has the form `XXX-YYYY`.
2. `XXX` is the first 3 letters and digits of the group name, in capitals. If the name has fewer, the app pads with `X`. If it has none, the prefix is `GRP`.
3. `YYYY` is 4 characters from `ABCDEFGHJKMNPQRSTUVWXYZ23456789`. The alphabet has no `0`, `O`, `1`, `I`, `L`.
4. If the code exists, the app draws a new `YYYY` until the code is unique.
5. The code never changes. A rename does not change it.

### Group page and settings

1. The page `/groups/ID` shows the members panel and the transactions panel. [Members](./members.md) and [balances](./balances.md) own them.
2. The topbar breadcrumb shows "Groups > NAME" and a chip with the base currency code.
3. If the group does not exist, or the current user is not a member, the app shows "That group is not available to you." and redirects to `/`.
4. The user selects the group name in the breadcrumb. The dialog "Group settings" opens.
5. The field "Name" follows the name rules of "Create a group".
6. The field "Base currency" is disabled. The hint reads "The base currency cannot change after the group is created."
7. The server ignores a base currency in the request. The base currency never changes.
8. On save, the app shows "Group updated" and redraws the topbar.
9. The app has no delete and no archive of a group.

### Invite dialog

1. The user selects "Invite" in the members panel. The dialog "Invite to group" opens.
2. The dialog shows "Share this code to invite people to NAME." and the code in a code box.
3. The dialog shows "They sign in, then enter it under Join with a code on the Groups page."
4. "Copy code" copies the code to the clipboard and shows "Code CODE copied".
5. If the browser blocks the clipboard, the app shows the code in a toast to copy by hand.
6. "Done" closes the dialog.
7. Any member of the group can open the dialog.

### Join with an invite code

1. The page `/` shows the card "Join with a code" with one field and the button "Join".
2. The app trims the code and changes it to capitals before the match.
3. If the field is empty, the error is "Enter an invite code."
4. If no group has the code, the error is "No group uses this code. Check it with the person who invited you."
5. If the current user is a member, the app shows "You are in NAME" and opens the group.
6. Otherwise the app adds the current user as the last member of the group. Join order is the order of the members.
7. The app shows "You joined NAME" and opens the group.
8. The join needs no approval. Any signed-in user who knows the code can join.

### Leave a group

1. The member detail of the current user shows the button "Leave group".
2. If the current user has an expense or a payment in the group, the button is disabled. [Members](./members.md) defines this rule.
3. If the user selects the button, a confirmation opens: "Leave NAME?", "You can rejoin later with the invite code.", ok "Leave group".
4. On confirm, the app deletes the member of the current user.
5. The app shows "You left NAME" and redirects to `/`.
6. The user keeps the user record. Rejoin puts the user last in the join order.

## Data

The feature owns the table `groups`. It reads `users`, `members`, `expenses` and `payments`.

| Column | Type | Rule |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Assigned by SQLite |
| `name` | TEXT NOT NULL | `CHECK (length(name) BETWEEN 1 AND 50)` |
| `currency` | TEXT NOT NULL | Base currency code. One of the 15 codes. The app never updates it |
| `invite_code` | TEXT NOT NULL UNIQUE | `XXX-YYYY` |
| `created_at` | TEXT NOT NULL | Entry time, UTC ISO 8601 |

- The base currency code is the stored identifier. The symbol and the decimals come from `app/core/money.py`.
- The balance of the current user in each row of the list comes from [balances](./balances.md). The list never stores it.
- The app creates the group and the first member in one transaction.

## Implementation

| Item | Place |
|---|---|
| Routes, rules, SQL | `app/groups/routes.py`, `service.py`, `repo.py`, `schemas.py`, `api.py` |
| Balance of the current user | `balances.service.balances_of_groups`. The groups service calls it once for all groups of the user. It runs 4 queries and uses `compute_balances` for each group |
| Invite code prefix | `invite_prefix` in `service.py`. It keeps the ASCII letters `A` to `Z` and the digits only. It drops other characters, for example `é` |
| Currency list, symbols, decimals | `app/core/money.py` |
| Pages | `app/templates/pages/groups_home.html`, `app/templates/pages/group.html` |
| Fragments | `app/templates/partials/groups/`: `list.html` (root `#group-list-region`), `join_card.html` (root `#join-region`), `create_dialog.html` and `create_form.html`, `settings_dialog.html` and `settings_form.html`, `invite_dialog.html`, `topbar.html` |
| Macros | `group_row` in `rows.html`, `balance_amount` in `money.html`, `dialog` and `dlg_head` in `overlays.html`, `code_box` in `data.html`, `segmented` and `select_field` in `forms.html`, `empty_state` in `feedback.html` |

A dialog `GET` is a fragment. If a request has no `HX-Request` header, the route redirects to the page that holds the fragment.

| Method and URL | Returns |
|---|---|
| `GET /` | Page: the groups home |
| `GET /groups/list?q=TEXT&filter=VALUE` | Fragment: the list and the empty states. The counter is outside the fragment. The fragment updates it with `hx-swap-oob`. VALUE is `all`, `owe` or `owed` |
| `GET /groups/new` | Fragment: the dialog "New group" |
| `POST /groups` | Redirect to `/groups/ID`. Status 422 and the form fragment on error |
| `POST /groups/join` | Redirect to `/groups/ID`. Status 422 and the card fragment on error |
| `GET /groups/{id}` | Page: the group |
| `GET /groups/{id}/settings` | Fragment: the dialog "Group settings" |
| `POST /groups/{id}/settings` | Empty swap (`HX-Reswap: none`). The body holds the topbar with `hx-swap-oob`. Events `toast`, `close-dialog`. Status 422 and the form fragment on error |
| `GET /groups/{id}/invite` | Fragment: the invite dialog |
| `POST /groups/{id}/leave` | Redirect to `/`. Status 409 with events `toast`, `close-dialog`, `members-changed` if the member has a transaction. Status 404 with a redirect to `/` if the user is not a member |
| `GET /api/v1/groups?q=TEXT&filter=all\|owe\|owed` | JSON: the groups of the user, each with `member_count`, `transaction_count` and `balance` (minor units of `currency`) |
| `POST /api/v1/groups` | Status 201, JSON: the group `{id, name, currency, invite_code}`. Body `{"name", "currency"}`. Status 422 with `fields` on error |
| `GET /api/v1/groups/{id}` | JSON: the group. Status 404 if the user is not a member |
| `PATCH /api/v1/groups/{id}` | JSON: the renamed group. Body `{"name"}`. Status 422, status 404 |
| `POST /api/v1/groups/join` | Status 200, JSON: the group, also if the user is a member of the group. Body `{"code": "LIS-7K2Q"}`. Status 422 if the code is wrong |

Every `/groups/{id}…` route checks that the current user is a member. The check is `require_member` in `service.py`. It raises `NotFound`.

A path id that is not a number, or is below 1 or above 2^63 - 1, is an unknown id. The route answers as it does for an id that does not exist.

A redirect from an htmx request is the header `HX-Location` and the flash cookie. A request without htmx gets status 303. The group page, for a user who is not a member, redirects to `/` with the flash "That group is not available to you.". A dialog route answers status 404.

## Failure & idempotency

- If the group name or the code is invalid, the app answers with status 422 and re-renders the form with the field errors. It writes nothing.
- If a user joins twice, the second request finds the member and answers "You are in NAME". It adds no row.
- If a user submits "Create a new group" twice, the app creates two groups. Group names need not be unique.
- If the invite code collides at insert, the `UNIQUE` index rejects the row. The service draws a new code and retries up to 10 times.
- If a user leaves a group in another tab first, the second leave answers status 404 and redirects to `/`.
- If the last member leaves, the group stays with no member. Only the invite code opens it again. See [backlog](../backlog.md).

## Assumptions

- All users share one database. A user can join any group whose code the user knows.
- The invite code is not a secret. Anyone with the code joins.
- A group has one base currency, and all its balances use it.

## Related docs

- [`sign-in.md`](./sign-in.md): the current user
- [`members.md`](./members.md): the members panel, add, remove
- [`balances.md`](./balances.md): the balance of the current user and the transaction list
- [`../product/overview.md`](../product/overview.md): MVP-01 and the scope
- [`../product/glossary.md`](../product/glossary.md): Group, Base currency, Invite code, Leave
- [`../tech/architecture.md`](../tech/architecture.md): layers and request flow
- [`../tech/guide-navigation.md`](../tech/guide-navigation.md): URL naming rules, dialogs and fragments
- [`../tech/design-system.md`](../tech/design-system.md): regions, dialogs and events
- [`../backlog.md`](../backlog.md): Invite and invite code, group without members, bootstrap scope

## Next steps

- Delete or archive a group (F4).
