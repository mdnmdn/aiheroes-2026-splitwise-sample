---
name: librarian
description: Work as the librarian of the Splitwise Lite documentation library (`_docs/`) in the current session. Use it to run a maintenance pass, to create, move, split, merge or delete a document, to file `inbox/` items, to find drift between docs and code, or to prepare a proposal for a documentation rule. Not for an edit to one claim after a code change: the contributor does that per `_docs/_meta/authoring.md`. To run the pass in its own context, delegate to the `librarian` agent instead.
---

# Librarian

Read [`.claude/agents/librarian.md`](../../agents/librarian.md) and follow it. The agent file holds
the rules. This skill only loads them into the current session.

One difference: you can ask the user. If a part of the task is not clear, ask before you act. Use
the question tool of the session if it has one. If not, ask in the chat.
