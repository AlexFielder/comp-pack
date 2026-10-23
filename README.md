# comp-pack

A [Claude Code](https://claude.com/claude-code) skill that builds a **comprehension pack** for a repository: one evidence-backed document that lets the owner answer four questions without asking Claude.

1. **What should it do?** The system map, the data model and the rules, each rule tagged with who decided it (the owner, a published standard, earlier code, or Claude's own assumption).
2. **How do we know it does it?** Whether each rule's contract (`requires` / `ensures` / `invariant`) is enforced by anything, whether each tested rule is actually called, and whether each action has the effects it should: above all, whether what users enter is actually saved, and whether a "read" quietly writes.
3. **Where will it break?** Five surprises, request walk-throughs, the deploy, and a symptom → cause → where-to-look table.
4. **How would we fix it?** Owner questions, in-flight branches and ordered next steps.

A revised pack opens with a semantic diff against the previous one: weakened contracts, new effects and lost enforcement first, because those are the changes a green build hides. The contracts-and-effects approach comes from Gavin Ray's post [Design by Contract and effects are essential for LLM-generated code](https://gavinray97.github.io/blog/design-by-contract-and-effects-for-llms).

It also runs **explain-back** sessions, in which the owner proves that understanding through a quiz or a narrated walk-through, and records weak spots for the next revision of the pack.

## Why

AI-assisted delivery produces working systems faster than their owners can absorb them. Green builds and passing tests don't tell you whether the tested rules run in production or whether a "Save" button saves anything. The pack makes Claude verify those claims in the code, cite every one as a clickable link, and label what nobody ever decided.

## Install

Clone the repository into your personal skills folder:

```bash
git clone https://github.com/AlexFielder/comp-pack.git ~/.claude/skills/comp-pack
```

On Windows (PowerShell):

```powershell
git clone https://github.com/AlexFielder/comp-pack.git "$env:USERPROFILE\.claude\skills\comp-pack"
```

To share it with a team, clone it into a project's `.claude/skills/comp-pack` instead.

## Use

In a Claude Code session opened on the repository you want to understand, ask for it in plain words:

- "Build a comp pack for this repo"
- "I don't understand what Claude built here, walk me through it"
- "Quiz me on this repo" (explain-back)

The skill writes the pack to `docs/comprehension/YYYY-MM-DD-comprehension-pass.md` and leaves it uncommitted, because the owner reading it is the point. Explain-back records go to `docs/comprehension/explain-back/`.

The build launches three or four parallel reader subagents, so a pack for a mid-sized web app takes one long session and a fair amount of tokens.

## What's in it

| File | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | The workflow: survey, readers, the two checks, verification, writing, reporting |
| [references/pack-template.md](references/pack-template.md) | The ten sections of a pack, in order |
| [references/reader-briefs.md](references/reader-briefs.md) | How to split the reading and the brief each reader subagent gets |
| [references/reference-format.md](references/reference-format.md) | The link contract that makes every citation clickable in GitHub, VS Code and the Claude desktop app |
| [references/explain-back.md](references/explain-back.md) | Quiz and walk-through sessions, scoring and the session record |
| [references/mempalace.md](references/mempalace.md) | Optional: filing a "start here" drawer into [MemPalace](https://github.com/MemPalace/mempalace) |
| [scripts/check_refs.py](scripts/check_refs.py) | Checks every link in a pack: bad targets, missing files, line numbers past the end of a file |

`check_refs.py` needs only Python 3:

```bash
python ~/.claude/skills/comp-pack/scripts/check_refs.py --show docs/comprehension/<pack>.md
```

## Licence

Public domain, under [the Unlicense](LICENSE).
