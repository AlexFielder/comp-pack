# Pack template

Ten sections, in this order. Aim for something the owner reads in about two hours with the code open beside it: roughly 300-450 lines of Markdown. Longer means you haven't decided what matters.

Every section answers one of the four questions (what should it do; how do we know; where does it break; how would we fix it). If a section doesn't help with one of them for this repository, keep the heading and write one line saying why it's short.

---

## Header

```markdown
# <System name> comprehension pass

**<Restriction line, only if one applies, e.g. "Client X's IP. Never copy this pack, or anything from it, into another repository or a shared notes folder.">**

YYYY-MM-DD · `<default branch>` at `<short SHA>` (version <x> if any) · <one clause on the checkout or branch situation>

This pack exists so that <owner> can answer four questions about <system> without asking Claude: **what should it do, how do we know it does that, where will it break, and how would we fix it.** Read it in order; it takes about <N> hours with the code open beside it. Every reference is a link whose text is the path from the repository root, pinned to the commit above.
```

Add one sentence of disambiguation if the name collides with something else (a product and an unrelated venture that share a name, say).

## 1. The system on one page

- One Mermaid `flowchart LR`: users, edge (Cloudflare, IIS, Vercel), processes, identity provider, data stores, external services, and the code areas that matter. Label edges with what crosses them. Mark the surprising edges (a dotted line for "only at start-up", a note for "not called").
- Then 4-6 bullets: how many deployable units, projects and what each holds, test projects and what they cover, environments with their hosts and branches. Cite each.

## 2. Five things that surprise everyone

Exactly five, ranked by consequence. These are the reason the pack exists; each must be verified by the main session, not just a reader.

For each, a `###` heading that states the surprise as a plain sentence ("Nothing a user enters is saved"), then bullets:
- **What happens:** the mechanism, with links.
- **Consequences:** what a user or operator experiences.
- **Plan of record** (if any): where the fix is planned, or "none".

Good surprises are things a competent person who had skimmed the README would get wrong. Always consider the results of the two checks (wired? saved?), access control as actually enforced versus as described, values that look calculated but are seeded or hard-coded, missing logging, and deploy steps that lose data. If the two checks come back clean, say so in a sentence at the top of this section; clean is a finding too.

## 3. The data model

- **Shape:** how many entities, how relationships work (navigation properties or string ids), delete behaviour.
- A table: area | entities | real-world meaning.
- A Mermaid `erDiagram` of the relationships a reader verified (not every entity; the ones that carry meaning).
- **Things to know before changing the model:** conventions that silently change columns, enum storage, temporal or history tables, unique indexes and check constraints, how seeding decides to run, where and when migrations run and what a failed one does, how to apply a script by hand.

## 4. The rules catalogue

One table. Columns: **Rule** (name plus link) | **In plain English** | **Source** | **Wired?**

- **Plain English:** what the rule decides, with the numbers, in words the owner would use. Use `<br/>` for short numbered steps inside a cell.
- **Source:** one of
  - *Owner's decision* (cite the answer, document, meeting or commit),
  - *Published standard* (cite the clause as the code or document states it),
  - *Prototype* or *Upstream port* (the rule came from earlier code, not a decision),
  - *Claude's assumption* (nobody decided it; Claude picked a value). Bold this one.
  Mixed sources are fine: "Bands: owner. Weights: prototype."
- **Wired?** **No**, or Yes with the caller's link. "Yes" without a caller is not allowed.

After the table, **gaps the tests don't cover**: edge cases where the rule's behaviour is undecided or surprising and no test pins it. These usually become owner questions.

## 5. Questions only the owner can answer

Numbered, each one sentence of context plus the question, each traceable to §4 or §2. Name the owner ("Questions only Sam can answer", "Questions for the client"). Order by how much of the system each answer unblocks. Ten to fifteen is typical; fewer is fine.

When the product owner and the operator differ (a client owns the rules and you run the servers; an upstream team owns a port), split the section into `5.1 For <product owner>` and `5.2 For <operator>`, numbering straight through, so each list can go to the person who answers it.

## 6. Three request walk-throughs

Pick three that together touch the most important code: usually one that writes, one that reads something computed, and one that crosses a trust boundary (sign-in, an external runner, a webhook). Open with one short paragraph on how every interaction travels (HTTP posts, SignalR circuit, long-poll, queue).

Each walk-through is a numbered list of hops; each hop has a bold label, what happens, and a link. End each with **Saved:** yes or no, and where.

## 7. Deployment, and where it breaks

- **The deploy:** trigger, runner, guards, numbered steps, what is backed up (files? database?), where secrets come from, app-pool or host settings.
- **Where it breaks:** a table, symptom | likely cause | look at. Write the symptom as the user or operator sees it ("HTTP 500.30 on every page", "sign-in loops"). Derive causes from the code, not from generic advice.
- **Smaller pipeline notes:** the bullets that didn't fit elsewhere.

## 8. In-flight work

What's open: pull requests, branches ahead of the default branch, worktrees. For each: one line on what it changes, its size (`git diff --shortstat`), and **what it fixes and doesn't fix from §2**. Read the diff of anything that touches a §2 surprise; list the rest. Links to branch-only files use full GitHub URLs.

## 9. Self-quiz

Ten questions, opened with: "Answer each one before opening it. If you can answer eight or more without looking, you own this system."

```markdown
<details><summary>1. A manager confirms an item, and the app pool recycles ten minutes later. What happens to the confirmation?</summary>

It's lost. ... ([src/...](../../src/...#L128-L129))
</details>
```

The blank line after `</summary>` matters: without it GitHub doesn't render the Markdown inside. Write questions as scenarios ("X happens; what does the user see?"), not definitions. Cover §2 (at least three), the data model, a walk-through, the deploy and one rule edge case. Every answer cites evidence. Explain-back sessions draw on these.

## 10. Next steps

One opening sentence that names the single biggest lever. Then an ordered list of what to do, each item tied to a §2 surprise or a §5 question. Estimates, if any, in attended hours.
