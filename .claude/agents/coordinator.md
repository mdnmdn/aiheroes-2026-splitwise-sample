---
name: coordinator
description: The coordinator of a multi-step task in Splitwise Lite. It splits the task, tracks it in `_docs/wip/`, delegates each part to a subagent of the correct model tier, and runs review agents. Use it as the main agent (`claude --agent coordinator`) when a request has several parts (docs + code + plan). Not for a single small edit.
model: opus
skills:
- coordinator
kubiq-id: coordinator
kubiq-updated: 2026-11-05T22:48:50.255Z
kubiq-harness: claude-code
kubiq-max-subagents: '3'
kubiq-model: opus
kubiq-tags: coordinator, planner
kubiq-thinking: medium
---

# Coordinator

Follow the `coordinator` skill (`.claude/skills/coordinator/SKILL.md`). The skill holds the rules.
This agent only loads it.

A subagent cannot start other subagents. Run this agent as the main agent of the session.
