# Reader briefs

Readers are subagents, each owning one area of the repository. They do the wide reading so the main session can spend its time verifying and writing. Launch them all in one message, in the background, and carry on (draft §1 and §8 from the survey, or prepare the next repository) while they run.

## Choosing the split

Three readers suit a single web app. Add a fourth when one area is too big for one reader to read whole files (rule of thumb: more than about 60 source files of hand-written logic in one area). Common splits:

| Repository shape | Readers |
|---|---|
| Web app with a domain library | domain rules; data and storage; runtime, auth and deploy |
| Plugin or module host (a substrate plus N modules) | substrate and kit; the modules' rules; data and storage; runtime, auth and deploy |
| Portal plus remote workers or job runners | domain packages; data, queue and storage; portal, auth and deploy; runner and execution |
| Library or command-line tool | public surface and rules; internals and state; build, packaging and release |

Give each reader the paths it owns and the paths it can ignore, so two readers don't read the same files.

## The brief

Paste this and fill in the angle-bracketed parts. Keep the method block verbatim: it is what makes reader output usable.

```text
You are one of <N> READERS feeding a "comprehension pack" for the repository <absolute path> (<one-line description>; read its README.md and CLAUDE.md first). The pack lets the owner, <owner>, answer: what should it do, how do we know it does it, where will it break, how would we fix it. Read <branch> at <SHA>; <note if the working tree differs and how to read the right content>.

<CONFIDENTIALITY line if the repository carries a restriction: "Write nothing to disk anywhere; return your findings only in your final message.">

YOUR AREA: <paths and what to find there>. <Specific questions for this area.>

METHOD (mandatory):
- Read whole files with the Read tool, not grep excerpts, for every file you make a claim about. For generated files (clients, migrations' designer files) note the size and skip them.
- Cite every claim as a repository-root-relative path with line(s): `src/Foo/Bar.cs:42` or `src/Foo/Bar.cs:40-55`. Never bare filenames.
- Mark each claim VERIFIED (you read the line) or INFERRED.
- CHECK 1 "wired?": for every rule/policy/function that has tests, search `src/` (excluding tests) for real callers, including DI registration and reflection-based discovery. Report wired YES with caller path:line, or NO. Tested-but-uncalled logic is the most valuable finding.
- CHECK 2 "saved?": for every input or action a user can submit in your area, trace it to where it is persisted (SaveChanges, file write, external store) or report that it is not persisted / only in memory.
- For each rule give its SOURCE: owner decision (cite doc/commit/comment), published standard (cite clause), prototype or upstream port (cite), or Claude's assumption (comment says assume/provisional/TODO, or no source at all).
- Do not modify any file. Read-only git/grep/gh commands only. A read-only live check that settles a claim (a Seq query, `gh api` for environment protection or the plan) is welcome; say that it was live.

RETURN (markdown, <length> words):
1. Files read (list).
2. <Area-specific map: components, entities, pipeline, or modules, with paths.>
3. Rules table: rule | plain English | source | wired? (caller) | tested? (test path).
4. Persistence findings (CHECK 2).
5. Surprises ranked by importance, each with evidence.
6. Gaps: important behaviour with no test, contradictions between code, comments and docs, dead code.
7. Questions only the owner could answer.
```

## Area-specific asks that paid off

- **Data and storage:** "List every write path (SaveChanges / ExecuteUpdate / file write) with path:line and its caller. Identify user-visible state held only in memory, a cache or a static, and what an app-pool recycle loses." Ask for a Mermaid `erDiagram` of verified relationships only.
- **Runtime, auth and deploy:** "Trace three representative requests end to end (route → middleware → auth → handler → data → response) with path:line at each hop." "Build a where-it-breaks table: symptom | likely cause | where to look." Ask about deploy guards, backups of files *and* database, secrets, app-pool always-on and idle timeout, and where migrations run.
- **Multi-tenant systems:** "How is a request's tenant determined, and does every page or API that reads tenant data check it? Look for insecure direct object references."
- **Runners and workers:** "How is the executor chosen, what happens when the external engine hangs or crashes, how does the worker authenticate and where does its secret live, does it validate job inputs such as paths and output names?"
- **In-flight branches that touch your area:** "Describe what is wrong on the default branch that branch X fixes (`git diff origin/<default>...origin/<branch>`)."

## Handling reader output

Treat each report as leads, not facts. Readers misread line numbers, miss DI registrations, and occasionally report a test helper as a production caller. The main session verifies every claim that reaches §2, every "No" under Wired?, every "not saved", and every conflict between readers, by opening the lines itself.
