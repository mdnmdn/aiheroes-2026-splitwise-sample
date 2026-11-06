---
name: coordinator
description: Work as the coordinator of a multi-step task in Splitwise Lite. Split the task, track it in `_docs/wip/`, delegate each part to a subagent of the correct model tier, require tests, lint and doc updates, and run review agents. Use when a request has several parts (docs + code + plan), when the user says "act as coordinator" or "use subagents", or when a task is too large for one context. Not for a single small edit.
---

# Coordinator

You coordinate. Subagents do the work. You keep the decisions, the plan and the final check.
Your context is the scarce resource: keep conclusions in it, not file dumps.

## 1. Before you delegate

1. Read `AGENTS.md` and `_docs/Home.md`. Find the 2–3 documents the task needs.
2. Explore once, cheaply: `mise run digest --summary <paths>`, then `--headings`. If a source is
   large (a design, a big module), send one agent to write an inventory in
   `_docs/wip/<task>-inventory.md`.
3. If a part of the task is not clear, ask the user before you delegate. Use the question tool of
   the session if it has one. If not, ask in the chat. A guess sends every subagent the wrong way.
4. Make the decisions the human delegated. Write them in the `## Decisions` section of
   `_docs/wip/<task>.md`. Every subagent reads it. A brief prevents five agents from making five
   different choices.
5. Do not decide what the human must decide (product scope, phase, vocabulary conflicts). Write one
   line in `_docs/backlog.md` and continue with the rest.

## 2. Track the work

- For each task that you delegate, write a note `_docs/wip/<task>.md` (`kind: wip`,
  `id: wip-<task>`). It holds the decisions. If the work crosses sessions or has more than 3 steps,
  it also holds the steps, the order, the done criteria and the close procedure. Update it when a
  step closes. Delete it when the task closes.
- Put docs and small text data in `_docs/wip/`: the brief, inventories, reports. Each file is a
  `wip` document with front matter, so `mise run docs-lint` checks it.
- Put spikes and temporary assets in `tmp/<task>/`: prototype code, screenshots, generated files.
  It is not in git.

## 3. Pick the model tier

Give each agent the smallest model that can do its task. Examples of tiers:

|Tier|Examples|Give it|
|---|---|---|
|Large|Opus, Fable, GPT (large)|Architecture choices, hard debugging, a review that must find subtle bugs. Rarely needed: the coordinator usually holds this role|
|Medium|Sonnet, Terra|Write a document, implement a feature slice, reconcile documents, an inventory of a large source, a code review|
|Small|Haiku, Luna|A pure function with tests, a skill or a short doc from a clear outline, mechanical edits, link checks, renames, summaries of a known file|

If a small-tier agent fails twice, give the task to the next tier. Do not retry the same prompt.

## 4. Write the prompt

A subagent has no memory. Each prompt contains:

1. **Goal and scope**: the files it creates or changes. Name what it must **not** touch, mainly the
   files that other running agents own.
2. **Read first**: the brief, the owning docs, the skill to load (`splitwise-fullstack` for code,
   `ste-writing` for docs).
3. **Decisions**: the binding choices, and the conflicts you resolved. Say "the feature doc wins"
   or similar, so the agent does not pick a winner itself.
4. **Rules**: one edit = Edit or Write tool. A batch of edits = a script in `_tools/`, if the
   script is faster or uses fewer tokens than the separate edits. If the task is not clear, ask
   instead of a guess. Do not commit. Do not stash or revert changes it did not make.
5. **Tests**: every rule in a service gets a unit test. Every route gets an integration test.
   Money rules get edge cases.
6. **Done**: `mise run lint`, `mise run test`, `mise run docs-lint` pass. The agent updates the
   docs that its change touched (`_docs/_meta/authoring.md`), in STE.
7. **Report**: files changed, test count, deviations from the docs, choices it made that you did
   not, what the next step must know. Ask for a short report.

## 5. Run agents

- If the user does not specify otherwise, run at most 3 subagents at the same time.
- Run in parallel only when the agents own different files. Shared files (`Home.md`, `AGENTS.md`,
  the glossary, `base.html`) get one owner per wave.
- Run in sequence when a step builds on the output of the step before.
- Similar work goes to one agent, or to parallel agents with the same prompt shape: one agent for
  all feature docs, not six agents with six styles.
- While agents run, do work that does not overlap: write the plan, read a report, prepare the next
  prompt.

## 6. After each agent

1. Read the report. Check its claims that matter: run `mise run test`, `mise run lint`,
   `mise run docs-lint` yourself.
2. Collect its "choices I made". Accept, or correct them in the brief and in the next prompt.
3. Look for conflicts between agents (routes, names, events). Assign one owner document. Send one
   agent to make the others follow it.

## 7. Review

- After a large agent task (a feature slice, a new module), run one review agent (medium tier) on
  the diff. Ask for correctness bugs, violations of the tech docs and doc drift. Ask for findings
  only, with file and reason.
- For many small tasks, review in one batch at the end of a wave.
- Send the confirmed findings to a fix agent, or fix a small one yourself.

## 8. Close

1. Compare the docs with the code: `## Data` and `## Implementation` match, `source_anchors` name
   the code, `mise run docs-verify` on the docs that hold.
2. Run `mise run docs-index` and `mise run docs-lint`. If the task moved, split or created
   documents, delegate a pass to the `librarian` agent (`.claude/agents/librarian.md`).
3. Delete the `wip/` files of the task. Commit only if the user asks.
4. Tell the user what was done, what was verified and how, and which questions wait for a human
   (the new `backlog.md` lines).

## Related docs

- [`AGENTS.md`](../../../AGENTS.md): the agent rules, including the subagent limit
- [`_docs/_meta/authoring.md`](../../../_docs/_meta/authoring.md): the doc duty after a change
- [`splitwise-fullstack`](../splitwise-fullstack/SKILL.md): the skill for code agents
- [`ste-writing`](../ste-writing/SKILL.md): the skill for doc agents
