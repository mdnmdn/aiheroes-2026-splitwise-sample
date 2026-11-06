---
id: tech-design-guidelines
title: Design guidelines and how to read the design
kind: tech
status: current
summary: How to open and read the files in `_design/`, and the visual and interaction rules of the design. Tokens, themes, type, spacing, motion, icons, layout, component usage, responsive behaviour, accessibility and microcopy.
read_when: you read the design, style a page or a component, or choose a component, a token or a message for a screen
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [_design/site/storybook.html, _design/site/assets/splitwise.css, _design/site/assets/splitwise.js]
depends_on: [tech-design-system]
review_cycle: quarterly
---

# Design guidelines and how to read the design

`_design/site/` holds a static prototype: four HTML pages, one stylesheet and two scripts. The
storybook is the catalogue of components. This document tells you how to read these files and which
visual rules the design sets. It states each rule once. For the app, [`design-system.md`](./design-system.md)
owns how the design becomes templates, the component macros, the HTMX patterns and the design sync.

The CSS holds every value. This document names tokens and classes. Read the value in
`splitwise.css`, section 2 (tokens). Never copy a value into a template.

## 1. How to read `_design/`

### 1.1 Files

| File | What it is |
|---|---|
| `site/storybook.html` | The catalogue. Each component is live, with its states, its markup and its class list |
| `site/index.html` | Page layout: the list of groups, search, filter, join by invite code, new group dialog |
| `site/group.html` | Page layout: members and balances, transaction list, action bar and all group dialogs |
| `site/login.html` | Page layout: the sign-in card |
| `site/assets/splitwise.css` | The only stylesheet: tokens, themes, accents, every component class |
| `site/assets/splitwise.js` | Script `window.Splitwise`: icons, appearance, toast, confirm, forms, money, balance, avatar |
| `site/assets/splitwise-app.js` | Prototype only: script `window.SplitwiseApp` with the fake data store |

### 1.2 Open the files

- A browser opens each HTML file directly from disk. No server and no build step are needed.
- The scripts MUST load. The pages show a banner if `assets/splitwise.js` or `assets/splitwise-app.js` is missing.
- A preview with scripts turned off shows no icons, no theme picker and no working buttons. Open the file in a browser.
- Open `storybook.html` first. Use its side list to jump to a section.
- Use the theme picker (palette button in the top bar) to see each component in light, dark and each accent. Check each new style in both themes.
- The picker saves the choice in browser storage. All pages and all open tabs share it.

### 1.3 Storybook order

The side list groups the sections. The order below is the order on the page.

| Group | Sections, in order | What each shows |
|---|---|---|
| Foundations | Overview | Page skeleton, the two shared files, `data-icon` and `[data-close]` |
| | Colour | Colour tokens as swatches, with their use |
| | Typography | The six sizes with their tokens |
| | Spacing and radius | The spacing steps and the radii |
| | Motion | Durations and the enter and exit demo |
| | Icons | Every icon name, and how to place one |
| | Layout primitives | `od-*` helpers with a live example |
| Controls | Buttons | Variants, sizes, disabled, loading, icon button, link button |
| | Text fields | Field, label, hint, error |
| | Money field | Amount input with the currency symbol |
| | Select | Native select |
| | Check tiles | Multi-select tiles with a share on the right |
| | Segmented control | Two to four exclusive options |
| | Swatches | Colour choice (accent picker) |
| Data display | Chips, Avatars | Small tags, initials |
| | Balance amounts, Stats | Signed amount with label, key figures |
| | Cards and balance rows | `.card` and `ul.rows` |
| | Transaction rows and types | Rows under day headers |
| Feedback | Form validation | Error summary and field errors, live |
| Data display | Transaction type tags | The two type tags |
| Patterns | Group list, Invite code | List with search and filter, code box |
| Feedback | Empty state, Settled badge, Toast | The three feedback parts |
| Overlays | Dialog, Confirm, Menu | Native dialog, confirm helper, popover |
| Patterns | Appearance selector, Top bar, App pages and `SplitwiseApp`, Action bar, Login card, Settle-up plan, Balance breakdown | Page chrome and page patterns |

Each section has the same parts: a kicker, a title, a lead sentence that states the rule, a live
example, a snippet or a class list. The lead sentence is the rule of the component.

### 1.4 Find a component

1. Open the page that you build. The comment at the top of the page names the components it uses, with a storybook group. For example, `group.html` lists Stats, Balance rows, Dialogs and Settle-up plan.
2. Open the section of that name in the storybook. Its class list gives the class names and `data-*` attributes.
3. Open `splitwise.css`. Each component has a comment above its rules that states the markup shape, for example `.field.od-field[data-k="key"] > label + control + .hint + .err`.
4. For behaviour, read the header comment of `splitwise.js`. It lists the API of `window.Splitwise`.

The CSS sections are numbered: 0 fonts, 1 layout primitives, 2 tokens, 3 base, 4 controls, 5 data
display, 6 feedback, 7 overlays, 8 app chrome and patterns.

Attributes that carry behaviour:

| Attribute | Meaning |
|---|---|
| `data-icon="name"` | Placeholder that `Splitwise.hydrate` replaces with an SVG icon. `data-label` adds an accessible name |
| `data-k="key"` | Marks a `.field`. The key links the field to its error in `Splitwise.forms` |
| `data-goto="key"` | A link in `.err-summary` that focuses the field with that key |
| `data-close` | A button in a `<dialog>` that closes it |
| `data-strict` | A dialog that a click on the backdrop does not close |
| `data-appearance` | Mount point of the appearance selector |
| `data-theme`, `data-accent` | Set on `<html>` by `splitwise.js`. They select the colour set |
| `aria-busy="true"` | A button in the loading state |
| `aria-invalid="true"` | An invalid input |

The API of `window.Splitwise`:

| Call | Use |
|---|---|
| `icon(name, label)`, `hydrate(root)`, `icons` | Icon markup, replace placeholders, list of icon names |
| `appearance.get()`, `.set(patch)`, `.mount(el, opts)` | Read, save and apply theme and accent. Draw the selector |
| `toast(message)`, `copy(text)` | Show a toast. Copy to the clipboard with a toast |
| `confirm({title, body, ok})` | Returns a promise. `true` on confirm, `false` on cancel or Esc |
| `forms.bind`, `.paint`, `.reset`, `.focusField` | Validation display, summary, focus |
| `money.decimals`, `.fmt`, `.fmtSigned`, `.symbol`, `.parse`, `.toInput` | Money in minor units |
| `balance.html`, `.label`, `.cls` | The balance amount stack: signed amount, label, colour class |
| `avatar(name, index, size)` | Avatar markup |

The event `splitwise:appearance` fires on `document` after each change of theme or accent.

### 1.5 Prototype only: do not copy as behaviour

`splitwise-app.js` and the page scripts in the three pages are a mock. They show how a screen
behaves, not how the app works.

| Part | Rule |
|---|---|
| Fake data store: `SplitwiseApp.state`, `save`, seed data in browser storage under `splitwise.v2` | Never copy. The server owns data. The browser holds no ledger |
| `requireUser`, `signIn`, `signOut`, `flash`, `takeFlash` | Never copy. The sign-in is a mock with no redirect |
| Money engine: `shares`, `balances`, `settlePlan` | Never copy. The server computes money |
| Validation rules in the page scripts | Read for the messages and the cases. The server owns the rules |
| The sample user and the sample groups | Test data of the prototype only |
| Markup that page scripts build with strings | Read for the markup shape. The app renders it with templates |

The prototype helpers table of `design-system.md` maps each helper to its replacement in the app.

### 1.6 The vocabulary trap

The design uses the word "payment" for an expense and "internal transfer" for a payment. The
glossary reserves "payment" for a recorded transfer between two members. The app uses the glossary
terms in every label, message and variable. The section "Words in the app" of
[`design-system.md`](./design-system.md) has the mapping table. The open decision is in [`../backlog.md`](../backlog.md). The class names
`.tag.payment` and `.tag.internal`, the ids `payDlg` and `intDlg` and the data field `type:'payment'`
are design identifiers. Do not read them as product terms. See the [glossary](../product/glossary.md).

When you copy a message from the design, check it against the glossary first.

## 2. Colour

Use a token. Never write a hex value.

| Token | Use |
|---|---|
| `--bg`, `--surface`, `--surface-2`, `--hover` | Page ground, card and dialog, subtle fill, hover fill |
| `--border`, `--border-strong` | Hairline between rows and cards, border of a control |
| `--text`, `--muted`, `--subtle` | Primary text, secondary text, tertiary label |
| `--accent`, `--accent-hover`, `--accent-fg`, `--accent-soft` | Primary button, focus ring, link, selection. Text on an accent fill. Selected background |
| `--accent-2`, `--accent-2-fg`, `--accent-2-soft`, `--accent-2-ink` | Orange highlight: brand mark, payment icon, `.chip.hot`, code box |
| `--pos`, `--neg` | Money only: a positive and a negative amount |
| `--danger`, `--danger-soft` | Error text, error border, destructive action, error summary background |
| `--shadow`, `--scrim` | Elevation of a popover and a dialog. Backdrop of a dialog |

Rules:

- Use `--accent-2` only as a fill with `--accent-2-fg` text. For orange text, use `--accent-2-ink`.
- Use `--pos` and `--neg` for money only. An accent never replaces them. They do not change with the accent.
- Use `.pos`, `.neg`, `.muted` for amount colour, always with a sign and a label.
- Never use colour as the only carrier of a meaning.
- The values of light and dark are chosen apart. Both give 4.5:1 text contrast. Do not derive one from the other.

### 2.1 Themes and accents

| Setting | Values | Where it is set |
|---|---|---|
| Theme | `light`, `dark`, `system` (the default) | `data-theme` on `<html>`. `system` follows the browser. The attribute shows the resolved value |
| Accent | `pop` (the default, purple with orange), `teal`, `blue`, `green`, `violet`, `orange`, `rose` | `data-accent` on `<html>` |

Each accent has its own light and dark set of `--accent`, `--accent-hover`, `--accent-fg` and
`--accent-soft`. The orange `--accent-2` stays the same in every accent. `splitwise.js` saves the
choice in browser storage under `splitwise.theme` and `splitwise.accent`, and sets both attributes
before first paint. For this reason it loads in `<head>` without `defer`.

A new component MUST look correct in both themes and in all seven accents.

## 3. Typography

| Token | Use |
|---|---|
| `--font` | All interface text. The family is Geist, with the system font as fallback |
| `--mono` | Every amount and every code. The family is Geist Mono |
| `--fs-2xl` | A large balance figure (`.big-num`) |
| `--fs-xl` | Page title, dialog title on a page card (`h1`) |
| `--fs-lg` | Dialog title, section heading |
| `--fs-md` | Body text, input text, row title. The body line height is 1.5 |
| `--fs-sm` | Button label, field label, hint, error, meta line |
| `--fs-xs` | Caption, chip, day header, balance label |

Rules:

- Put each amount in `.num`. It sets the mono family and tabular figures, so columns line up.
- Keep an amount and its currency on one line: `.od-nowrap`.
- The uppercase labels (`.day`, `.panel-head h2`, `.menu-group legend`) are `--fs-xs` or `--fs-sm` with letter spacing. Do not use uppercase for anything else.
- An input has `--fs-md` text, so a phone browser does not zoom.

## 4. Spacing, radius and elevation

| Scale | Tokens | Use |
|---|---|---|
| Spacing | `--s1` to `--s8` | Every gap and padding. A 4 and 8 rhythm |
| Radius (read the values in the CSS, not in the storybook captions) | `--r-sm` | Controls and small parts |
| | `--r-md` | Cards |
| | `--r-lg` | Dialogs |
| | `--r-full` | Avatars, pills, swatches |
| Elevation | `--shadow` | Popover and dialog only |

Rules:

- A card has a hairline border and no shadow. `.card` is the only container surface.
- Never write a pixel value for a gap or a radius in a template. Use the token.
- Layout heights use `--bar-h` (action bar) and `--topbar-h` (sticky offset).

## 5. Motion

| Token | Use |
|---|---|
| `--t-fast` | Hover, exit, small state feedback, menu entry |
| `--t-med` | Dialog, toast and menu entering |
| `--ease-out` | Enter |
| `--ease-in` | Exit |

Rules:

- Motion only explains a change of state.
- Enter with `--t-med` and `--ease-out`. Exit faster, with `--t-fast` and `--ease-in`.
- Animate `transform` and `opacity` only.
- Under `prefers-reduced-motion: reduce`, the stylesheet turns off every animation and transition. Never override it.
- Pointer-only styles (hover) live in `@media (hover: hover)`.

## 6. Icons

One outline family: a 24 px grid, a 1.5 stroke and round caps. The class is `svg.i`. An icon sits
next to text. Use `<span data-icon="name"></span>` in markup and `Splitwise.icon(name)` in script.

| Names | Use |
|---|---|
| `logo` | Brand mark |
| `plus`, `close`, `check` | Add, close a dialog, success |
| `receipt` | An expense row (a "payment" in the design) |
| `pay`, `arrow` | A payment row (an "internal transfer" in the design). Sender to receiver |
| `sun`, `moon`, `palette` | Theme toggle, appearance menu |
| `user`, `users`, `logout` | Current user, members, sign out |
| `edit`, `trash`, `copy` | Edit, delete, copy the invite code |
| `search`, `info` | Search field, help |

Rules:

- An icon is decorative by default and has `aria-hidden`. An icon that stands alone and has a meaning gets a label: `data-label` or `Splitwise.icon(name, label)`.
- An icon-only button needs an `aria-label`.
- Do not add an icon outside this list. Add it to `splitwise.js` and to the storybook first.

## 7. Layout primitives

Use these classes before you write a flex or grid rule. They live in `@layer od-layout`, so
product CSS wins over them.

| Class | Use |
|---|---|
| `.od-stack`, `.od-row`, `.od-row-top`, `.od-cluster` | Column, centred row, top-aligned row, wrapping row. The gap is `--od-gap` |
| `.od-fill`, `.od-fixed` | A child that takes the free space. A child that never shrinks |
| `.od-grid` | Equal columns. The count is `--od-cols` |
| `.od-stat`, `.od-field`, `.od-cell` | Stacked blocks: numeral over caption, label over control |
| `.od-truncate`, `.od-clamp-2`, `.od-clamp-3` | One-line ellipsis. A clamp at two or three lines |
| `.od-nowrap`, `.od-keep` | Keep an amount and its currency together. Keep a word whole |
| `.od-tile`, `.od-media` | Header over body. A responsive image with `--od-ratio` |
| `.od-screen`, `.od-scroll`, `.od-rail` | Full-height shell, scroll area, horizontal rail |
| `.od-spacer`, `.od-touch` | An invisible placeholder. A 44 px touch area |

Rules:

- A name or a description MAY truncate. An amount and a button NEVER truncate.
- An `.od-stat` holds two block children, never two sibling spans.
- Page classes: `.layout` (group page), `.home` (home page), `.login` (sign-in page), `.panel-head`, `.actionbar`, `.sticky-side`.

## 8. Components: usage rules

### 8.1 Buttons

| Variant | Use |
|---|---|
| `.btn.primary` | The main action of a screen or a dialog. One per screen |
| `.btn.secondary` | An alternative action |
| `.btn.ghost` | A low-emphasis action, for example Cancel |
| `.btn.danger` | A destructive action. Always behind a confirm dialog |
| `.btn.sm` | A compact button inside a card |
| `.btn.block` | A full-width button in the login card and in sheets |
| `.icon-btn` | An icon-only action. 44 px. Has `aria-label` |
| `.icon-btn.outline` | An icon button that lines up with an `.input` |
| `.link-btn` | A text action inside a form, for example Select all |

- Set `aria-busy="true"` on a button while its request runs. It shows a spinner and blocks clicks.
- Use `disabled` for a button that cannot act. Do not hide the button.
- In a dialog foot, put Cancel (`.btn.ghost` or `.secondary`) before the primary action.

### 8.2 Fields

A field is `.field.od-field[data-k]` with a visible `<label>`, the control, a `.hint` and a `.err`.

- Every control has a visible label. A placeholder is an example, never a label. A hidden label uses `.sr-only`.
- A `.hint` states a rule before the error. A `.err` states the fix after it. An empty `.err` is hidden.
- An invalid control has `aria-invalid="true"` and `aria-describedby` that points to its `.err`.
- The page shows an error after the user leaves the field. After the first submit, it shows all errors.
- Use `.two` for two short fields side by side. It stacks below 400 px.
- Use `.input` on `<input>`, `<select>` and `<textarea>`. Its height is 44 px.

### 8.3 Error summary

- Show `.err-summary` at the top of the form if two or more fields fail. It has `tabindex="-1"`.
- Its heading names the number: "Fix 3 fields to continue:". Each item is a link with `data-goto` that focuses the field.
- On submit, focus the summary if two or more fields fail. If one field fails, focus that field.
- An error never moves to a toast. A toast is for success only.

### 8.4 Money field

- Use `.money` with `.cur-sym` and an `.input`. The symbol is display only. The stored value is the currency code.
- The user types text. The script parses it into minor units. Never use a float for money.
- The placeholder shows the form of the number for the currency, for example `0.00` for `EUR`.
- Accept a comma or a dot as the decimal mark. Reject other characters with a message.

### 8.5 Choice controls

| Control | Use when |
|---|---|
| `select.input` | The choice has more than four options, or the options are people, currencies or users |
| `.segmented` | Two to four exclusive options that the user switches often: filters, theme |
| `.checks` with `.check` | Several options of people. The whole tile is the touch target. The share shows on the right |
| `.swatches` | A colour choice. Each swatch has a hidden text name |

- `.segmented` uses real radio buttons, so the arrow keys work. Its `<fieldset>` has a `<legend>`, visible or `.sr-only`.
- A `.check` selection uses `--accent` and `--accent-soft`. Add a "Select all" and "Clear all" `.link-btn` above a long list.

### 8.6 Data display

| Part | Rule |
|---|---|
| `.chip` | A short tag of one or two words: a currency code, "You". Not interactive. `.chip.hot` is the orange highlight |
| `.avatar` | Initial on a tinted circle. The hue is `--h` and follows join order. Decorative. The name is always next to it |
| `.card` | The one container surface. A list inside is `ul.rows` with `li > .row-btn` |
| `.row-btn` | Lead, then `.od-fill` text (`.row-title`, `.row-meta`), then a trailing `.amt`. A row that navigates is an `a.row-btn`. Minimum height is 60 px |
| `.kind-icon` | The square lead of a transaction row. `.pay` is the variant for the second type |
| `.day`, `.day-group` | A date header over its rows. Newest first |
| `.stats`, `.od-stat` | Key figures at the top of a card: numeral over caption |
| `.tag.payment`, `.tag.internal` | The transaction type, always as text |
| `.code-box` | The invite code, big, in mono. Pair it with a Copy button |
| `.lines`, `.total-line` | A divided list in a dialog that ends in a total line, so each number has an explanation |
| `.plan`, `.arrow` | A settlement plan row: sender, arrow, receiver, amount on its own line. The app does not use it until F2 |

### 8.7 Balance amount

- A balance is `.amt.od-stat` with `.num` and `.amt-label`. `Splitwise.balance.html` builds it.
- The sign is a real plus or minus (`+60.00 EUR`, `−30.00 EUR`). Zero has no sign.
- The label gives the meaning: the design writes "gets back", "owes" and "settled up". The app writes "is owed", "owes" and "settled". The open decision is in [`../backlog.md`](../backlog.md).
- The colour class is `.pos`, `.neg` or `.muted`. Colour never carries the meaning alone.
- The amount stays on one line (`.od-nowrap`) and is right-aligned.

### 8.8 Dialogs and confirm

- Use a native `<dialog>` with `.dlg > .dlg-head + .dlg-body + .dlg-foot`. The head holds the title `h2` and a close `.icon-btn[data-close]`.
- Give the dialog `aria-labelledby` that points to its title. Open it with `showModal()`.
- A dialog closes with Esc, a click on the backdrop and each `[data-close]` button. Set `data-strict` to ignore the backdrop.
- Below 560 px, a dialog is a bottom sheet.
- The body scrolls. The head and the foot stay fixed.
- A destructive action needs `Splitwise.confirm`. Its title is a question. Its body says what the user loses and what happens next. Its `ok` label names the action, for example "Delete payment".
- A confirm dialog is strict. Focus starts on Cancel. Esc cancels.

### 8.9 Toast

- Use a toast for a short confirmation after an action succeeds, for example "Name updated".
- It has `role="status"`. It hides after about three seconds.
- A toast never carries an error that the user must act on. Show that error next to its field.

### 8.10 Empty state

- Use `.empty` with a `.kind-icon`, a title (`h3`) and one sentence.
- Say why the area is empty and what to do next. Add the action button of that next step.
- A list with no match shows `li.empty` inside the list, with a "Clear filters" button.
- Never show a blank card.

### 8.11 Settled badge and other parts

- `.settled` is a check icon plus text in `--pos`. Show it when every balance is zero.
- A menu is `<details class="menu">` with `.menu-pop`. It works without a script. The script closes it on an outside click and on Esc, and returns focus to the trigger.
- Use `Splitwise.copy` for the invite code. It shows a toast and, if the browser blocks the clipboard, a hint.
- A count under a filtered list has `role="status"`, so a screen reader announces it.

## 9. Responsive behaviour

Design for a phone first. The base styles fit a narrow screen. Media queries add the wide layout.

| Breakpoint | Change |
|---|---|
| Under 400 px | `.two` and `.checks` use one column |
| Under 480 px | `.brand-name` is hidden |
| Under 560 px | A dialog is a bottom sheet. `.user-name` and `.appearance-label` are hidden |
| Under 900 px | `.desktop-only` is hidden. `.actionbar` is a fixed bar at the bottom, and `.layout` reserves its height with `--bar-h` |
| From 900 px | `.layout` has a 340 px side panel and a main column. `.mobile-only` is hidden. The toast moves to the bottom corner |

- Page width limits: `.layout` and `.topbar-in` 1120 px, `.home` 520 px, `.login-card` 400 px, dialog 520 px.
- Mark an element for one size with `.mobile-only` or `.desktop-only`. Do not write a new media query for it.
- Respect `env(safe-area-inset-bottom)` in a fixed bottom part.
- Put the main actions in the action bar on a phone, within thumb reach.

## 10. Accessibility rules

The design is accessible. Each template keeps these rules.

- The page has a skip link `a.skip` to `#main`. The sign-in page has none.
- Each field has a `<label for>`. A hidden label uses `.sr-only`.
- An invalid field has `aria-invalid="true"` and `aria-describedby` that points to its `.err`.
- A form with two or more errors shows `.err-summary` with links that focus the fields (`[data-goto]`).
- Every form has `novalidate`. The server validates and gives the messages.
- A counter such as "2 of 5 groups" has `role="status"`.
- An icon is `aria-hidden` unless it has a label. An `icon_button` needs a label.
- A row that opens something has an `aria-label` with the amount and the balance label.
- Colour never carries an amount alone. A balance shows a sign and a label. A tag shows text.
- Touch targets are 44 px. Use the design classes and do not shrink them.
- The focus ring is `:focus-visible` with `--accent`. Never remove it.
- A dialog is a native `<dialog>` with `aria-labelledby`. After it closes, focus returns to the control that opened it.
- A confirm dialog starts with focus on Cancel. Esc cancels.
- A breadcrumb marks the current page with `aria-current="page"`.
- Text contrast is at least 4.5:1 in every theme. Use the text tokens on the surface tokens as the storybook shows.
- A toast has `role="status"`.
- Reduced motion turns off animation. See section 5.
- If JavaScript is off or a shared script fails, the page shows `.noscript-banner`.

## 11. Microcopy

The design writes in English, in a plain and short style. The rules below describe how the
design writes. Replace the words that the vocabulary trap (section 1.6) lists.

| Part | Rule | Example in the design |
|---|---|---|
| Tone | Plain, direct, no blame. Address the user as "you" | "Choose your name, or add yourself as a new user." |
| Page title | A noun phrase | "Your groups", "Sign in" |
| Button label | A verb and its object. Name the action, not "OK" | "Add payment", "Save expense", "Delete payment" |
| Field label | A short noun. Sentence case | "Description", "Split equally between" |
| Placeholder | An example. Begins with "e.g." for text | "e.g. Groceries at Pingo Doce" |
| Hint | One sentence that states a rule or a format | "Use at most 2 decimals." |
| Required value | "Enter a …" | "Enter an amount.", "Enter a name." |
| Choice error | "Choose …" or "Pick …" | "Choose who paid.", "Pick at least one person to split with." |
| Rule error | State the rule, then the fix | "Keep it under 30 characters." |
| Conflict error | Name the thing, then what to do | "No group uses this code. Check it with the person who invited you." |
| Date error | State the limit | "Date can't be in the future." |
| Error summary | Count, then the list of messages | "Fix 3 fields to continue:" |
| Confirm title | A question that names the object | "Delete this payment?" |
| Confirm body | What is lost, then what follows | "… removed and balances recalculated." |
| Toast | Past tense or a state. No full stop. Short | "Name updated" |
| Empty state | Why it is empty, then the next step | "No transactions yet. Add what someone paid for the group." |
| Balance label | A short phrase with the sign | "gets back", "owes", "settled up" |

- Write an amount with its currency. The design shows the symbol (`€95.40`). The glossary form is the amount with its currency code (`90.00 EUR`). The app follows the glossary.
- Write a date as a short readable date in the interface (`16 Oct 2026`). Store it as ISO 8601.
- The interface strings are English only. The browser locale sets number and date format.
- Never say what the app cannot do. The app records payments. It never moves money.

## Related docs

- [`design-system.md`](./design-system.md): how the design becomes templates, macros and HTMX patterns
- [`guide-navigation.md`](./guide-navigation.md): procedures for pages, fragments, dialogs and macros
- [`../product/glossary.md`](../product/glossary.md): the terms of every label
- [`../backlog.md`](../backlog.md): open design questions
