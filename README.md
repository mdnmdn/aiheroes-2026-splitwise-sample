# Splitwise Lite

A web app in which a group records shared expenses and sees who owes whom.

Stack: Python 3.13, FastAPI, Jinja2 with HTMX, SQLite. The tools come from [mise](https://mise.jdx.dev) and
[uv](https://docs.astral.sh/uv/).

## Install mise

|OS|Install|Activate in the shell|
|---|---|---|
|macOS|`brew install mise` or `curl https://mise.run \| sh`|zsh: `echo 'eval "$(mise activate zsh)"' >> ~/.zshrc`|
|Linux|`curl https://mise.run \| sh`|bash: `echo 'eval "$(mise activate bash)"' >> ~/.bashrc`|
|Windows|`winget install jdx.mise` or `scoop install mise`|PowerShell: add `mise activate pwsh \| Out-String \| Invoke-Expression` to `$PROFILE`|

Open a new shell, then run `mise --version`. In the repository, run `mise trust` once to allow
`mise.toml`. Other methods and shells: [Installing mise](https://mise.jdx.dev/installing-mise.html)
and [Getting started](https://mise.jdx.dev/getting-started.html).

## Quick start

```sh
mise install          # Python and uv
uv sync               # dependencies
cp .env.example .env  # optional: local settings
mise run dev          # http://127.0.0.1:8000, with auto reload
```

On start, the app creates the database `_data/splitwise.db` and applies the pending migrations.

In `dev`, the first start also adds sample data. Sign in as Alice, Bob, Carla or Dan.

Sign-in is simulated: you pick a user or add a new one, with no password. Each browser tab keeps its
own user, so two tabs can act as two members of the same group.

## Tasks

|Command|What it does|
|---|---|
|`mise run dev`|Start the server with auto reload|
|`mise run start`|Start the server without reload|
|`mise run test`|Run the tests|
|`mise run lint` / `mise run fmt`|Check / fix style and formatting|
|`mise run migrate`|Apply pending migrations and exit|
|`mise run db-reset`|Delete the dev database and migrate again|
|`mise run design-sync`|Copy the design CSS and JS into `app/static/`|
|`mise run docs-lint`|Check the documentation|

`mise tasks` lists all of them. [`_docs/infra/dev-environment.md`](_docs/infra/dev-environment.md)
has the settings and details.

## Repository

|Path|Holds|
|---|---|
|`app/`|The application: one package per feature, `core/`, templates, static files, migrations|
|`tests/`|Unit and integration tests|
|`_design/`|The HTML design and the component storybook. Open `_design/site/storybook.html` in a browser|
|`_docs/`|The documentation library. Start at [`_docs/Home.md`](_docs/Home.md)|
|`_tools/`|Support scripts for docs and design sync|
|`_data/`|Local database. Not in git|

## Documentation

- What the product does: [`_docs/product/overview.md`](_docs/product/overview.md)
- The features: [`_docs/features/`](_docs/features/)
- Architecture and code rules: [`_docs/tech/architecture.md`](_docs/tech/architecture.md),
  [`_docs/tech/practices.md`](_docs/tech/practices.md)
- Design: [`_docs/tech/design-guidelines.md`](_docs/tech/design-guidelines.md),
  [`_docs/tech/design-system.md`](_docs/tech/design-system.md)
- Agents (Claude Code and others): [`AGENTS.md`](AGENTS.md)
