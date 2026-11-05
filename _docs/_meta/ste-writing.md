---
id: meta-ste-writing
title: STE writing (project dialect)
kind: meta
status: current
summary: The Splitwise Lite dialect of Simplified Technical English. The rules agents apply when they write AGENTS.md, procedures, prompts, CLI help, error messages, commit messages and Behaviour sections.
read_when: you write or rewrite text that an agent or a non-native reader must read without help
updated: 2026-11-05
verified: 2026-11-05
depends_on: [prod-glossary, meta-asd-ste-100]
review_cycle: yearly
---

# STE writing (project dialect)

Write so that each sentence has one reading and each word has one meaning. An agent that reads
the wrong meaning records the wrong expense or computes the wrong balance. STE fixes form, not
content: never drop a fact and never add one.

This project adopts [ASD-STE100](./asd-ste-100.md) with the changes in this document. The
[glossary](../product/glossary.md) is the dictionary: one entry per term, one meaning.

## Where STE applies

Every document that an agent writes or changes in `_docs/` and `AGENTS.md` follows this dialect.
The table gives the mode for each text. Two exceptions: `_docs/inbox/` and `_docs/_meta/asd-ste-100.md`.

| Text | Mode |
|---|---|
| `AGENTS.md`, procedures in `_meta/`, prompts, standing instructions | Procedural |
| CLI help, error messages, commit messages | Procedural |
| Feature `## Behaviour` sections | Procedural for steps, descriptive for facts |
| Tool descriptions, reports | Descriptive |
| Product text, rationale, decision rows | Flavoured |

## 1. Modes

| Mode | Limits |
|---|---|
| **Procedural** | 20 words per sentence. One instruction per sentence. Imperative. Condition first |
| **Descriptive** | 25 words per sentence. Active voice. One condition per sentence. Six sentences per paragraph at most |
| **Flavoured** | Sentence rules are guidance. Vocabulary rules still apply |

A code identifier, flag, path, number with unit, or quoted text counts as one word.

## 2. Process

1. Read the text once for meaning. List its facts, conditions, limits and real hedges.
2. Pick the mode for each part. A document can mix modes by section.
3. Walk sentence by sentence. Fix each violation of §3 and §4.
4. Read the text again. Check the word limit of the mode, the forbidden words and the never-bare words.
5. Compare the result with your list from step 1. If precision would be lost, keep the longer form.
6. If the text already complies, say so and change nothing.

Stop when a sentence is unambiguous, not when it is shortest.

## 3. Sentence rules

- One sentence, one idea. One step, one action, unless the actions occur at the same time.
- Use the active voice and name the actor: "The app rejects the expense", not "The expense is rejected".
- Use simple tenses only: present, past, future, imperative. No "has been", no "is doing".
- Never use "-ing" as a verb: "When you add a member", not "When adding a member".
- Use a verb for an action, not a noun: "validate the amounts", not "perform a validation of the amounts".
- Write the condition first, then a comma, then the command: "If a member has no expense, hide the member from the payer list."
- No semicolons. No dash that joins two clauses. Split into two sentences.
- No contractions. Do not drop articles or subjects.
- A noun cluster has three words at most. Break longer ones with "of", "for", "that".
- No phrasal verbs: "start", not "spin up".
- No Latin abbreviations: "for example", not "e.g.". No "etc.".
- Use a vertical list for three or more steps, conditions or items.
- Keep a hedge that carries real uncertainty. Delete filler hedges.

## 4. Dialect rules

**Normative strength.**

- A required action is an imperative. A prohibition starts with "Never" or "Do not".
- No lowercase "should", "may", "might", "try to" in a rule. Write MUST, SHOULD, MAY in capitals only in specifications.
- After each hard rule, write one descriptive sentence with the reason.
- Do not shout: no "CRITICAL", no "ALWAYS" in capitals, no "!!!".
- Write WARNING only before an action that can give a member a wrong balance or corrupt stored money values.
- Write CAUTION only before an action that can lose data, for example delete a group or wipe `_data/`.

**Identifiers.** Write code names, flags, paths, JSON fields and commands verbatim, in code font.
Do not inflect them: "the `Expense` fields", not "`Expense`'s fields".

**One word per concept.** Use the left column. Never the right column. The
[glossary](../product/glossary.md) defines each term.

| Use | Not |
|---|---|
| expense | bill, charge, purchase |
| member (a person in a group) | friend, person, participant (when you mean any member) |
| user (the person who operates the app; an account holder from F9) | member (when you mean the operator) |
| payer | buyer, spender |
| participant (a member who owes part of an expense) | debtor, beneficiary |
| share | portion, cut, part (of an expense) |
| payment (a recorded transfer between members) | settlement, transfer, reimbursement, repayment |
| balance | debt, net, net position (in a rule) |
| settlement plan | simplification, debt graph |
| group | team, circle, party |
| amount (money, with a currency) | sum, value, price |
| minor units (integer, for example cents) | cents (in a rule), pennies, decimals |
| currency code (`EUR`, ISO 4217) | currency symbol (as a stored value) |
| base currency | group currency, home currency |
| split mode (equal, exact, percentage, shares) | split type, split method |
| exchange rate | FX rate, conversion rate |
| record (a payment) | pay, settle, send (the app never moves money) |
| delete | remove (for expenses and payments). "Remove" is for members only |

**Never bare.** Qualify each of these words every time:

- *amount*: which currency, and major or minor units?
- *balance*: whose balance, and what does the sign mean?
- *owe*: who owes whom?
- *split*: the verb, or the split mode?
- *settle*, *settled*: record a payment, or all balances are zero?
- *date*: the expense date, or the entry time?
- *user*: the operator, or a member?
- *currency*: the base currency, or the expense currency?
- *total*: the total of what, in which currency?

**Numbers, units, time.**

- Write money with the currency code: `90.00 EUR`. Write stored money in minor units: `9000`.
- The balance sign carries the meaning. `+60.00 EUR` means the member is owed money. `−30.00 EUR` means the member owes money.
- Write dates in ISO 8601: `2026-11-05`. Write times in UTC ISO 8601: `2026-11-05T10:00:00Z`.
- Every percent says what it is of: "20% of the expense amount".
- Every range states its bounds: `[2026-01-01, 2026-02-01)`.
- No "today", "now", "recently" in a document.

## 5. Patterns

| Text | Pattern |
|---|---|
| Agent rule | `<command>. <reason>.` |
| Error message | `<what failed>: <why>. <what to do>.` |
| CLI flag help | `<verb> <object>. Default: <value>.` |
| Behaviour rule | One condition and one result per sentence |
| Acceptance example | `<inputs> → <balances>`, with the currency code on each amount |
| Commit subject | Conventional commit, imperative, 72 characters or fewer. The body tells why |

Examples:

```text
Never delete a group without the owner's request. A deleted group loses all its expenses and payments.
expense rejected: the shares add up to 80.00 EUR, the amount is 90.00 EUR. Change the shares so they add up to 90.00 EUR.
--currency CODE   Set the base currency of the group. Default: EUR.
Alice pays 90.00 EUR for Alice, Bob, Carla → Alice +60.00 EUR, Bob −30.00 EUR, Carla −30.00 EUR
docs: add the split modes to the expense feature
```

## 6. Boundaries

- Never change code, identifiers, commands, numbers or quoted text.
- Never change requirement strength: "can fail" stays "can fail", "never" stays "never".
- Never edit `_docs/inbox/`. Raw input stays verbatim.
- Documents keep their own rules too: present tense, no time words, frontmatter (see [authoring](./authoring.md)).
- STE does not make empty text useful. If a sentence has no fact, delete it and say so.

## Related docs

- [`./asd-ste-100.md`](./asd-ste-100.md): the external standard, its 53 rules and its evidence
- [`../product/glossary.md`](../product/glossary.md): the dictionary of project terms
- [`./authoring.md`](./authoring.md): the writing procedure that applies these rules
- [`./tools.md`](./tools.md): the project scripts
