---
id: meta-asd-ste-100
title: ASD-STE100 Simplified Technical English
kind: meta
status: current
summary: "What ASD-STE100 (Issue 9) is, its 53 writing rules in paraphrase, how to write with it, how to adapt it to software docs and agent-facing text, evidence, tools and limits."
read_when: you write or rewrite text that an agent or a non-native reader must read without help (AGENTS.md, prompts, procedures, error messages, CLI help, Behaviour and Contract sections)
updated: 2026-11-05
verified: 2026-11-05
review_cycle: yearly
---

# ASD-STE100 Simplified Technical English

Researched on 2026-10-03 from the official Issue 9 PDF and public sources (list in §11). This
document is a map of an external standard. This project does not own it. Its rules bind
the documents of this project only as far as `ste-writing.md` adopts them.

**Copyright.** ASD owns the specification and its dictionary. The PDF is free to download, but
redistribution and reproduction need written permission from the STE Maintenance Group (STEMG).
This document paraphrases the rules and cites rule numbers. It does not copy the dictionary or the
rule text. Get the original from <https://www.asd-ste100.org/>.

**One-line verdict.** STE is a controlled language with a small dictionary and 53 writing rules. Its
structural rules (short sentences, one instruction per sentence, active voice, simple tenses, one
word for one meaning) transfer well to agent-facing text. Its dictionary was built for aircraft
maintenance and does not transfer: a project glossary replaces it.

---

## 1. What STE is

ASD-STE100 is a controlled natural language for technical documentation. It restricts the
vocabulary and the grammar of English, so that each word has one meaning and each sentence has one
reading. The original reader was an aircraft mechanic with limited English and no person to ask.
An LLM agent that reads another agent's output is in the same position.

| Item | Fact |
|---|---|
| Origin | AECMA (European aerospace industries) and AIA, at the request of European airlines. Working group founded 1983, first guide 1986 |
| Name | "STE100" honours the ATA100 publication specification, which required it from 1987 |
| Owner | ASD (successor of AECMA). STEMG maintains it, with national support teams |
| Current issue | **Issue 9, 2025-01-15**. It replaces all earlier issues. Release cadence is about 3-4 years |
| Issue 9 changes | Re-titled "Standard for technical documentation". 31 of 53 rules reworded, no new rules. 555 dictionary entries changed. "Technical name" became "technical noun". Two technical-noun categories added (law, life forms). Terms aligned with ISO 1087 |
| Availability | Free PDF by web form. No redistribution without STEMG written permission. "ASD-STE100" is an EU trademark |
| Change requests | A change form to `stemg@asd-ste100.org` |
| Use outside aerospace | Defence, machinery, automotive, medical, energy, IT and software. Wikipedia reports that most Issue 8 recipients work outside aerospace (unverified figure) |

What STE does **not** do, by its own statement:

- It does not regulate format, abbreviations or units. Use it with a style guide, never alone.
- It is not an English course. Writing STE needs good English and knowledge of the subject.
- It does not make empty text useful. It fixes form, not substance.

## 2. Structure of the specification

The specification has two parts.

- **Part 1, writing rules**: 9 sections, 53 numbered rules, plus 8 general recommendations that are
  not rules. Each rule has an explanation, examples (non-STE and STE) and, in Issue 9, "help" notes.
- **Part 2, dictionary**: 875 approved words and 1274 non-approved words with approved
  alternatives. Public sources round this to "about 900 words".

### 2.1 How the dictionary works

- Each approved word has **one part of speech** and **one meaning**. "Test" is an approved noun, not
  a verb: write "Do a test of the system", not "Test the system". "Turn" means rotate, so
  "The light turns green" is wrong.
- A non-approved word has a pointer to an approved alternative: *ensure* → MAKE SURE, *perform* →
  DO, *may* → CAN, *should/shall* → MUST, *however* → BUT, *since* → BECAUSE, *main* → PRIMARY,
  *follow* (an instruction) → OBEY.
- Verbs have a fixed list of permitted forms (for example REMOVE, REMOVES, REMOVED).

### 2.2 Technical nouns and technical verbs

Words outside the dictionary are allowed when they belong to a category:

- **22 technical-noun categories** (rule 1.5). Examples: official part names, tools, materials,
  systems and their parts, units and numbers, quoted text, roles and organisations, official
  documents, operating conditions, colours, damage terms. **Category 19 is computer science and
  ICT**: database, file, network, interface, prompt, token, update. Issue 9 adds AI terms (chatbot,
  large language model, prompt engineering, hallucination).
- **4 technical-verb categories** (rule 1.12): manufacturing processes, **computer processes**
  (click, type, enter, open, save, delete, copy, scroll, boot, download, install, reboot, upload),
  subject-field instructions, and law. Use a technical verb only when no approved verb says the
  same thing: "find broken wires", not "detect broken wires".

Your own project terms (in this project: expense, payer, share, balance, settlement plan) are technical nouns.
Rules 1.8 to 1.11 say: use the terms your field approves, keep them short, avoid slang, and never
use two terms for one item.

## 3. The writing rules (paraphrase)

Numbers are the official rule numbers of Issue 9. The wording below is ours.

### Section 1: Words (rules 1.1-1.14)

- Use approved words, technical nouns or technical verbs only (1.1).
- Use an approved word only as its part of speech, with its meaning, in its approved forms (1.2-1.4).
- Never use a technical noun as a verb (1.7: "apply oil", not "oil"), or a technical verb as a noun
  (1.13).
- Use one term for one item, everywhere (1.11). No regional words, slang or jargon (1.10).
- Use American spelling unless a directive says otherwise (1.14).

### Section 2: Multi-word nouns (2.1-2.2)

- A noun cluster has three words at most (2.1). Break longer ones with "of", "for", "in":
  "the bolts that attach the housing to the engine", not "engine housing attachment bolts".
- If an official name is longer, write it in full once, then use a short form or hyphens (2.2).

### Section 3: Verbs (3.1-3.7)

- Six forms only: infinitive, imperative, simple present, simple past, simple future, and the past
  participle as an adjective (3.2, 3.3).
- No present perfect, past perfect, progressive or other complex constructions (3.4).
  "The operator has adjusted" → "The operator adjusted".
- No "-ing" form, except as part of a technical noun ("troubleshooting", "welding torch") (3.5).
- Active voice. Passive only in descriptions and only when the actor is unknown (3.6). Ask "by whom?".
- Use a verb for an action, not a noun: "before you remove the unit", not "before the removal of the
  unit" (3.7).

### Section 4: Sentences (4.1-4.5)

- Short and clear sentences (4.1).
- Do not omit words or use contractions to save space (4.2): "If shims are installed, remove them",
  not "If installed, remove shims". "Do not", never "don't".
- Use a vertical list for complex text (4.3). The list starts after a colon. Do not mix procedural and
  descriptive items in one list.
- Use connecting words (and, but, then, thus, as a result) between related sentences (4.4).
- Use articles and "this/these" before nouns (4.5): "Turn the shaft", not "Turn shaft". No article
  before an identifier.

### Section 5: Procedural writing (5.1-5.5)

- **Max 20 words** per sentence (5.1). This includes warnings and cautions.
- **One instruction per sentence**, unless the actions occur at the same time (5.2).
- Imperative form (5.3). Do not put "must" before an imperative, except for important safety text.
- **Condition first**, then a comma, then the command (5.4): "When the light comes on, set the switch
  to NORMAL."
- Notes give information, never instructions (5.5). Test: the procedure works with all notes removed.

### Section 6: Descriptive writing (6.1-6.6)

- Give information step by step, one subject per sentence (6.1).
- Repeat key words and key phrases instead of synonyms. They give the text its structure (6.2).
- **Max 25 words** per sentence (6.3).
- One topic per paragraph, topic sentence first, **max 6 sentences** per paragraph (6.4-6.6).
- No imperatives in descriptive text.

### Section 7: Safety instructions (7.1-7.3)

- Use a signal word for the level of risk: WARNING (injury or death), CAUTION (damage to equipment)
  (7.1).
- Start with a clear command, or with the condition when the reader must know it first (7.2).
- Always state the risk or the result (7.3).
- Placement before the step is a convention of publication specifications (S1000D, ATA), not a
  numbered STE rule.

### Section 8: Punctuation and word count (8.1-8.7)

- **No semicolons** (8.1). Write two sentences.
- Hyphens join words that act as one unit (8.2). A hyphenated group counts as one word (8.7).
- Parentheses are allowed for references, identifiers, alternatives and short explanations (8.3).
  Text in parentheses counts as one word in its sentence (8.5).
- In a vertical list the colon ends the sentence, and each item counts as its own sentence (8.4).
- Each of these counts as one word: a number, a number with unit, an abbreviation, an identifier,
  quoted text, a title or label, a proper name (8.6). **A code identifier counts as one word.**

### Section 9: Writing practices (9.1-9.4)

- When a word-for-word replacement fails, change the sentence construction (9.1).
- Use each approved word correctly (9.2).
- No phrasal verbs made of approved words (9.3): "extinguish", not "put out". Only a few
  (put on, come on) are approved.
- Use a consistent style: the same type of step has the same sentence pattern (9.4).

**General recommendations** (not rules): use "that" after "make sure"; avoid ambiguous "with" and
"this"; repeat the noun when a pronoun is unclear; avoid Latin abbreviations (e.g., i.e., etc.);
use neutral language; take care with possessives.

### 3.1 Numeric limits

| Item | Limit | Rule |
|---|---|---|
| Procedural sentence | 20 words | 5.1 |
| Descriptive sentence, note sentence | 25 words | 6.3, 5.5 |
| Paragraph | 6 sentences, 1 topic | 6.5, 6.6 |
| Noun cluster | 3 words | 2.1 |
| Instructions per sentence | 1, unless simultaneous | 5.2 |
| Verb forms | 6 | 3.2 |
| Semicolons | 0 | 8.1 |

## 4. How to write in STE: a method

### 4.1 Before you write

1. Decide the text type for each section. **Procedural** text tells the reader what to do
   (steps, rules for an agent, a runbook). **Descriptive** text tells the reader what is true
   (behaviour, contracts, explanations). The limits differ: 20 words against 25.
2. List the technical nouns the text needs. Take each one from the project glossary
   (`_docs/product/glossary.md`). If a term is missing, define it once and use only that term.
3. Find the reader's conditions: what must the reader know **before** each action?

### 4.2 While you write

- One sentence, one idea. One step, one action.
- Put the actor first and use an active verb: "The app rejects the expense", not "The expense is rejected".
- Put the condition before the command: "If the group has no expense, add one expense."
- Use the simplest verb that is exact: use, do, make sure, start, stop, show, find, get, give, put.
- Use the same word for the same thing on every line. Do not rotate synonyms for style.
- Keep articles and subjects. Do not write telegraph style.
- Use a vertical list for three or more steps, conditions or items.
- Keep hedges that carry real uncertainty ("the exchange rate can be out of date"). Remove filler hedges
  ("it is important to note that this may potentially help").

### 4.3 When you revise

Read each sentence and ask:

1. Is there one possible reading only? If not, change the construction (9.1), do not just swap words.
2. Does it have more than 20 words (procedure) or 25 words (description)? Split it.
3. Is there a semicolon, a dash that joins two clauses, or a parenthesis with a full clause? Split it.
4. Is it passive, present perfect, progressive, or does it use "-ing" as a verb? Rewrite it.
5. Is a noun doing the job of a verb ("perform a validation of")? Use the verb.
6. Does each paragraph have one topic and six sentences at most?
7. Did the rewrite keep every fact, every condition and every limit? Compare against the original.

Stop when the sentence is unambiguous, not when it is shortest.

## 5. Adapting STE to software and agent-facing text

STE was designed for paper maintenance manuals. For the readers of this project (agents and developers) apply
these adaptations.

### 5.1 Code and identifiers

- An identifier, a flag, a path, a JSON field or a command is a technical noun. Write it verbatim in
  code font. It counts as one word (8.6).
- Do not inflect an identifier like an English word. Add a noun: "the `Env.History` result", not
  "`Env.History`'s".
- One concept, one identifier, one prose word. If the flag is `--out`, do not call it "output path"
  in one place and "destination file" in another.

### 5.2 The glossary is the dictionary

The ASD dictionary cannot be copied, and most software words are not in it. STE itself allows
company terminology (1.8). The project glossary plays the role of Part 2: one entry per term, one
meaning, the term used everywhere. Synonym rotation (expense/bill/charge, check/verify/validate)
is the most common and most costly STE violation in software text.

### 5.3 Normative strength

STE replaces *should*, *shall* and *may* with MUST and CAN, and writes procedures in the imperative.
For agent instructions:

- Use the imperative for a required action: "Run `just check` before you finish."
- Use "Never ..." or "Do not ..." for a prohibition, and name the permitted action next to it.
- Use RFC 2119 / RFC 8174 capitals (MUST, SHOULD, MAY) only in specifications, and then in capitals
  only. Lowercase "should" stays ordinary English and is ambiguous: avoid it.
- Do not shout. "CRITICAL: you MUST ALWAYS" makes recent models over-apply the rule. A calm, exact
  rule works better.

### 5.4 Keep the reason

Bare commands generalise badly. LLM vendors (Anthropic, OpenAI) recommend that each hard rule
carries its motivation, so the agent can apply it to cases the rule does not list. STE permits this
as descriptive text. Write the rule as a command, then one short descriptive sentence with the
reason:

> Never edit files in `_docs/inbox/`. Raw input must stay verbatim, so that later readers can
> trust it as the original.

### 5.5 Positive phrasing and examples

- A prohibition names the forbidden thing and can prime it. When possible, say what to do:
  "Write the answer in plain paragraphs", not "Do not use markdown".
- An example often teaches a format faster than a rule. Keep examples short and label them.

### 5.6 Per text type

| Text | Apply |
|---|---|
| `AGENTS.md`, prompts, standing instructions | Procedural rules (20 words, one instruction, imperative, condition first) plus one reason sentence per hard rule |
| Tool and command descriptions | What it does, when to use it, inputs with types and examples, output shape, hard limits |
| Error messages | What failed, why, what to do, in that order, with identifiers verbatim |
| CLI help | Imperative verb first, one line per flag, default and unit stated |
| Behaviour, Contract, Failure sections | Descriptive rules (25 words, active voice, one condition per sentence, glossary terms only) |
| Rationale, product text, decisions | STE-flavoured only: sentence rules loosely, full freedom of vocabulary |
| Agent-to-agent messages | Status as facts, named items, one instruction per sentence |

## 6. Examples

### 6.1 From the specification (short, paraphrased where long)

| Non-STE | STE | Rule |
|---|---|---|
| The operator has adjusted the linkage. | The operator adjusted the linkage. | 3.4 |
| The circuits are connected by a switching relay. | A switching relay connects the circuits. | 3.6 |
| Set the switch to NORMAL when the light comes on. | When the light comes on, set the switch to NORMAL. | 5.4 |
| Examine the removed parts; replace the damaged ones. | Two numbered steps: examine, then replace. | 8.1 |
| Rotary switch to INPUT. | Set the rotary switch to INPUT. | 4.2 |
| Follow the safety instructions. | Obey the safety instructions. | 1.3 |
| Main body, body, body assembly (one part) | Body assembly, every time | 9.4 |

### 6.2 Software and this project (our own examples)

**Error message.**
Before: `error: could not complete, the split may be wrong or some data is missing`
After: `error: expense rejected. The shares add up to 80.00 EUR and the amount is 90.00 EUR. Change the shares so that they add up to 90.00 EUR.`

**CLI help.**
Before: `--currency   Specifies which money type might be used for the group, if desired.`
After: `--currency CODE   Set the base currency of the group. Use an ISO 4217 code. Default: EUR.`

**Agent rule.**
Before: `The agent should try not to touch the stored money stuff since that might be bad.`
After: `Never store an amount as a decimal number. Store minor units, for example 9000 for 90.00 EUR. Decimal numbers lose cents.`

**Descriptive rule (one condition per sentence).**
Before: `an expense split equally among its participants gives each participant the amount divided by their count, and any leftover cent goes to the first participants in order, unless the split mode is exact, in which case the shares are taken as typed and must add up to the amount.`
After:

- In the equal split mode, each participant gets the same share.
- If the amount does not divide evenly, the app adds one minor unit to the first shares.
- In the exact split mode, the app uses the shares as the user typed them.
- If the exact shares do not add up to the amount, the app rejects the expense.

**Terminology.**
Before: `Add the bill ... the debt of each friend is updated ... the settlement is saved as a transfer.`
After: `Add the expense ... the app updates the balance of each member ... the app records the payment.`

**Acceptance example.**
Before: `Alice covers a dinner for the group, so the others owe her.`
After: `Alice pays 90.00 EUR for Alice, Bob, Carla → Alice +60.00 EUR, Bob −30.00 EUR, Carla −30.00 EUR.`

**Agent-to-agent message.**
Before: `Looks like it's mostly done but a few issues were noticed, might be good if someone took a look.`
After: `Two tests fail: TestEqualSplit and TestExactSplit. Fix both tests. Do not change other files. Report the result.`

## 7. Evidence and limits

### 7.1 What is measured

- **Human readers.** Chervak, Drury and Ouellette (1996): 175 aircraft technicians, 16 work cards.
  Comprehension errors fell from 18% to 14%. For non-native readers, accuracy rose from 69% to 87%.
  The gain was largest on difficult text. This is the main hard evidence, and it is old.
- **Machine translation.** Controlled language helped rule-based and statistical MT. With neural MT
  it gave no gain, or a small loss. Miyata and Fujita (2021) found that explicit, syntactically clear
  source text matters more than short, simple text.
- **LLM instruction following.** No peer-reviewed study tests STE-rewritten prompts. Adjacent
  results: underspecified prompts regress twice as often across model changes (Yang et al. 2025).
  Better tool descriptions improved agent results (Anthropic). AGENTS.md files raise cost by over
  20% and do not raise task success in general, but agents do obey the instructions in them
  (Gloaguen et al. 2026).
- **STE skills for LLM output** report fewer linter violations (one claims 78% fewer). They measure
  style compliance, not task quality.

**Verdict.** Explicitness and consistent terms have support. Short sentences alone do not. Use STE
to remove ambiguity, never to remove information.

### 7.2 Known limits and risks

- The dictionary is too narrow for software, and noun/verb splits force long phrases
  ("Do a test of" instead of "test").
- Bare imperatives drop the reason. Agents then apply rules badly to edge cases (§5.4).
- Split sentences make text longer. Context files already cost tokens, so cut content that
  does not change behaviour.
- The tone is mechanical. That suits agent text and runbooks. It does not suit product prose.
- A checker finds form problems only. "Only human writers can judge whether a sentence makes good
  sense" (Boeing). No tool and no text can be certified STE-compliant by ASD.
- Underspecification is a bigger risk than complexity. A short text that omits a requirement is
  worse than a long precise one.

## 8. Tools

None of these is endorsed by ASD. All open-source items are MIT unless noted. Items marked (u) were
seen only in search results.

| Tool | Kind | Checks / notes |
|---|---|---|
| Boeing Simplified English Checker | Commercial, since 1990 | Parser with 400+ rules: length, vocabulary, verb forms, noun clusters, articles |
| HyperSTE (Etteplan), Congree, Acrolinx / Markup AI | Commercial | Rules plus licensed dictionary, editor plugins, custom term lists |
| TechScribe STE checker | Open, on LanguageTool | STE terms and grammar rules, extensible with project terms |
| `danyuchn/asd-ste100-skill` | Claude skill + Python linter | Strict and STE-flavoured modes. Keeps real hedges. Linter: semicolons, 6 soft phrasal verbs, marketing adjectives, nominalisation, passive and present perfect (advisory), sentences over 25 words, 10 synonym groups, list items that end in "and/or". No dictionary |
| `1fc0nfig/ste-writing` | Skill + linter | Adds paragraph length, dashes, gerunds, contractions, hedges, violations per 100 words |
| `JAICHANGPARK/ASD-STE100` | Skill + CLI | Strict and pragmatic modes, modals, noun clusters, Latin abbreviations |
| `sjtower/ste-plugin` | Claude plugin | `/ste-check`, `/ste-rewrite`, error/warning/review levels |
| `stuffbucket/vale` | Go linter + MCP server | 8 structural rules, OpenSTE vocabulary |
| OpenSTE | Word list | Community wordset, independent of ASD |
| `dfch/AsdSte100Vocab` | Word list, AGPL-3.0 | Carries the ASD vocabulary. Copyright status is doubtful: do not vendor |
| Vale (Google, Microsoft styles), write-good, proselint | Generic prose linters | No STE rule set. Vale can host custom rules |

The mechanical checks are cheap: sentence length, paragraph length, semicolons, contractions,
"-ing" verbs, passive and perfect tenses (advisory), synonym groups, banned words. Noun clusters
need part-of-speech tagging and give many false positives. Meaning preservation needs a human or
a review agent.

## 9. Related standards

| Standard | Core idea | Relation to STE |
|---|---|---|
| Plain Language (US, digital.gov) | Write for the reader, test for understanding | Outcome-based, no word list. Wider and softer |
| ISO 24495-1:2023 | Readers find, understand and use what they need | Principles that STE implements in part |
| Google developer style guide | Second person, active voice, present tense, condition before instruction, code font for identifiers | Overlaps the STE sentence rules. Good source for code-in-text conventions |
| Microsoft Writing Style Guide | Crisp, clear, global English | Overlaps, warmer tone |
| RFC 2119 / RFC 8174 | MUST, SHOULD, MAY in capitals carry requirement strength | Fills the gap STE leaves for graded requirements |
| Attempto Controlled English | English subset with formal logic semantics | Far stricter, machine-parsable |
| Caterpillar Technical English | Industrial controlled language for translation | A sibling of STE |

## 10. Checklist

Procedural text (instructions, agent rules):

- [ ] Each sentence has 20 words or fewer. Identifiers count as one word.
- [ ] Each sentence has one instruction, in the imperative.
- [ ] Each condition comes before its command.
- [ ] Each hard rule has one sentence with its reason.
- [ ] No "should", "might", "try to". Use a command, "Never", or a capital MUST in a specification.

Descriptive text (behaviour, contracts):

- [ ] Each sentence has 25 words or fewer and one condition at most.
- [ ] The actor is named and the verb is active.
- [ ] Each paragraph has one topic and six sentences at most.

All text:

- [ ] Each term comes from the glossary and keeps one meaning. No synonyms.
- [ ] No semicolons, no contractions, no phrasal verbs, no Latin abbreviations.
- [ ] Only simple tenses. No "-ing" as a verb. No noun where a verb fits.
- [ ] Identifiers are verbatim, in code font, and not inflected.
- [ ] The rewrite keeps every fact, limit and real hedge of the original.

## 11. Sources

Specification and governance:

- ASD-STE100 Issue 9 PDF: <https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf>
- STEMG site and downloads: <https://www.asd-ste100.org/>
- ASD overview: <https://www.asd-europe.org/standards-specifications/simplified-technical-english/what-are-the-basics-of-simplified-technical-english/>
- Issue 9 summaries: <https://www.tcworld.info/e-magazine/technical-writing/asd-ste100-issue-9-setting-a-standard-for-technical-documentation>,
  <https://simplifiedtechnicalenglish.substack.com/p/from-specification-to-standard-understanding>
- Wikipedia: <https://en.wikipedia.org/wiki/Simplified_Technical_English>

Evidence:

- Chervak, Drury, Ouellette 1996: <https://journals.sagepub.com/doi/abs/10.1177/154193129604000502>
- Controlled language and NMT: <https://link.springer.com/article/10.1007/s10590-019-09233-w>
- Miyata, Fujita 2021: <https://arxiv.org/abs/2102.02955>
- Yang et al., underspecified prompts: <https://arxiv.org/abs/2505.13360>
- Gloaguen et al., AGENTS.md files: <https://arxiv.org/abs/2602.11988>
- Negated instructions: <https://arxiv.org/pdf/2404.15154>

Vendor guidance for prompts and tools:

- Anthropic prompting best practices: <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices>
- Anthropic, writing tools for agents: <https://www.anthropic.com/engineering/writing-tools-for-agents>
- OpenAI GPT-4.1 prompting guide: <https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide>
- Google, code in text: <https://developers.google.com/style/code-in-text>
- RFC 2119: <https://www.rfc-editor.org/rfc/rfc2119>, RFC 8174: <https://www.rfc-editor.org/rfc/rfc8174.txt>

Tools:

- <https://github.com/danyuchn/asd-ste100-skill>, <https://github.com/1fc0nfig/ste-writing>,
  <https://github.com/JAICHANGPARK/ASD-STE100>, <https://github.com/sjtower/ste-plugin>,
  <https://github.com/stuffbucket/vale>, <https://github.com/openste/openste>
- Boeing checker: <https://www.boeing.com/company/simplified-english-checker>
- TechScribe: <https://www.simplified-english.co.uk/>
- Other standards: <https://digital.gov/guides/plain-language>, <https://www.iso.org/standard/78907.html>,
  <https://attempto.ifi.uzh.ch/site/docs/ace_constructionrules.html>,
  Kuhn's survey of controlled natural languages <https://aclanthology.org/J14-1005.pdf>

## Related docs

- [`./ste-writing.md`](./ste-writing.md) — the project dialect that adopts this standard
- [`./authoring.md`](./authoring.md) — the writing rules that bind documents of this project
- [`../product/glossary.md`](../product/glossary.md) — the project terms, the STE dictionary of this project
