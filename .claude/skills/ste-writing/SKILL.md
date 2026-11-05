---
name: ste-writing
description: Write or rewrite text in the Splitwise Lite dialect of ASD-STE100 Simplified Technical English, for readers (agents, non-native developers) that cannot ask for clarification. Use before you write or change any document in _docs/ or AGENTS.md, and for prompts, standing instructions, CLI help, error messages and commit messages. Also use when the user asks to "apply STE", "simplify", "disambiguate" or "make this unambiguous". Not for code, marketing copy or casual chat.
---

# STE writing (Splitwise Lite)

Write so that each sentence has one reading and each word has one meaning. This skill fixes form,
not content: never drop or add a fact.

1. Read `_docs/_meta/ste-writing.md`. It holds the rules: scope, modes, sentence rules, vocabulary, patterns.
2. Read `_docs/product/glossary.md`. It is the dictionary of project terms. Do not use a word from its *Not* column.
3. For a case the rules do not cover, read `_docs/_meta/asd-ste-100.md`.
4. Pick the mode of each section from the scope table. Then check each sentence against the rules of that mode.

## Self-check before you finish

- Each sentence has one idea. It obeys the word limit of its mode.
- The voice is active, and the actor is named. No "-ing" verb forms, no semicolons, no contractions.
- Each product term is a glossary term. Each amount has its currency code: `90.00 EUR`.
- No fact was dropped or added. No requirement changed strength.

## Output

- By default, return the rewritten text only. No preamble, no change summary.
- If you kept a longer or non-STE form on purpose, add one last line:
  `Kept as-is: <phrase>: <the precision a rewrite would lose>`.
- When the user asks which rules broke, add a table `| Rule | Original | Rewrite |` before the text.
- When you edit a file, edit in place with the Edit tool. Do not rewrite a file with a script.
