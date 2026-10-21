# Explain-back

A pack nobody can explain back is a document, not understanding. Explain-back sessions are where the owner proves, in their own words, that they can answer the four questions, and where Claude finds the parts the pack failed to teach. If you bill review time, the session is billable work: log it under the repository's project like any other.

Be a coach, not an examiner. The goal is that the owner leaves knowing more than they arrived with, and that the next pack revision fixes whatever didn't land.

## Set-up

1. Find the newest pack in `docs/comprehension/` and every earlier record in `docs/comprehension/explain-back/`. If there's no pack, say so and offer to build one first; explain-back without a pack turns into Claude lecturing.
2. Check drift: `git log --oneline <pack SHA>..origin/<default> -- <paths the pack cites most>`. If cited code has changed, say which sections may be stale before you start, and verify any answer that depends on them against the current code.
3. Ask which mode, unless the owner already said:
   - **Quiz** (about 30-45 minutes): ten questions.
   - **Walk-through** (about 20-30 minutes per flow): the owner narrates a named flow end to end.
   - **Both**: the quiz first, then one walk-through chosen from the quiz's weakest area.

## Quiz mode

**Choosing questions.** Ten, in this priority:
1. Weak spots recorded in earlier sessions that haven't been answered Solid since (up to four).
2. The pack's §9 self-quiz questions not asked in the last session, but **reworded as a fresh scenario** so a memorised answer doesn't pass. ("A manager confirms an item and the pool recycles" becomes "Two users edit the same project and then a deploy runs: what survives?")
3. One or two §5 owner questions, framed as "What does the code do today about X, and who has to decide it?"
4. At least one new question from §2 or §4 that the pack didn't quiz.

Cover at least three of the four questions (what, how we know, where it breaks, how to fix).

**Asking.** One question at a time. Never show the answer, the options or the pack text before the owner answers. If the owner asks to look something up, that's fine; note it ("answered with the pack open") and score Partial at most.

**Scoring each answer.**

| Score | Meaning |
|---|---|
| **Solid (2)** | Right, in their own words, and they can say how they know (the file, the test, the behaviour). |
| **Partial (1)** | Right outcome but wrong or missing mechanism, or right with the pack open. |
| **Missed (0)** | Wrong, or "I don't know". |

Ask "how do you know?" when an answer is right but bare; a correct guess isn't understanding.

**Correcting.** After every answer, Partial or Missed especially: state the correct answer in two or three sentences and cite the evidence as reference-contract links ([references/reference-format.md](reference-format.md)). Open the cited lines yourself before quoting them; the pack can be wrong. If the pack *was* wrong or stale, say so, score the owner's answer on the code as it is, and record a **pack defect** rather than a weak spot.

## Walk-through mode

1. The owner names a flow ("a tenant submits a job and downloads the DXF") or picks one of the pack's §6 walk-throughs.
2. They narrate it hop by hop, from the user's action to the durable write and back. Don't interrupt mid-hop; let them finish each hop.
3. After each hop, confirm or correct with a link. Note hops they skip ("you went from the form straight to the database; what checks the tenant in between?").
4. End with the two checks applied to their flow: **Is the rule they described actually called here? Is the thing they described actually saved?**
5. Score the flow: Solid if every hop was right and none skipped, Partial if one or two hops were wrong or missing, Missed if the shape was wrong.

## Recording the session

Write `docs/comprehension/explain-back/YYYY-MM-DD-explain-back.md` in the target repository (add `-2` for a second session the same day). Leave it uncommitted unless the owner says otherwise. If the repository carries a confidentiality restriction, the record stays in that repository only.

```markdown
# Explain-back, YYYY-MM-DD

Pack: [docs/comprehension/YYYY-MM-DD-comprehension-pass.md](../YYYY-MM-DD-comprehension-pass.md) (`<SHA>`) · Mode: quiz | walk-through | both · Attended time: <start>-<end>

**Score: <points>/<max> (<percent>%).** <One sentence: owns it (80%+), getting there (50-79%), or not yet (under 50%).>

| # | Question (as asked) | Score | Correction and evidence |
|---|---|---|---|
| 1 | ... | Solid | — |
| 2 | ... | Missed | <two sentences> ([src/...](../../../src/...#L..)) |

## Weak spots
- <Topic>: <what the owner believed versus what is true>. Pack section: §<n>. Suggested pack change: <expand, add a diagram, add a walk-through, add a quiz question>.

## Pack defects
- <Where the pack was wrong or stale, with the correct evidence.>

## Next session
- <The two or three things to ask first next time.>
```

Then, if MemPalace is available, add one drawer to the repository's wing in room `comprehension` (see [mempalace.md](mempalace.md)) holding the date, score, weak spots and pack defects, so the next session on the repository knows where the owner is shaky.

## Feeding the next revision

When the pack is next revised (see SKILL.md, survey step), read every explain-back record. Each weak spot either gets a clearer explanation, a diagram or an extra walk-through in the section it names, plus a new quiz question; each pack defect gets fixed. Mention in the revised pack's header which sessions it absorbed.
