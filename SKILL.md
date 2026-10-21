---
name: comp-pack
description: Build a comprehension pack for a repository, a single evidence-backed document that lets the owner answer, without asking Claude, what the system should do, how we know it does it, where it breaks and how to fix it, and run explain-back sessions in which the owner proves that understanding. Use this whenever someone says "comp pack", "comprehension pack", "comprehension pass", "help me understand this repo", "I don't understand what Claude built", "black box", "walk me through how X works end to end", "onboard me to <repo>", "explain-back", "quiz me on <repo>", "test my understanding", or wants to revise an existing pack in docs/comprehension/. Also use it before a handover, a client review or a retainer review of AI-built code, even if the word "pack" never appears. Not for a quality or security audit, or for a diff review (use code-review).
---

# Comprehension pack

AI-assisted delivery produces working systems faster than their owner can absorb them. Reading every line doesn't scale and more tests don't help if nobody knows what the tests prove. A comprehension pack is the alternative: one document, verified against the code, that answers four questions about a repository.

1. **What should it do?** The system map, the data model and the rules, each rule tagged with *who decided it*.
2. **How do we know it does it?** Whether each tested rule is actually *called*, and whether what users enter is actually *saved*.
3. **Where will it break?** Surprises, request walk-throughs, the deploy, and a symptom → cause → where-to-look table.
4. **How would we fix it?** Owner questions, in-flight branches, and ordered next steps.

The first pack this method produced found that a system's tested domain rules had no callers and that nothing users entered was saved. Neither showed up in green builds or passing tests. That is the point of the method: claims get verified in the code, not trusted.

Two modes:
- **Build or revise a pack:** the workflow below.
- **Explain-back:** read [references/explain-back.md](references/explain-back.md) and follow it.

## Build a pack

### 1. Survey (main session, about 10 minutes)

- Read the repository's `README.md` and `CLAUDE.md` (or equivalent) and the newest existing pack in `docs/comprehension/` if there is one. A revision starts from the old pack plus every explain-back record in `docs/comprehension/explain-back/`: weak spots recorded there get expanded in the new pack.
- Pin the commit: default branch, short SHA, version if the repository carries one. `git fetch` first. If the checkout sits on another branch, say so and read the default branch's content (`git show origin/<default>:<path>` or confirm the code is identical with `git diff --stat HEAD origin/<default>`). Don't switch branches in someone's checkout.
- List in-flight work: open pull requests (`gh pr list`), branches ahead of the default branch with `git rev-list --left-right --count`, `git diff --shortstat`, and worktrees (`git worktree list`). You note these in §8; you don't read them all.
- Map the layout (`git ls-files | sed 's|/.*||' | sort | uniq -c`) and decide how to split the reading.

### 2. Readers (parallel subagents)

Launch three or four reader subagents **in one message**, each owning one area, and do other work while they run. The split that worked:

| Reader | Area |
|---|---|
| Domain rules | the business logic and its tests; split into two readers when there are many modules or packages |
| Data and storage | contexts, entities, migrations, seeding, every write path, what lives only in memory |
| Runtime, auth and deploy | the request pipeline, sign-in and authorization, error handling, logging, CI and deploy, where it breaks |
| (optional) Execution | background workers, job runners, external engines, anything long-running |

Use the brief in [references/reader-briefs.md](references/reader-briefs.md). Its non-negotiables: read whole files, cite every claim with a repository-root-relative `path:line`, mark each claim VERIFIED or INFERRED, run the two checks below, tag each rule's source, and modify nothing.

### 3. The two checks that earn their keep

Every pack runs both, and reports the result even when it's good news.

- **Wired?** For every rule, policy or function that has tests, find its non-test callers. A tested rule with no caller is a specification that nothing runs, and whatever users actually see comes from somewhere else (often untested). Search the whole source tree, not only the obvious caller, and check dependency injection registrations and reflection-based discovery before declaring something unwired.
- **Saved?** For every form, action or input a user can submit, trace it to a durable write (`SaveChanges`, a file, an external store) or show that it isn't one. Watch for in-memory singletons, static lists, caches loaded once at start-up, and "save" buttons that only mutate an object.

Two cheaper checks are worth the minutes, because each found a headline on the second run:
- **Does the default branch still build?** Look at the last CI run on the default branch (`gh run list`) and, if nothing has deployed recently, run the restore the CI runs (for .NET, `dotnet restore --locked-mode`). Locked restores with NuGet audit as errors break silently when a new advisory lands, and the live site then can't be patched.
- **Do the comments and docs match the code?** Readers find claims like "write scopes are asserted there" or "the runner's 30-second heartbeat" that the code contradicts. A comment that promises a safety mechanism which doesn't exist is a surprise-grade finding, not a documentation nit.

### 4. Verify (main session)

Readers are fast but wrong often enough to matter. Before writing, open the cited lines yourself for:
- every headline claim (anything that goes into §2 "surprises" or §10 "next steps");
- every "No" in a Wired? column and every "not saved" finding;
- anything two readers disagree on.

Drop or soften what doesn't survive. Say "inference" where you couldn't confirm. Budget about a third of the session for this; it's where the value is.

After writing, run the bundled checker, which validates every link against the contract and, with `--show`, prints the first lines each anchor lands on:

```bash
python ~/.claude/skills/comp-pack/scripts/check_refs.py --show docs/comprehension/<pack>.md
```

Read the `SHOW` lines, not just the totals. Readers' line numbers in JSON, YAML and workflow files are the least reliable: on one run two `appsettings` citations pointed past the end of a 37-line file, and only the checker caught them.

### 5. Write the pack

Path: `docs/comprehension/YYYY-MM-DD-comprehension-pass.md` in the target repository (today's date, ISO format). Follow [references/pack-template.md](references/pack-template.md): ten sections, in order. If you already have a good pack in another repository, copy its structure and tone, but never use a pack from a confidential repository as a model for another client's work.

Leave the pack **uncommitted** unless the owner says otherwise: the owner reads it first, and that reading is the point.

### 6. File it into MemPalace

Read [references/mempalace.md](references/mempalace.md). In short: the scheduled mine already chunks the full pack into the repository's wing, so you add one curated **"start here"** drawer in room `comprehension` with the facts a future session needs first. Skip this step if you don't use [MemPalace](references/mempalace.md). If `add_drawer` says "peer MCP writer active", a mine holds the palace lock: draft the drawer, wait for the mine to finish and retry.

### 7. Report

Give the owner: the pack's path, the five surprises in one line each, the wired/saved results, the number of owner questions, and what to read first. Then offer an explain-back session.

## The reference contract

The Claude desktop app's file pane, GitHub and VS Code (with or without the "comp pack reader" extension) all turn references into clickable links, so every reference follows one form (contract version 2):

```markdown
[src/Acme.Web/Program.cs:131](../../src/Acme.Web/Program.cs#L131)
[src/Acme.Web/Services/OrderStore.cs:58-92](../../src/Acme.Web/Services/OrderStore.cs#L58-L92)
[.github/workflows/deploy.yml](../../.github/workflows/deploy.yml)
```

- **Link text:** the path relative to the repository root, no leading slash, then `:line` or `:start-end` when a line matters.
- **Target:** the same path relative to the Markdown file's own folder (`../../` from `docs/comprehension/`), then `#L<line>` or `#L<start>-L<end>`. All three consumers resolve targets from the file's folder; a leading `/` breaks in the desktop app.
- **Always the full path.** Never a bare filename, never "same file, line 495": write a second full link. Several lines in one file means several links.
- Encode spaces in the target as `%20`. Use forward slashes everywhere.
- Inside Mermaid diagrams and fenced code, write no links; name the file in the surrounding prose instead.
- A reference to another repository uses its full URL instead.

The full contract, with edge cases, is in [references/reference-format.md](references/reference-format.md). Change it only together with the extension.

## Writing conventions

The reader is the owner, who knows the domain and roughly what was built, but not the code. Write for them.

- **Active voice, no hedging.** "The deploy wipes the folder", not "the folder is wiped". Keep "may" only for real uncertainty, and then say what would settle it.
- **Spell out every abbreviation the first time**, full term first, abbreviation in brackets: "insecure direct object reference (IDOR)". After that, use the abbreviation.
- **ISO dates** (YYYY-MM-DD) everywhere.
- **Estimates in attended hours**, not engineer-days, if the pack gives any. AI-assisted delivery runs far below conventional estimates.
- **Plain-English first, evidence second.** Each claim says what happens in words, then cites where. A table cell that only holds a path teaches nothing.
- **Label sources honestly.** "Claude's assumption" is not an insult; it's the most useful label in the pack, because it marks what the owner has never decided.
- **No praise padding.** Good news gets one line; the reader's time goes to what will surprise them.

## Confidentiality

Some repositories carry restrictions on where their content may go. Before writing, check the task, the repository's `CLAUDE.md` and the global instructions for any, and:
- put the restriction as the first line under the pack's title, in bold;
- keep the pack, reader output and notes out of every forbidden location (no copies to shared notes folders, ops repositories or other projects' dossiers);
- tell readers in their brief to write nothing to disk.

A typical case: a client's codebase that must never reach a clean-room rebuild of the same product, or a shared operations repository.

## Checklist before you hand over

- [ ] Commit pinned in the header; branch situation stated.
- [ ] All ten sections present; §2 has exactly five surprises, each verified by you.
- [ ] Every rule in §4 has plain English, a source and a Wired? answer with evidence.
- [ ] The Saved? result is stated explicitly somewhere in §2 or §3.
- [ ] `scripts/check_refs.py --show` reports 0 hard problems and every `SHOW` line lands on the code its sentence describes.
- [ ] Abbreviations expanded on first use; dates ISO; no passive or "would be" hedges.
- [ ] Self-quiz answers in `<details>` with a blank line after `</summary>`, each citing evidence.
- [ ] Pack left uncommitted; MemPalace start-here drawer filed; restriction line present if one applies.
