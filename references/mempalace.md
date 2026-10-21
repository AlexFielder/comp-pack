# Filing a pack into MemPalace

Goal: the next session on the repository, whatever it's about, can start from the pack's conclusions rather than rediscovering them. Skip this file if you don't use [MemPalace](https://github.com/MemPalace/mempalace) (no `mempalace` MCP server); the pack in the repository is the durable record either way.

## The decision: one curated drawer, not a manual mine

Use `mempalace_add_drawer` for a single **"start here"** drawer per pack, in the repository's wing, room `comprehension`. Don't mine the pack by hand.

Why:
- **The full text arrives anyway** if you run a scheduled mine over your repositories: it picks up uncommitted files under `docs/` too and files them, chunked, into the repository's wing (room `general`). A manual mine would duplicate that work, hold the palace lock (refusing every other session's writes while it runs), and needs the repository's `mempalace.yaml` to be present or it mines generated code.
- **Chunks bury the conclusions.** Mined chunks are 1-2 KB slices in room `general`, mixed with thousands of code drawers. A search for "what should I know about X" may surface a quiz answer or a table fragment instead of the headline. One drawer in its own room is findable by filter (`room: "comprehension"`) and reads as a whole.
- **Revisions stay clean.** A curated drawer is one id to replace; mined chunks of an old pack are replaced by the next mine automatically.

## Which wing

The wing is the `wing:` line of the repository's `mempalace.yaml`, for example `acme-web`. Check it exists with `mempalace_list_wings`.

Never file into a `wing_`-prefixed lookalike (`wing_acme-web`). Those are forks a palace transfer can leave behind; filing there splits the repository's memory in two. Worktrees and sibling clones can have their own wings; file into the main repository's wing only.

Use the palace your mine writes to. If a call is refused with "peer MCP writer active", a mine holds the lock: wait for it to finish and retry; don't kill anything.

## Replacing an earlier drawer

Before adding, search the wing's `comprehension` room (`mempalace_search` with `wing`, `room: "comprehension"`) for an earlier start-here drawer for the same repository. If one exists, delete it by id (`mempalace_delete_drawer`) after the new one is filed. Don't use `mempalace_delete_by_source` for this: it matches the full stored path of mined files and has no wing parameter, so it's the wrong tool for a curated drawer and risky in general (always `dry_run` it first if you ever do need it).

## The drawer

`added_by: comp-pack`, `source_file:` the pack's absolute path, `room: comprehension`. Content, at most about 4 KB, plain Markdown, no links needed (paths in backticks are fine):

```markdown
START HERE: <System> comprehension pack, YYYY-MM-DD (<branch> at <SHA>)
Full pack: <absolute path> (<committed | uncommitted at time of filing>)
<Restriction line if one applies.>

What it is: <two sentences>.

Five surprises:
1. <one line each, with the key file>
...

Checks: wired? <result in one line>. saved? <result in one line>.

Rules decided by Claude, not the owner: <list>.

Open owner questions (<n>): <the top three, one line each>.

In flight: <branches and PRs that change the picture, one line each>.

Where it breaks first: <the top two symptoms and where to look>.
```

Explain-back sessions add their own drawer in the same room (date, score, weak spots, pack defects). Keep the latest two per repository; delete older ones.
