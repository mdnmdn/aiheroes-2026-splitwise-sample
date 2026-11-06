---
id: backlog
title: Backlog
kind: product
status: current
summary: Every open question, known gap and deferred item, project-wide.
read_when: you plan the next piece of work, or you hit something this project has not decided
updated: 2026-11-05
verified: 2026-11-05
review_cycle: monthly
---

# Backlog

Each line names the document it affects. An empty section is a valid state. This file records what
the project has not decided. It is not a task tracker: it holds no assignees, estimates or dates.

A human resolves an item. Then the answer goes into the owning document, and the line is deleted.

## Open questions

- **Payer outside the participants.** Can a payer pay for an expense without being a participant,
  for example a gift? The specification assumes yes. Affects `product/overview.md`,
  `product/glossary.md` (Payer).
- **Lowest expense date.** The app accepts any past date, for example 0001-01-01. A human decides a
  lower bound. Affects `features/expenses.md`, `features/payments.md`.
- **Exchange-rate source (F3).** Which source supplies the rate, and what happens offline. Affects
  `product/overview.md`.
- **Base currency change (F3).** Can a group change its base currency later, and how are past
  balances converted. Affects `product/overview.md`, `product/glossary.md` (Base currency).
- **Undo depth (F6).** Is undo limited to the last change, or a full history. Affects
  `product/overview.md`, `product/glossary.md` (Undo).
- **Member who leaves (F9).** What happens to the data of a member who leaves a shared group.
  Affects `product/overview.md`.
- **Open user creation and adding members.** In the simulation, anybody can create users with
  `POST /api/v1/users`, and any member can add any user to a group without consent. A human decides
  the rules for real accounts (F9). Affects `features/sign-in.md`, `features/members.md`.
- **Double submit of a new user.** `features/sign-in.md` says a double submit signs in as the user
  the first request created, and also that a taken name gives the name-exists error. The code gives
  the error. Affects `features/sign-in.md`.
- **Product name.** The specification says *Splitwise*. The project says *Splitwise Lite*. A human
  picks one name for the product text. Affects `product/overview.md`, `Home.md`, `AGENTS.md`.
- **Bootstrap scope versus MVP scope.** The HTML design covers simulated sign-in, many groups, join
  codes, settle-up and other items that `product/overview.md` places after the MVP (F2, F4, F9). The
  human asked to build the bootstrap from the design. A human decides how `product/overview.md`
  records this. Affects `product/overview.md`, `features/`.
- **Design vocabulary.** The HTML design labels an expense as "payment" and a payment as "internal
  transfer" (also "from/to", "Person"). The app uses glossary terms. A human decides whether the
  design labels change. Affects `_design/site/`, `product/glossary.md`.
- **Balance labels.** The design says "gets back" and "settled up". The app says "is owed" and
  "settled", as the glossary does. A human decides. Affects `_design/site/`, `product/glossary.md`.
- **Radius captions in the storybook.** The captions of `storybook.html` (Spacing and radius) give
  other pixel values than the tokens `--r-sm`, `--r-md` and `--r-lg` in `splitwise.css`. The
  stylesheet is the source. A human decides whether the captions change. Affects `_design/site/`,
  `tech/design-guidelines.md`.
- **Greedy settlement plan (F2).** The settle-up dialog of the design uses the greedy method. It may
  not give the fewest payments that the glossary requires. A human decides the method for F2. Affects `product/glossary.md` (Settlement plan),
  F2 in `product/overview.md`, `features/balances.md`.
- **Amount text in the design.** The design script accepts `12.` (a point and no decimals) and the
  message "Amount must be more than zero." The app follows `features/expenses.md`: it rejects `12.`
  and says "The amount must be more than zero." A human decides whether the design script changes.
  Affects `_design/site/assets/splitwise.js`, `features/expenses.md`.
- **Server date in UTC.** `features/expenses.md` defines the server date in UTC. `clock.today_iso`
  used the local date of the server before step 3. Step 3 changed it to UTC. The date input of the
  dialog still shows the date format of the browser. Affects `features/expenses.md`, `core/clock.py`.
- **Note on a payment.** The design lets a payment have an optional note. The glossary defines Note
  for an expense only (F5). Affects `product/glossary.md` (Note), `features/payments.md`.
- **Invite and invite code.** The glossary **Invite** (F9) is a link. The invite code of the design
  overlaps with it. A human decides. Affects `product/glossary.md` (Invite, Invite code).
- **User and member in the bootstrap.** The glossary says one user and no account, and a member can
  exist without a user. The bootstrap has many simulated users, and each member is a user. Affects
  `product/glossary.md` (User, Member), `features/members.md`, `features/sign-in.md`.
- **Group without members.** When the last member leaves a group, the group stays with no member.
  Only its invite code can bring a user back. A human decides whether the app deletes such a group.
  Affects `features/groups.md`.
- **Payment receiver error.** `features/payments.md` lists the error "Choose the sender." and a rule for sender equal to receiver. The code also gives "Choose the receiver." when the receiver is missing or not a member. Affects `features/payments.md`, `app/payments/service.py`.
- **Mine empty state text.** `features/balances.md` says the empty Mine list shows "Nothing involves you yet." The template shows the title without a full stop and a second text. Affects `features/balances.md`, `partials/balances/transactions.html`.
- **Delete confirmation route.** `tech/guide-navigation.md` says a confirmation dialog is a `GET` of `/{id}/delete`. The code has no such route: a `POST .../delete` from a button with `data-confirm-*` does it. Affects `tech/guide-navigation.md`, `app/static/js/splitwise.js`.
- **Style attribute in templates.** `tech/design-system.md` and `tech/guide-navigation.md` say a template sets no design value in a `style` attribute. Templates use `style="--od-gap:..."` and `avatar` sets `style="--h:..."`. Affects both documents, `app/templates/`.
- **Button busy state.** The section "Buttons" of `tech/design-guidelines.md` and the section "Loading state" of `tech/design-system.md` say a button gets `aria-busy="true"` while its request runs. `app.js` never sets it. Only `hx-disabled-elt` shows the state. Affects both documents, `app/static/js/app.js`.
- **Script health banner.** The sections "Open the files" and "Accessibility rules" of `tech/design-guidelines.md` say a page shows a banner when a shared script is missing. The design pages do it, but `base.html` has only a `<noscript>` banner. Affects `tech/design-guidelines.md`, `app/templates/base.html`.
- **Expense participant errors and hint.** The code (`validate` in `app/expenses/service.py`) also gives "Choose members of this group only." for a participant that is not a member or that repeats. The share hint reads "1 participant" for one participant. The fields table of `features/expenses.md` gives only "Pick at least one participant." and "N participants". Affects `features/expenses.md`.

## Known gaps

- **Feature contracts.** The MVP and F1–F9 contracts live inside `product/overview.md`. Each becomes
  a `features/` document when a human has decided enough of it to have its own contract. See `_meta/feedback.md`.

## Deferred

