---
id: prod-overview
title: Product overview and specification
kind: product
status: current
summary: The vision and users of Splitwise Lite, the MVP contract, the roadmap F1–F9, quality requirements and success metrics.
read_when: you decide whether something is in scope, or you change what the MVP or a roadmap feature does
updated: 2026-11-05
verified: 2026-11-05
depends_on: [prod-glossary]
review_cycle: monthly
---

# Splitwise — Product Specification

## Vision and goals

Splitwise lets a group of people record shared expenses. The group always knows, at a glance, who owes whom and how to bring every balance to zero.

**Problem.** Flatmates, travel companions and friends share expenses constantly. Members track them in chats or spreadsheets. This leads to forgotten balances, arithmetic errors and awkward conversations.

**Target users**

- Flatmates who share rent, utilities and groceries over months
- Friends on a trip who share expenses over days, often in several currencies
- Couples or small groups with an ongoing shared account

**Product goals**

1. Adding an expense takes under 15 seconds.
2. Balances are always correct to the minor unit. The expenses and payments behind each balance explain every number.
3. A group needs as few payments as possible to bring every balance to zero.
4. Nobody has to trust the member who entered an expense. Every change is visible to the group.

**Non-goals**

- Moving money: Splitwise records payments and never moves money.
- Personal budgeting or spending analytics.
- Accounting or tax features for businesses.

## Core concepts

Everything in Splitwise derives from expenses and payments. The app computes balances. Nobody stores or edits a balance by hand.

The [glossary](./glossary.md) defines the core terms: group, member, expense, payer, participant, share, payment, balance and settlement plan. It also defines the balance invariant (the total of all balances in a group is zero).

## Part 1 — MVP specification

The MVP lets one group record equal-split expenses in a single currency. The user sees correct balances and records payments between members.

### Scope

- One base currency per group. The user sets it when the user creates the group and cannot change it.
- Equal split mode only.
- Single-user app: whoever opens it can edit everything. No accounts, no sharing, no permissions.
- Local persistence. Data survives restarts.

### User stories

1. As a user, I create a group with a name and a base currency, so I can start tracking.
2. As a user, I add, rename and remove members, so the group matches reality.
3. As a user, I add an expense with description, amount, expense date, payer and participants (default: every member), so the app records the expense.
4. As a user, I edit or delete an expense, so I can fix mistakes.
5. As a user, I see the balance of each member, so I know who owes money and who is owed money.
6. As a user, I see the expense list, newest first, with the payer and the participants of each expense.
7. As a user, I record a payment from one member to another, so balances include that payment.
8. As a user, I open a member and see which expenses and payments make up the balance of that member.

### Functional requirements

| ID | Requirement |
| --- | --- |
| MVP-01 | A group has a name (1–50 characters) and a base currency. The app stores the base currency as an ISO 4217 currency code. |
| MVP-02 | A member name is unique within a group (case-insensitive) and has 1–30 characters. |
| MVP-03 | The app never removes a member who has an expense or a payment. The user can rename that member. |
| MVP-04 | An expense requires a description (1–100 characters), an amount > 0, an expense date, one payer and at least one participant. |
| MVP-05 | An expense date or payment date can be in the past. The app rejects a date in the future. |
| MVP-06 | A payment requires a sender, a receiver (different members), an amount > 0 and a payment date. |
| MVP-07 | After every change, the app recomputes the balances from all expenses and payments. |
| MVP-08 | Before the app deletes an expense or a payment, it asks for confirmation. |

### Business rules

- **Money is stored as integer minor units**, never as a floating-point number.
- **Equal split rounding:** The app divides the amount of the expense by the number of participants. The remainder minor units go one each to the participants in join order. Example: `10.00 EUR` split equally between 3 participants gives shares of `3.34 EUR`, `3.33 EUR` and `3.33 EUR`.
- The shares of an expense always add up exactly to the amount of the expense.
- The total of all balances is always zero. A violation is a bug, not a user error.
- The app shows each amount with the standard decimals and the symbol of its currency.

### Acceptance criteria (examples)

- Alice pays `90.00 EUR` for Alice, Bob, Carla → Alice `+60.00 EUR`, Bob `−30.00 EUR`, Carla `−30.00 EUR`.
- Bob then records a payment of `30.00 EUR` to Alice → Alice `+30.00 EUR`, Bob `0.00 EUR`, Carla `−30.00 EUR`.
- The user deletes the first expense → Alice `−30.00 EUR`, Bob `+30.00 EUR`, Carla `0.00 EUR`.

### Out of scope for the MVP

- Uneven splits
- Multiple currencies
- Settlement suggestions
- Accounts and sharing
- Categories
- Attachments
- Notifications
- Export

## Part 2 — Next features

After the MVP, Splitwise grows in the order below. Each feature builds on the MVP model and does not change how balances are defined.

| # | Feature | Depends on |
| --- | --- | --- |
| F1 | Uneven splits | MVP |
| F2 | Settlement plan | MVP |
| F3 | Multi-currency | F1 |
| F4 | Multiple groups and overview | MVP |
| F5 | Categories, notes, search | MVP |
| F6 | Activity log and undo | MVP |
| F7 | Recurring expenses | F1 |
| F8 | Export and import | F3 |
| F9 | Accounts, invites and sharing | F4, F6 |

### F1 — Uneven splits

Goal: describe how the members share an expense in fact, not only equally.

- Split modes: **equal** (default), **exact amounts**, **percentages** and **shares** (for example 2:1:1).
- In exact amounts mode, the shares must add up to the amount of the expense. In percentages mode, the percentages must add up to 100%.
- The form shows the remaining amount live. It blocks saving until the remaining amount is zero.
- The app rounds the percentages and shares split modes with the largest-remainder method. The shares of the expense still add up exactly to its amount.
- Editing an expense keeps its split mode.

### F2 — Settlement plan

Goal: bring every balance in a group to zero with as few payments as possible.

- The app shows a settlement plan computed from the current balances. The plan has no more than (members with a non-zero balance − 1) payments.
- The user can record each suggested payment in one action. The action creates a normal payment.
- A group whose balances are all zero shows as “settled”.

### F3 — Multi-currency

Goal: record expenses in the currency in which the payer paid, for example on a trip abroad.

- Each expense has its own expense currency. The group keeps one base currency for balances.
- The expense stores the original amount, the expense currency and the exchange rate used. The app stores the converted shares in the base currency.
- The exchange rate defaults to the rate on the expense date. The user can override it manually.
- After the user saves an expense, its converted amount never changes when exchange rates change.

### F4 — Multiple groups and overview

- A user can keep many groups, each with its own base currency.
- A home screen lists the groups. For each group, it shows the balance of the user.
- A user can archive a group. An archived group is read-only.

### F5 — Categories, notes, search

- Each expense has an optional category from a fixed list (food, transport, housing, utilities, entertainment, other).
- Each expense has an optional note.
- The user can filter expenses by member, category and date range. The user can search expenses by description.

### F6 — Activity log and undo

- The app logs every create, edit and delete of an expense, a payment or a member. Each entry has the entry time and the values before and after.
- The user can undo the last change. The user can restore a deleted expense from the log.

### F7 — Recurring expenses

- An expense can repeat weekly or monthly with the same split mode and shares. It repeats until an end date or indefinitely.
- The app creates each occurrence on its date as a normal expense. Editing the template affects future occurrences only.

### F8 — Export and import

- The user can export the expenses and payments of a group as CSV. The user can export the full group as JSON.
- The user can import a JSON export to restore or move a group.

### F9 — Accounts, invites and sharing

- Users sign in. A member can be linked to a user account.
- A group owner invites people by link. An invitee claims an existing member or joins as a new member.
- Every member can add expenses. Only the creator of an expense or the group owner can edit or delete it.
- Changes sync to the devices of all members.

## Quality requirements and success metrics

Correctness of money comes before every other quality. A wrong balance is the one unacceptable failure.

**Quality requirements**

- **Correctness:** Automated tests cover the balance logic and the split logic. The tests include rounding edge cases: `0.01 EUR` split equally between 3 participants, large amounts, and currencies with zero decimals such as `JPY`.
- **Responsiveness:** Any screen loads and any balance recomputes in under 200 ms for a group of 20 members and 2,000 expenses.
- **Usability:** The app works on a phone-sized screen. The user reaches each core flow in two taps from the group screen.
- **Accessibility:** The app meets WCAG 2.2 AA. The app never conveys an amount by color alone. The app also shows a sign or a label for owes money and is owed money.
- **Data safety:** No data loss on restart or crash. The app asks for confirmation before each destructive action.
- **Localization-ready:** All text and all number and date formatting go through a locale layer. English is first.

**Success metrics**

| Metric | Target |
| --- | --- |
| Median time to add an expense | < 15 s |
| Balance errors reported | 0 |
| Groups with at least 5 expenses after one week | > 50% |
| Settled groups that used the settlement plan (after F2) | > 70% |

## Related docs

- [`glossary.md`](./glossary.md): the definition of every term used here
- [`../backlog.md`](../backlog.md): the open product questions this specification leaves open
