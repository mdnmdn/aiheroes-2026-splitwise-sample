---
id: tech-guide-navigation
title: "Guide: pages, fragments, dialogs and components"
kind: tech
status: current
summary: Procedures to add a page, an HTMX fragment, a dialog and a component macro. The URL naming rules, the route owners, the redirect rules and the side-by-side check against the design.
read_when: you add or change a page, a fragment, a dialog or a component macro, or you name a URL
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/templates/base.html, app/templates/components/overlays.html, app/templates/components/forms.html, app/core/htmx.py, app/core/session.py, app/static/js/app.js, app/groups/routes.py, app/expenses/routes.py, _tools/design_sync.py, _design/site/storybook.html]
depends_on: [tech-design-system, tech-architecture, prod-glossary]
review_cycle: quarterly
---

# Guide: pages, fragments, dialogs and components

This guide gives the steps to extend the UI. [`design-system.md`](./design-system.md) gives the
model behind the steps: the page shell, the macros and the HTMX rules. Read it once before you
start. [`guide-authentication.md`](./guide-authentication.md) explains how a route gets the user.

## 1. URL naming

- A URL is lowercase. Words are separated by a hyphen. A collection name is a plural noun.
- A page URL names a thing: `/groups/{group_id}`. It has no verb.
- A path parameter is `{<thing>_id}` in code. Its value is an integer.
- A sub-resource nests under its group: `/groups/{group_id}/expenses/{expense_id}`.
- A dialog is a `GET` of the thing plus `/new`, `/{id}/edit` or an action noun, for example `/invite`.
- An HTML endpoint reads with `GET`. Every change is a `POST`, so a boosted form works without a verb trick:
  - create: `POST /<collection>`
  - update: `POST /<collection>/{id}`
  - delete: `POST /<collection>/{id}/delete`
- A form and a button use `hx-post`. No HTML route uses `PUT`, `PATCH` or `DELETE`.
- A confirmation dialog is a `GET` of `/{id}/delete`. Its form does the `POST` to the same URL.
- The JSON API lives under `/api/v1`. It can use `GET`, `POST`, `PUT`, `PATCH` and `DELETE`. HTML routes never use that prefix.
- A filter is a query parameter: `?filter=mine`, `?q=ski`. A filter is not a path.

### 1.1 Route owners

Each feature document owns its routes. Its `## Implementation` section lists them. This guide holds
the naming rules only. Do not copy a route table here.

Examples of the rules:

- `GET /groups/{id}/expenses/new` opens a dialog.
- `POST /groups/{id}/expenses/{eid}/delete` deletes an expense.

| Area | Owner |
|---|---|
| Sign-in | [`sign-in.md`](../features/sign-in.md) |
| Groups | [`groups.md`](../features/groups.md) |
| Members | [`members.md`](../features/members.md) |
| Expenses | [`expenses.md`](../features/expenses.md) |
| Payments | [`payments.md`](../features/payments.md) |
| Balances | [`balances.md`](../features/balances.md) |

If a route changes, change the feature document in the same commit.

## 2. Add a page

1. Pick the URL by section 1. Add the route to the `## Implementation` section of the feature document.
2. Create `app/templates/pages/<name>.html`. Start with `{% extends "base.html" %}`.
3. Set block `title` to the page name. The shell adds ` — Splitwise`.
4. Set block `main_class` to `home` for one column or `layout` for the side panel and the list. Fill block `main`.
5. Build the content from macros in `components/`. Add no CSS.
6. Add the route in `app/<feature>/routes.py`. Protect it with `current_user_html`.
7. Pass `user` and, on a group page, `group` to the template. The topbar needs both.
8. Render with `templates.TemplateResponse(request, "pages/<name>.html", context)`.
9. Add an integration test that gets the page as a signed-in user and as no user.

The topbar shows the breadcrumb. A page under a group passes `group`, and the topbar shows the
group name, the currency chip and the settings button. A page with no group shows only "Groups".
A page that must have no topbar sets `shell` to `"bare"` before block `main`, as the login page
does.

```jinja
{% extends "base.html" %}
{% set shell = "app" %}
{% block title %}{{ group.name }}{% endblock %}
{% block main_class %}layout{% endblock %}
{% block main %}
  {% include "partials/members/panel.html" %}
  {% include "partials/balances/transactions.html" %}
{% endblock %}
```

## 3. Add an HTMX fragment

A fragment is one region that the server renders alone. Use it for a list, a panel or a dialog
body that updates without a page load.

1. Create the template `app/templates/partials/<feature>/<name>.html`. It never extends `base.html`.
2. Give its root element a fixed `id` that ends in `-region`.
3. Add the route. The route returns the fragment for a request with `HX-Request`.
4. In `core/htmx.py`, use `is_htmx`. If the request is not HTMX, the route returns the full page that includes the fragment.
5. In the page, include the same partial, so the page and the fragment share one source.
6. On the control that loads or updates the fragment, set `hx-get`, `hx-target="#<id>"` and `hx-swap`. Use `outerHTML` for a region that carries its own `id`.
7. If the region reloads after a change, add `hx-trigger="ledger-changed from:body"` to its root element.
8. If the mutation route can return the region, return it with `hx-swap-oob="true"` and remove the `ledger-changed` listener, so it does not load twice.
9. Add a test that checks the status and the root `id` of the fragment.

The mutation route builds its response with the helpers of `core/htmx.py`. The helpers set
`HX-Reswap`, `HX-Trigger` and the out-of-band parts. A route never writes these headers by hand.

## 4. Add a dialog

1. Create the template `partials/<feature>/<name>_dialog.html`. Use the `dialog` macro from `components/overlays.html`.
2. Give the dialog a fixed `id` and the `id` of its title. The macro sets `aria-labelledby`. Build the head with the macro `dlg_head`.
3. Put the form inside. Give it `novalidate` and `hx-post`, with `hx-target="this"`, `hx-swap="outerHTML"` and `hx-disabled-elt="find button[type=submit]"`.
4. Build each field with the macros of `components/forms.html`. Pass the error text from the context.
5. Put a Cancel button with `data-close` and the primary button in the footer.
6. For a delete button, add `data-confirm-title`, `data-confirm-body` and `data-confirm-ok`. `app.js` shows the confirm dialog before the request.
7. Add the `GET` route for the dialog. It returns the dialog template with default values.
8. Add the mutation route. On success, it returns the response of section 5.4 of `design-system.md` with the event `close-dialog`.
9. On a validation error, the route returns the form fragment again with status 422. The form keeps the user input.
10. Add the opener to the page: `hx-get="<dialog URL>"`, `hx-target="#dialog-host"`, `hx-swap="innerHTML"`.
11. Add tests for the dialog `GET`, for a valid post and for an invalid post that returns 422.

A dialog that holds a risky action sets `data-strict`. A dialog that stays open after a success
does not send `close-dialog`. It returns its own new content.

## 5. Add a component macro

Start from the storybook. The storybook is the reference, so the macro copies it.

1. Find the section in `_design/site/storybook.html`. If the component is missing, add it to the storybook first.
2. Copy the markup of the example into the macro file of its kind in `app/templates/components/`.
3. Replace each fixed text and value with a parameter. Give optional parts a default value.
4. Keep the class names, the attribute names and the order of the elements as in the storybook.
5. Add no CSS class, no `<style>` block and no style attribute. If a style is missing, change `splitwise.css` first and run `mise run design-sync`.
6. Print each value through autoescape. Never use `|safe` on user text.
7. Do not compute money in the macro. Take a formatted string or call the filters `money` and `signed_money`.
8. Add the aria attributes of the storybook. A parameter for an icon button label has no default.
9. Add a row to the macro table in section 4 of `design-system.md`.
10. Use the macro in one template. Compare the result with the storybook, as in section 7.

Name the macro in snake case. Use the glossary term for the thing that it shows: `expense_row`,
not `bill_row`. A macro of an existing kind goes in the file of that kind. Do not create a file
for one macro.

## 6. Redirects

| Case | Use | Why |
|---|---|---|
| A boosted form or link, and the next page is a full page | Status 303 with `Location` | HTMX follows the redirect and swaps the body |
| A request from a dialog form with `hx-target="this"` | Header `HX-Location` from `redirect_to` in `core/htmx.py` | The swap target is the form, so htmx must navigate. `HX-Location` keeps the user header of the tab. `HX-Redirect` loads the page with the cookie user |
| A request that is not HTMX | Status 303 | The browser follows it |
| A route with no user | 303 to `/login?next=<path>` | The dependency does this |

After a redirect, the page shows a message through the flash cookie, because `HX-Trigger` is
lost. Use `flash` from `core/htmx.py`. Use the `toast` event when the page stays.

- Use 303 after a `POST`, never 302. A 303 makes the browser use `GET`.
- The `next` value is a local path. The server rejects a value that does not start with `/` or that starts with `//`.
- After a delete of the open thing, redirect to its parent. When the user leaves a group, redirect to `/`.

## 7. Check a page against the design

Check each new or changed page against its design page.

1. Start the app. Open `_design/site/<page>.html` in one window and the app page in another.
2. Set the same width in both windows. Check 390 px and 1280 px.
3. Set the same theme and accent in both. Check light and dark.
4. Compare the regions in order: topbar, panel head, rows, empty state, dialog.
5. Open each dialog in both and compare the fields, the hints and the buttons.
6. Trigger each error in both. Compare the `err-summary` and the field errors.
7. Tab through the page in both. The focus order and the focus ring must match.
8. Compare the markup. Each class in the design must be in the app, with no extra class.
9. For a difference, decide which side is wrong. If the design is wrong, change the design first. If the template is wrong, fix the template.

Words are the only allowed difference. The app uses glossary terms. Section 7 of
[`design-system.md`](./design-system.md) lists the mapping.

## Related docs

- [`design-system.md`](./design-system.md): the model of the page shell, macros and HTMX
- [`architecture.md`](./architecture.md): layers and the request flow of a page and a fragment
- [`guide-authentication.md`](./guide-authentication.md): protect a route and test as two users
- [`guide-api.md`](./guide-api.md): the JSON endpoints under `/api/v1`
- [`practices.md`](./practices.md): rules for services, tests and errors
- [`../product/glossary.md`](../product/glossary.md): the terms for names and labels
