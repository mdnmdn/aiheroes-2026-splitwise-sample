---
id: prod-glossary
title: Glossary
kind: product
status: current
summary: The product vocabulary. One definition per term, and the words that are not used for it. The dictionary of the STE dialect.
read_when: you write a product, feature or procedural text and need the exact word for a concept, or you introduce a new term
updated: 2026-11-05
verified: 2026-11-05
review_cycle: quarterly
---

# Glossary

This document owns the product vocabulary. Every other document uses these terms with these
meanings. Each document links here and does not define a term again. The writing rules that apply the
vocabulary are in [`../_meta/ste-writing.md`](../_meta/ste-writing.md). One word names one concept.
The words in the *Not* column are not used for that concept.

A new term gets a row here first, then it can appear in another document. A term that changes
meaning is a product decision for a human, not an edit.

## Core model

Everything derives from expenses and payments. Balances are computed, never stored or edited.

| Term | Definition | Not |
|---|---|---|
| **Group** | A named set of members who share expenses. A group has one base currency. | team, circle, party |
| **Member** | A person in a group, identified by a display name. A member can exist without a user account. | friend, person |
| **User** | The person who operates the app. In the MVP there is one user and no account. From F9, a user has an account and can be linked to a member. | member (for the operator) |
| **Expense** | A cost that one member pays on behalf of some or all members. It has a description, an amount, an expense date, a payer and participants. | bill, charge, purchase |
| **Payer** | The member who paid an expense. The payer can be a participant or not. | buyer, spender |
| **Participant** | A member who owes a share of an expense. | debtor, beneficiary |
| **Share** | The part of an expense that one participant owes. The shares of an expense always sum to its amount. | portion, cut, part |
| **Payment** | A recorded transfer of money from one member (the sender) to another member (the receiver). It settles debts. The app records payments and never moves money. | settlement, transfer, reimbursement, repayment |
| **Sender / receiver** | The two members of a payment: the sender gives money, the receiver gets it. They are always different members. | payer (for a payment) |
| **Balance** | A per-member figure: total paid for expenses, minus total of the member's shares, plus payments sent, minus payments received. A positive balance means the member is owed money. A negative balance means the member owes money. | debt, net, net position |
| **Settlement plan** | A suggested list of payments that brings every balance in a group to zero, with as few payments as possible (F2). | simplification, debt graph |
| **Settled** | The state of a group in which every balance is zero. | paid off, closed |

**Balance invariant.** The total of all balances in a group is always exactly zero. A violation is a bug, not a user error.

## Money

| Term | Definition | Not |
|---|---|---|
| **Amount** | A quantity of money in one currency. Written with its currency code: `90.00 EUR`. | sum, value, price |
| **Minor units** | The integer form of an amount in the smallest unit of its currency (cents for `EUR`, units for `JPY`). Money is stored in minor units, never as a floating-point number: `90.00 EUR` is `9000`. | decimals, pennies |
| **Currency code** | The ISO 4217 three-letter code of a currency (`EUR`, `USD`, `JPY`). The stored identifier of a currency. The symbol is display only. | currency symbol (as a stored value) |
| **Base currency** | The currency of a group, set when the group is created. All balances are in the base currency. | group currency, home currency |
| **Expense currency** | The currency in which an expense was paid (F3). It can differ from the base currency. | original currency |
| **Exchange rate** | The rate that converts an expense currency to the base currency. It is stored with the expense and does not change after the expense is saved (F3). | FX rate, conversion rate |
| **Remainder** | The minor units left after an amount is divided into shares. The equal split mode gives one minor unit each to participants in join order. | rounding error |
| **Join order** | The order in which members joined a group. It is the stable order for remainder distribution. | creation order |
| **Largest-remainder method** | The rounding method for the percentage and shares split modes. Shares are rounded down, then the remaining minor units go to the participants with the largest fractional parts. | — |

## Splits

| Term | Definition | Not |
|---|---|---|
| **Split** (verb) | To divide the amount of an expense into shares. | — |
| **Split mode** | The rule that divides an expense into shares: *equal* (the MVP default), *exact amounts*, *percentages* or *shares* (F1). | split type, split method |
| **Equal** | The split mode that gives every participant the same share, plus or minus one minor unit of remainder. | even split |
| **Exact amounts** | The split mode in which the user enters each share. The shares sum to the amount of the expense. | custom amounts |
| **Percentages** | The split mode in which each share is a percentage of the amount. The percentages sum to 100%. | — |
| **Shares** (split mode) | The split mode in which each participant has a weight, for example 2:1:1. Each share is proportional to the weight. | ratio, weights |

## Time

| Term | Definition | Not |
|---|---|---|
| **Expense date** | The calendar date on which an expense occurred, chosen by the user. It cannot be in the future. | date (bare), created date |
| **Payment date** | The calendar date of a payment, chosen by the user. | date (bare) |
| **Entry time** | The UTC time at which the app recorded a change. The activity log shows it (F6). | timestamp (bare) |

## Later features

| Term | Definition | Not |
|---|---|---|
| **Archived group** | A group that is read-only. It stays in the group list (F4). | closed group, deleted group |
| **Category** | An optional label of an expense from a fixed list: food, transport, housing, utilities, entertainment, other (F5). | tag, type |
| **Note** | An optional free text attached to an expense (F5). | comment, memo |
| **Activity log** | The list of every create, edit and delete of an expense, a payment or a member, with the entry time and the values before and after (F6). | history, audit trail |
| **Undo** | The action that reverses the last change in the activity log (F6). | revert, rollback |
| **Recurring expense** | An expense template that repeats weekly or monthly with the same split mode and shares (F7). | subscription, repeat |
| **Occurrence** | One expense that a recurring expense creates on its date. It is a normal expense. | instance |
| **Export / import** | Export writes the expenses and payments of a group to CSV, or the full group to JSON. Import reads a JSON export to restore or move a group (F8). | backup, download |
| **Account** | The sign-in identity of a user (F9). | profile, login |
| **Group owner** | The user who created a shared group. The owner invites people and can edit or delete any expense (F9). | admin |
| **Invite** | A link that a group owner sends to add a person to a shared group (F9). | invitation code |
| **Claim** (a member) | The action in which an invitee links their account to an existing member of the group (F9). | merge, adopt |

## Related docs

- [`overview.md`](./overview.md): the product specification that uses these terms
- [`../_meta/ste-writing.md`](../_meta/ste-writing.md): the writing rules that apply this vocabulary
- [`../backlog.md`](../backlog.md): terms whose meaning a human has not decided
