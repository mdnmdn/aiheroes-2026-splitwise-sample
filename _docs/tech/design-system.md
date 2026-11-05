---
id: tech-design-system
title: Design system and templates
kind: tech
status: current
summary: How the HTML design in `_design/site/` becomes the app. Which files are the source of truth, the page shell, the component macros, the HTMX model for fragments and dialogs, the accessibility rules and the reasons for these choices.
read_when: you change a template, a component macro, the CSS or the browser script, or you add a page that must look like the design
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/templates/base.html, app/templates/components/buttons.html, app/templates/components/forms.html, app/templates/components/data.html, app/templates/components/money.html, app/templates/components/rows.html, app/templates/components/feedback.html, app/templates/components/overlays.html, app/templates/components/navigation.html, app/static/js/app.js, app/core/htmx.py, app/core/templating.py, _tools/design_sync.py, _design/site/storybook.html]
depends_on: [prod-glossary, tech-architecture]
review_cycle: quarterly
---

# Design system and templates

The design in `_design/site/` is a set of static HTML pages with one stylesheet and one component
script. The app turns it into server-rendered Jinja2 templates. The design CSS and the component
script stay unchanged. A small file `app/static/js/app.js` connects them to HTMX.

The storybook is the catalogue of components. The three pages are the guideline for the page
shell and the page layouts. [`architecture.md`](./architecture.md) describes the layers. The
procedures to add a page, a fragment, a dialog or a macro are in
[`guide-navigation.md`](./guide-navigation.md).

## 1. Sources of truth

| File | Role | Rule |
|---|---|---|
| `_design/site/storybook.html` | Component reference. Shows each component, its markup and its states | Change it first when a component changes |
| `_design/site/assets/splitwise.css` | The only stylesheet | The app copy is read only |
| `_design/site/assets/splitwise.js` | Component behaviour: icons, forms, confirm, toast, menus, dialogs, appearance | The app copy is read only |
| `_design/site/assets/splitwise-app.js` | Prototype: fake store in `localStorage`, seed data | The app never ships it |
| `_design/site/index.html`, `group.html`, `login.html` | Layout guideline for the pages | Compare each page with its design page |
| `app/static/js/app.js` | The glue between HTMX and `splitwise.js` | Holds no business rule |

`mise run design-sync` copies `splitwise.css` and `splitwise.js` to `app/static/css/` and
`app/static/js/`. Never edit the copies. A change in a copy is lost at the next sync and makes
the app differ from the storybook.

To change a style or a component behaviour, follow these steps:

1. Change `splitwise.css` or `splitwise.js` in `_design/site/assets/`.
2. Change the storybook section of the component in the same session.
3. Run `mise run design-sync`.
4. Change the macro or the template that uses the component.

A template never holds a `<style>` block or a style attribute that sets a value of the design. A
page-only rule belongs in the design CSS, in a commented block of its page.

## 2. Prototype helpers that the app replaces

`splitwise-app.js` holds the data of the prototype. The server owns data and rules. The table
lists each helper and its replacement. A helper that the table omits has no use in the app.

| Prototype helper | Replacement |
|---|---|
| Store: `state`, `load`, `save`, seed data, `migrate` | SQLite, repositories and migrations |
| `me`, `requireUser`, `signIn`, `signOut` | `core/session.py`, `/login` and `/logout`. See [`guide-authentication.md`](./guide-authentication.md) |
| `safeNext` | `safe_next` in `users/service.py` accepts a `next` value only if it is a local path that starts with `/` and not `//`, and that has only safe characters |
| `flash`, `takeFlash` | A one-time flash cookie. The server renders it into `#flash` and `app.js` shows a toast |
| `renderTopbar` | Macro `topbar` in `components/navigation.html`, rendered by `base.html` |
| `avatar(id, size)` | Macro `avatar` in `components/data.html` |
| `shares`, `balances`, `settlePlan`, `involves`, `hasHistory` | Services and `core/money.py`. Templates never compute money |
| `nameError`, `makeCode`, `myGroups`, `group` | Services of the `groups` and `members` features |
| Page scripts that build HTML with strings | Jinja templates in `pages/` and `partials/` |
| `Splitwise.money.fmt`, `fmtSigned`, `parse` | Jinja filters `money` and `signed_money` in `core/templating.py`, and the parser in `core/money.py` |
| `Splitwise.fmtDate` | Jinja filter `date` in `core/templating.py` |
| Dialog open code in the page scripts | `app.js` opens a dialog after HTMX swaps it into the dialog host |
| Toast calls from the page scripts | `HX-Trigger` event `toast`. `app.js` calls `Splitwise.toast` |
| Delete confirm calls | Attributes `data-confirm-*` on the trigger. `app.js` calls `Splitwise.confirm` |

`splitwise.js` stays in use for these parts: icons (`hydrate`), `forms` painting helpers,
`confirm`, `toast`, `copy`, `appearance`, menus and the `[data-close]` dialog handlers.

## 3. Page shell and pages

### 3.1 Master template

`app/templates/base.html` holds the page shell of the design pages. Each page extends it and fills
the blocks. The shell has these parts, in this order:

1. `<head>`: meta tags, `<title>` from block `title`, the stylesheet, `splitwise.js` without `defer`, then `htmx.min.js` and `app.js` with `defer`.
2. `<body hx-boost="true" data-user-id="…">`. The attribute `data-user-id` carries the user that the server used.
3. The no-JavaScript banner `.noscript-banner`.
4. The skip link `a.skip` that targets `#main`.
5. The `topbar` macro, in `<header class="topbar" id="topbar">`.
6. `<main id="main">` with the class from block `main_class`.
7. The block `after_main`, after `</main>`. The group page puts the `actionbar` there.
8. The flash carrier `<div id="flash" hidden>`.
9. The dialog host `<div id="dialog-host">`. Block `dialogs` fills it.

```html
<body hx-boost="true" data-user-id="{{ user.id if user }}">
  <noscript><p class="noscript-banner">Splitwise Lite needs JavaScript. Turn it on in your browser.</p></noscript>
  {% if shell != "bare" %}
    <a class="skip" href="#main">Skip to content</a>
    {% block topbar %}{{ topbar(user, group=group, group_count=group_count) }}{% endblock %}
  {% endif %}
  <main class="{% block main_class %}home{% endblock %}" id="main">{% block main %}{% endblock %}</main>
  {% block after_main %}{% endblock %}
  <div id="flash" data-message="{{ flash or '' }}" hidden></div>
  <div id="dialog-host">{% block dialogs %}{% endblock %}</div>
</body>
```

The login page sets `shell` to `bare`. It has no topbar and no skip link, as in the design.

The `<title>` has the form `<page> — Splitwise`. HTMX copies the new title after a boosted
navigation, so each page sets block `title`.

### 3.2 Pages

| Design page | Template | Route | Main regions |
|---|---|---|---|
| `login.html` | `pages/login.html` | `GET /login` | `form#loginForm.login-card`, appearance selector |
| `index.html` | `pages/groups_home.html` | `GET /` | `#group-list-region`, `#join-region`, new group dialog |
| `group.html` | `pages/group.html` | `GET /groups/{id}` | `#members-region`, `#expenses-region`, action bar |

A page template holds the layout and calls macros. Each region that HTMX reloads lives in a
template under `partials/<feature>/`, and the page includes it. The page and the fragment route
render the same file, so the markup has one source.

## 4. Component macros

Each storybook component has one Jinja macro. A macro file groups the components of one kind.
A macro takes values and returns the markup of the storybook. A macro adds no CSS class that the
storybook does not show.

| Storybook section | Macro (file) | CSS classes | Used by |
|---|---|---|---|
| Icons | `icon(name, label)` (`icons.html`) | `[data-icon]` | all pages |
| Buttons | `button(label, kind, size, icon_name, type, attrs)`, `icon_button(icon_name, label, attrs)` (`buttons.html`) | `.btn`, `.icon-btn`, `.link-btn` | all pages |
| Text fields | `field(key, label, error, hint, hidden)` with a call block (`forms.html`) | `.field`, `.od-field`, `.input`, `.hint`, `.err` | login, home, group dialogs |
| Money field | `money_field(key, label, symbol, value, error, placeholder)` (`forms.html`) | `.money`, `.cur-sym`, `.input` | expense and payment dialogs |
| Select | `select_field(key, label, options, value, error, hint)` (`forms.html`) | `select.input` | login, dialogs |
| Check tiles | `check_tiles(name, label, members, checked, shares, currency, hint, all_selected, error, attrs)` (`forms.html`) | `.checks`, `.check`, `.share` | expense dialog |
| Segmented control | `segmented(name, options, value, legend, id)` (`forms.html`) | `.segmented`, `.menu-group` | home filter, expense filter |
| Form validation | `err_summary(errors)` (`feedback.html`) | `.err-summary`, `[aria-invalid]` | all forms |
| Chips | `chip(text, hot, cls)` (`data.html`) | `.chip`, `.hot` | topbar, member rows |
| Avatars | `avatar(name, index, size)` (`data.html`) | `.avatar`, `--h` | topbar, member rows |
| Balance amounts | `balance_amount(minor, currency)` (`money.html`) | `.amt`, `.num.pos`, `.num.neg`, `.num.muted`, `.amt-label` | group rows, member rows |
| Stats | `stat(value, caption)` (`money.html`) | `.stats`, `.od-stat`, `.stat-num`, `.stat-cap` | balances card |
| Cards and balance rows | `member_row(row, group)`, `group_row(group)` (`rows.html`) | `.card`, `.rows`, `.row-btn`, `.row-title`, `.row-meta` | group page, home |
| Transaction rows and types | `tx_row(row, group)` for an expense and a payment, `day_group(day, group)` (`rows.html`) | `.row-btn`, `.kind-icon`, `.pay`, `.day-group`, `.day` | expense list |
| Transaction type tags | `tag(kind)` (`data.html`) | `.tag.payment`, `.tag.internal` | expense list |
| Empty state | `empty_state(title, text, icon_name, tag)` with an optional call block for the action (`feedback.html`) | `.empty`, `.kind-icon` | home, group |
| Settled badge | `settled_badge(text)` (`feedback.html`) | `.settled` | balances card |
| Dialog | `dialog(id, title_id, strict)` with a call block, and `dlg_head(title_id, title)` (`overlays.html`) | `.dlg`, `.dlg-head`, `.dlg-body`, `.dlg-foot`, `[data-close]` | all dialogs |
| Invite code | `code_box(code)` (`data.html`) | `.code-box` | invite dialog |
| Top bar | `topbar(user, group, group_count, oob)` (`navigation.html`) | `.topbar`, `.brand`, `.breadcrumb`, `.user-menu`, `.menu-pop` | all pages except login |
| Action bar | `actionbar(group)` (`navigation.html`) | `.actionbar`, `.mobile-only` | group page |

These storybook sections have no macro:

- Foundations (tokens, typography, spacing, motion, layout primitives) are CSS only. Templates use the classes.
- Confirm is a script component. The trigger carries `data-confirm-*` attributes.
- Toast is a script component. A server event shows it.
- Menu is part of `topbar`. Appearance selector is a mount point `<div data-appearance>`. `splitwise.js` fills it.
- Group list, Login card and App pages are page layouts, not components.
- Balance breakdown (`.lines`, `.total-line`) is markup in `partials/members/detail_dialog.html`.
- Settle-up plan (`.plan`, `.arrow`) has no markup in the app. The feature is not built (F2).

A macro that shows a stored value escapes it. Jinja autoescape stays on. Never use `|safe` on
user text.

```jinja
{% macro money_field(key, label, symbol, value="", error="") %}
<div class="field od-field" data-k="{{ key }}">
  <label for="f-{{ key }}">{{ label }}</label>
  <div class="money"><span class="cur-sym">{{ symbol }}</span>
    <input class="input" id="f-{{ key }}" name="{{ key }}" inputmode="decimal"
           value="{{ value }}" {% if error %}aria-invalid="true"{% endif %}
           aria-describedby="f-{{ key }}-err"></div>
  <p class="err" id="f-{{ key }}-err">{{ error }}</p>
</div>
{% endmacro %}
```

## 5. HTMX model

### 5.1 Navigation

`<body hx-boost="true">` sends each link and each form through HTMX. HTMX swaps the `<body>`
content and pushes the URL. The scripts in `<head>` do not run again. A boosted request carries
the sign-in header that `app.js` adds. A link that must leave the app, for example a file
download, has `hx-boost="false"`.

### 5.2 Regions and targets

A region is a part of a page that the server can render alone. Each region has a fixed `id`. The
id is the target of every request that updates the region.

| Region | Id | Fragment URL | Swap |
|---|---|---|---|
| Group list on home | `#group-list-region` | `GET /groups/list` | `outerHTML` |
| Members and balances | `#members-region` | `GET /groups/{id}/members` | `outerHTML` |
| Expense and payment list | `#expenses-region` | `GET /groups/{id}/transactions` | `outerHTML` |
| Dialog host | `#dialog-host` | `GET` of a dialog URL | `innerHTML` |

Search and filter controls use `hx-get` with `hx-target` on their region. The search field uses
`hx-trigger="input changed delay:250ms"`. The segmented filters use `change`. Both controls use
`hx-push-url="false"`, because filter state is not part of the URL.

### 5.3 Dialogs

The design uses native `<dialog>` elements. The app loads each dialog as a fragment into
`#dialog-host`.

1. A button has `hx-get="<dialog URL>"`, `hx-target="#dialog-host"` and `hx-swap="innerHTML"`.
2. The server returns one `dialog` macro with its form.
3. After the swap, `app.js` finds the `dialog` in the host and calls `showModal()`.
4. `splitwise.js` closes the dialog on `[data-close]` and on a click on the backdrop.
5. On the `close` event, `app.js` empties the host.

The form inside a dialog has `hx-post`, `hx-target="this"` and
`hx-swap="outerHTML"`. A dialog with unsaved input stays open on an error. A dialog that records a
risky action, such as a delete, sets `data-strict`, so a click on the backdrop does not close it.

### 5.4 Mutation response

A successful mutation returns status 200 with these parts:

- `HX-Reswap: none`, so the dialog form is not replaced.
- An empty body. The mutations of expenses, payments and members use this form.
- The header `HX-Trigger` with the events of section 5.5.
- Optional out-of-band fragments for a region that the mutation changes, each with `hx-swap-oob="true"`. A region that the response carries has no listener for the event, so it does not load twice. The group settings answer uses this form for the topbar.

```text
HX-Reswap: none
HX-Trigger: {"toast": {"message": "Expense added"}, "close-dialog": {}, "ledger-changed": {}}
```

Each region on the group page listens for `ledger-changed` and reloads itself:
`hx-trigger="ledger-changed from:body"`. The members region and the transaction region reload at
the same time. The balances and the list can differ for a short time between the two reads.

### 5.5 Events

`core/htmx.py` builds the `HX-Trigger` value. Each event name is kebab case.

| Event | Detail | Listener | Effect |
|---|---|---|---|
| `ledger-changed` | none | Regions with `hx-trigger` | The region reloads. Sent after each change of an expense or a payment |
| `members-changed` | none | Regions with `hx-trigger` | The region reloads. Sent after a member is added or removed |
| `toast` | `message` | `app.js` | Calls `Splitwise.toast(message)` |
| `close-dialog` | none | `app.js` | Closes the open dialog in the host |
| `session-start` | `token`, `user_id` | `app.js` | Stores the token of the new user in `sessionStorage`. Only the sign-in sends it |

A redirect loses the `HX-Trigger` header. After a redirect, the server sets a flash cookie with `flash` from `core/htmx.py`. The
route renders the next page with `render` from `core/templating.py`. It puts the cookie text into `#flash` and ends the cookie. `app.js` shows the toast.

A boosted swap replaces the content of `<body>`, so it can detach the toast element. `Splitwise.toast` makes the element again if it is not in the page. The listeners for `HX-Trigger` events are on `document`, because a swap of `<body>` does not remove them.

### 5.6 Errors

A validation error returns status 422 with the form fragment, rendered again with `err-summary`,
the field errors and the user input. HTMX does not swap a 4xx response by default. `app.js`
listens to `htmx:beforeSwap` and sets `shouldSwap` to true and `isError` to false for each response with status 422.

After a 422 swap, `app.js` focuses `.err-summary` if the summary is visible. Otherwise it focuses
the first `[aria-invalid="true"]` field. This matches `Splitwise.forms.bind` in the design.

For another error, `app.js` listens to `htmx:responseError` and `htmx:sendError`. If the response
has no `HX-Trigger` header, it shows the toast `Something went wrong. Try again.` The page keeps its state.

### 5.7 Loading state

- The design CSS shows a spinner on `.btn[aria-busy="true"]`. `app.js` does not set this attribute.
- A form has `hx-disabled-elt="find button[type=submit]"`, so a double click sends one request.
- A region reload shows no indicator. The design has no style for it. To add one, change the design first.

### 5.8 Behaviour after a swap

`splitwise.js` binds its behaviour at `DOMContentLoaded`. A swapped fragment loads later. `app.js`
registers one function with `htmx.onLoad`. HTMX calls it for the first page load and for each
swapped element. The function does these steps on the element it receives:

1. `Splitwise.hydrate(el)` replaces each `[data-icon]` placeholder.
2. It mounts the appearance selector in each `[data-appearance]` that has no selector yet.
3. It reads `#flash`, shows the toast if `data-message` is not empty, and then empties `data-message`.
4. It shows or hides the name field of each form with `data-new-user`, based on the selected option.
5. It focuses the first control of `#loginForm` if the form has no invalid field.
6. It opens each `dialog` without `open` that is a child of `#dialog-host`, and focuses the `[data-autofocus]` element in it.

The menu and dialog handlers of `splitwise.js` are delegated on `document`, so they need no
re-binding. The `icon` macro prints `<span data-icon>`, and step 1 fills it.

## 6. Accessibility rules

The templates keep each accessibility rule of the design. The rules are in
[`design-guidelines.md`](./design-guidelines.md) §10. The app prints the balance labels "is owed",
"owes" and "settled", with a sign (`+60.00 EUR`, `−30.00 EUR`). The design writes other words for
the labels. See [`design-guidelines.md`](./design-guidelines.md) §8.7.

## 7. Words in the app

The design uses two words that the glossary reserves for other things. The app uses the glossary
words in every label, message and template variable.

| Design label | App label (glossary term) |
|---|---|
| "payment", "Add payment" | expense, "Add expense" |
| "Internal transfer", "Internal" | payment, "Record payment", tag "Payment" |
| "Settle up" (plan) | settlement plan (F2, not built) |
| "Date" (bare) | expense date, payment date |
| "From", "To" | sender, receiver |

The CSS class names `.tag.payment` and `.tag.internal` stay as the design defines them. They are
identifiers, not labels. The macro `tag(kind)` maps `expense` to `.tag.payment` and `payment` to
`.tag.internal` and prints the glossary word as text. A rename of these classes starts in the
design.

## 8. Rationale

**Server-rendered fragments, not a single-page app.** The app has few screens and one data
store. The server owns the rules for money and balances. A single-page app would copy these
rules to the browser and add a build step, a client state store and a second validation layer.
With HTMX, one template renders a region for the first load and for each update. A developer
reads the HTML and the route to understand a screen.

**The design CSS is the single source.** One stylesheet that a designer and the app both use
cannot drift. A copy with local changes would make the storybook a false reference. The sync task
makes the rule cheap to follow.

**Out-of-band swaps for ledger changes.** A balance and the list that causes it come from one read,
so they never show two states of the data. The event `ledger-changed` covers the regions that the
response does not carry.

**Server-side validation only.** One validator gives one set of messages. The 422 response gives
the same result as the client check of the prototype, and a test can check it with no browser.

## Related docs

- [`architecture.md`](./architecture.md): layers, request flow and the sign-in model
- [`design-guidelines.md`](./design-guidelines.md): how to read `_design/` and the visual rules
- [`guide-navigation.md`](./guide-navigation.md): procedures for pages, fragments, dialogs and macros
- [`guide-authentication.md`](./guide-authentication.md): the sign-in header and the user in a tab
- [`project-structure.md`](./project-structure.md): where each file lives
- [`../product/glossary.md`](../product/glossary.md): the terms of every label
