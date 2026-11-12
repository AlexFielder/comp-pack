"""Render a comprehension pack as a phone-friendly HTML page (for example a Claude Artifact).

usage: python build_pack_page.py <pack.md> <out.html> [--repo-url https://github.com/<owner>/<repo>] [--sha <commit>]

The Markdown pack stays the master copy; the page is a view of it. The page adds:
surprise cards, self-quiz questions that open on tap, tables that turn into labelled
cards on narrow screens, count tiles, a contents drawer, and light and dark themes.

Pack links follow the reference contract (targets relative to the pack's folder), which
break once the page is hosted elsewhere. So the script rewrites them to GitHub links pinned
to the commit in the pack's header. It finds the repository from `git remote get-url
origin` in the pack's checkout; pass --repo-url and --sha to override. Raw HTML in the pack
is shown as text, except <br>, <details> and <summary>, which packs use on purpose.

Needs Python 3.9+ and Python-Markdown 3.x (`pip install markdown`).
"""
import argparse
import html
import os
import re
import subprocess
import sys

import markdown

BR = "⟦BR⟧"


def git(cwd, *args):
    try:
        out = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def github_base(remote):
    m = re.match(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+)/(.+?)(?:\.git)?/?$", remote or "")
    return f"https://github.com/{m.group(1)}/{m.group(2)}" if m else ""


def make_md():
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])
    md.preprocessors.deregister("html_block")
    md.inlinePatterns.deregister("html")
    return md


def inline(md, text):
    out = md.reset().convert(text)
    return re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)


def rewrite_links(src, pack_path, repo_url, sha):
    """Relative link targets -> GitHub blob URLs at the pinned commit."""
    pack_dir = os.path.dirname(os.path.abspath(pack_path))
    top = git(pack_dir, "rev-parse", "--show-toplevel")
    if not top:
        return src, 0, "not a git checkout, so relative links stay as they are"
    repo_url = repo_url or github_base(git(top, "remote", "get-url", "origin"))
    if not repo_url:
        return src, 0, "no GitHub remote found (pass --repo-url), so relative links stay as they are"
    if not sha:
        m = re.search(r"at `([0-9a-f]{7,40})`", src)
        sha = m.group(1) if m else git(top, "rev-parse", "HEAD")
    sha = git(top, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}") or sha
    rel_dir = os.path.relpath(pack_dir, top)
    count = [0]

    def fix(m):
        target = m.group(1)
        path, _, frag = target.partition("#")
        full = os.path.normpath(os.path.join(rel_dir, path.replace("%20", " "))).replace(os.sep, "/")
        if full.startswith(".."):
            return m.group(0)
        count[0] += 1
        url = f"{repo_url}/blob/{sha}/{full.replace(' ', '%20')}" + (f"#{frag}" if frag else "")
        return f"]({url})"

    out = re.sub(r"\]\(((?!https?:|mailto:|#)[^)\s]+)\)", fix, src)
    return out, count[0], f"{repo_url} at {sha[:12]}"


def preprocess(src):
    """Turn the pack's structure into placeholders the Markdown pass leaves alone."""
    lines = src.replace("\r", "").split("\n")
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("# ") else "Comprehension pass"
    body = lines[1:] if lines and lines[0].startswith("# ") else lines
    out, blocks, section = [], [], ""
    in_card = False
    fence = False

    def close_card():
        nonlocal in_card
        if in_card:
            out.append("\n@@CARDCLOSE@@\n")
            in_card = False

    for line in body:
        if line.startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        h2 = re.match(r"^## (.*)$", line)
        if h2:
            close_card()
            section = h2.group(1)
            out.append(line)
            continue
        in_surprises = bool(re.match(r"^2\.?\s", section)) or "surprise" in section.lower()
        h3 = re.match(r"^### (S\d+\.?|2\.\d+\.?)\s+(.*)$", line)
        if h3 and in_surprises:
            close_card()
            blocks.append((h3.group(1).rstrip("."), h3.group(2)))
            out.append(f"\n@@CARDOPEN:{len(blocks) - 1}@@\n")
            in_card = True
            continue
        if line.startswith("#"):
            close_card()
            out.append(line)
            continue
        bs = re.match(r"^\*\*(S\d+)\.\s+(.+?)\*\*\s*(.*)$", line)
        if bs and in_surprises:
            close_card()
            blocks.append((bs.group(1), bs.group(2).rstrip(".")))
            out.append(f"\n@@CARDOPEN:{len(blocks) - 1}@@\n")
            out.append(bs.group(3))
            out.append("\n@@CARDCLOSE@@\n")
            continue
        if in_card and re.match(r"^\*\*Also worth knowing", line):
            close_card()
        d = re.match(r"^\s*<details>\s*<summary>(.*?)</summary>\s*$", line)
        if d:
            summary = d.group(1).strip()
            if re.fullmatch(r"(?i)(show\s+)?answers?", summary):
                k = len(out) - 1
                while k >= 0 and not out[k].strip():
                    k -= 1
                q = re.match(r"^\s*(\d+)[.)]\s+(.*)$", out[k]) if k >= 0 else None
                if q:
                    summary = f"{q.group(1)}. {q.group(2)}"
                    del out[k]
            blocks.append(("Q", summary))
            out.append(f"\n@@QOPEN:{len(blocks) - 1}@@\n")
            continue
        if re.match(r"^\s*</details>\s*$", line):
            out.append("\n@@QCLOSE@@\n")
            continue
        # Python-Markdown nests lists only at 4-space indents; packs often use 2.
        line = re.sub(r"^( +)(?=([-*+]|\d+[.)]) )", lambda m: m.group(1) * 2, line)
        out.append(re.sub(r"<br\s*/?>", BR, line))
    close_card()
    return title, "\n".join(out), blocks


def label_tables(doc):
    def one(m):
        t = m.group(0)
        heads = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)]

        def row(rm):
            k = [0]

            def cell(cm):
                lab = heads[k[0]] if k[0] < len(heads) else ""
                k[0] += 1
                content = cm.group(2)
                plain = re.sub(r"<[^>]+>", "", content).strip()
                if plain in ("No", "No caller", "Nothing", "Gap") and len(content) < 40:
                    content = f'<span class="pill bad">{plain}</span>'
                return f'<td{cm.group(1)} data-label="{html.escape(lab, quote=True)}">{content}</td>'

            return re.sub(r"<td([^>]*)>(.*?)</td>", cell, rm.group(0), flags=re.S)

        t = re.sub(r"<tr>.*?</tr>", row, t, flags=re.S)
        cls = "reflow" if len(heads) >= 3 else "small"
        return f'<div class="tablewrap"><table class="{cls}"' + t[len("<table"):] + "</div>"

    return re.sub(r"<table>.*?</table>", one, doc, flags=re.S)


def section_of(doc, pattern):
    m = re.search(r'<h2 id="([^"]+)">(' + pattern + r".*?)</h2>(.*?)(?=<h2 |\Z)", doc, re.S | re.I)
    return (m.group(1), m.group(3)) if m else ("", "")


def build(src, pack_path, repo_url=None, sha=None):
    src, nlinks, linkinfo = rewrite_links(src, pack_path, repo_url, sha)
    title, body, blocks = preprocess(src)
    md = make_md()
    doc = md.reset().convert(body)
    doc = doc.replace(BR, "<br>")
    doc = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>',
                 r'<div class="diagram"><pre class="mermaid">\1</pre></div>', doc, flags=re.S)
    doc = label_tables(doc)

    def card_open(m):
        sid, ttl = blocks[int(m.group(1))]
        return (f'<article class="surprise" id="{html.escape(sid.lower().replace(".", "-"))}">'
                f'<div class="sid">{html.escape(sid)}</div><h3 class="stitle">{inline(md, ttl)}</h3>')

    doc = re.sub(r"<p>@@CARDOPEN:(\d+)@@</p>", card_open, doc)
    doc = doc.replace("<p>@@CARDCLOSE@@</p>", "</article>")
    doc = re.sub(r"<p>@@QOPEN:(\d+)@@</p>",
                 lambda m: f'<details class="quiz"><summary>{inline(md, re.sub(r"^(\d+)\.", r"\1\\.", blocks[int(m.group(1))][1]))}</summary><div class="ans">', doc)
    doc = doc.replace("<p>@@QCLOSE@@</p>", "</div></details>")
    doc = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', doc)

    # Header: everything before the first <h2> or <hr> is the pack's front matter.
    cut = min([i for i in (doc.find("<h2"), doc.find("<hr")) if i >= 0] or [len(doc)])
    front, rest = doc[:cut], doc[cut:]
    if rest.startswith("<hr />"):
        rest = rest[len("<hr />"):]
    restriction = ""
    rm = re.match(r"\s*<p><strong>([^<]*?[^:<])</strong></p>", front)
    if rm:
        restriction = rm.group(1)
        front = front[rm.end():]
        front = f'<div class="restrict" role="note"><b>Restricted.</b> {rm.group(1)}</div>' + front

    toc = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', rest)
    toc_html = "".join(f'<li><a href="#{a}">{re.sub(r"<[^>]+>", "", t)}</a></li>' for a, t in toc)

    n_surprise = sum(1 for b in blocks if b[0] != "Q")
    n_quiz = sum(1 for b in blocks if b[0] == "Q")
    s_id, _ = section_of(rest, r"2\.")
    r_id, r_body = section_of(rest, r"4\.")
    first_table = re.search(r"<tbody>(.*?)</tbody>", r_body, re.S)
    n_rules = len(re.findall(r"<tr>", first_table.group(1))) if first_table else 0
    q_id, q_body = section_of(rest, r"5\.")
    # Packs with a register cite OQ IDs; older packs just number their questions.
    n_oq = len(set(re.findall(r"\bOQ-\d{3}\b", q_body))) or len(re.findall(r"<li>", q_body))
    z_id, _ = section_of(rest, r"9\.")
    tiles = []
    for n, label, anchor in ((n_surprise, "Surprises", s_id), (n_rules, "Rules", r_id),
                             (n_oq, "Owner questions", q_id), (n_quiz, "Quiz questions", z_id)):
        if n:
            tiles.append(f'<a class="tile" href="#{anchor}"><b>{n}</b><span>{label}</span></a>')

    m = re.match(r"^(.*?)(?:,\s*(\d{4}-\d{2}-\d{2}))?$", title)
    name = re.sub(r"\s+comprehension pass$", "", m.group(1), flags=re.I).strip() or title
    when = m.group(2) or (re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(pack_path)) or [""])[0]
    short = f"{name.split(' (')[0]} comp pack {when}".strip()

    page = TEMPLATE
    for k, v in {
        "%%PAGE_TITLE%%": html.escape(short), "%%SHORT%%": html.escape(short), "%%NAME%%": html.escape(name),
        "%%WHEN%%": html.escape(when), "%%TILES%%": "".join(tiles), "%%TOC%%": toc_html,
        "%%FRONT%%": front, "%%DOC%%": rest,
    }.items():
        page = page.replace(k, v)
    stats = {"surprises": n_surprise, "rules": n_rules, "owner_questions": n_oq, "quiz": n_quiz,
             "links_rewritten": nlinks, "links": linkinfo, "restriction": restriction or None}
    return page, stats


TEMPLATE = """<title>%%PAGE_TITLE%%</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">
<style>
/* Layout: one reading column; surprises and quiz answers as cards; tables reflow to labelled cards under 680px. */
:root {
  --bg: #f5f5f2; --surface: #ffffff; --sunk: #ecece7; --fg: #1c1f24; --fg2: #464b53; --muted: #6d727a;
  --line: #dcdcd5; --accent: #1f6b5c; --accent-bg: #e2f0ec; --warn: #8a4b00; --warn-bg: #fbeed8;
  --bad: #a8261b; --bad-bg: #fbe6e3;
  --sans: "IBM Plex Sans", "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #121412; --surface: #1a1d1b; --sunk: #242825; --fg: #e7e9e6; --fg2: #c4c8c3; --muted: #8f958f;
  --line: #2e332f; --accent: #7fcfb9; --accent-bg: #173029; --warn: #f0bd6a; --warn-bg: #33270f;
  --bad: #ff9b90; --bad-bg: #3a1714; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #121412; --surface: #1a1d1b; --sunk: #242825; --fg: #e7e9e6; --fg2: #c4c8c3; --muted: #8f958f;
  --line: #2e332f; --accent: #7fcfb9; --accent-bg: #173029; --warn: #f0bd6a; --warn-bg: #33270f;
  --bad: #ff9b90; --bad-bg: #3a1714; color-scheme: dark; }
html { scroll-padding-top: calc(env(safe-area-inset-top, 0px) + 64px); }
body { background: var(--bg); color: var(--fg); font: 16px/1.6 var(--sans); -webkit-text-size-adjust: 100%; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--surface); }
.wrap { max-width: 820px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 0 72px; }
a { color: var(--accent); text-underline-offset: 2px; }
a:focus-visible, button:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
code { font: 500 0.86em var(--mono); background: var(--sunk); padding: 1px 5px; border-radius: 4px; overflow-wrap: anywhere; }
p, li, td { overflow-wrap: anywhere; }

.bar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 9; background: var(--surface); border-bottom: 1px solid var(--line); }
.bar .in { max-width: 820px; margin: 0 auto; display: flex; align-items: center; gap: 10px; min-height: 52px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.bar .nm { flex: 1; min-width: 0; font-weight: 600; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.btn { font: 600 14px var(--sans); color: var(--fg); background: var(--sunk); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px; cursor: pointer; text-decoration: none; }
.toc { border-top: 1px solid var(--line); background: var(--surface); max-height: 70vh; overflow-y: auto; }
.toc ol { max-width: 820px; margin: 0 auto; list-style: none; padding-block: 6px 12px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.toc a { display: block; padding: 10px 0; border-bottom: 1px solid var(--line); text-decoration: none; color: var(--fg); }

.hero { padding-block: 28px 4px; }
.eyebrow { font: 600 12px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
.hero h1 { font-size: clamp(26px, 6vw, 36px); line-height: 1.15; margin: 6px 0 4px; text-wrap: balance; letter-spacing: -.01em; }
.hero .when { color: var(--fg2); font-variant-numeric: tabular-nums; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; margin: 18px 0 6px; }
.tile { text-decoration: none; border-radius: 10px; padding: 10px 8px; border: 1px solid var(--line); background: var(--surface); color: var(--fg); }
.tile b { display: block; font-size: 24px; line-height: 1.1; color: var(--accent); font-variant-numeric: tabular-nums; }
.tile span { font-size: 12px; color: var(--fg2); }
.front { font-size: 15px; color: var(--fg2); }
.front p { margin: 10px 0; }
.restrict { background: var(--warn-bg); color: var(--warn); border-radius: 10px; padding: 10px 12px; margin: 14px 0; font-weight: 500; }

h2 { font-size: 22px; line-height: 1.25; margin: 40px 0 12px; padding-top: 14px; border-top: 2px solid var(--fg); text-wrap: balance; }
h3 { font-size: 18px; margin: 28px 0 8px; text-wrap: balance; }
.content > p, .content > ul, .content > ol { max-width: 68ch; }
.content ul, .content ol { padding-left: 1.3em; }
.content li { margin: 4px 0; }

.pill { display: inline-block; font: 600 12px/1 var(--sans); padding: 5px 8px; border-radius: 999px; white-space: nowrap; }
.pill.bad { color: var(--bad); background: var(--bad-bg); }

.surprise { background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--bad); border-radius: 10px; padding: 12px 16px 6px; margin: 14px 0; }
.surprise .sid { font: 600 13px var(--mono); color: var(--bad); }
.surprise .stitle { font-size: 18px; line-height: 1.35; margin: 4px 0 8px; }
.surprise ul { padding-left: 1.2em; }

details.quiz { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; margin: 10px 0; }
details.quiz > summary { cursor: pointer; padding: 12px 14px; font-weight: 600; list-style: none; display: flex; gap: 10px; }
details.quiz > summary::-webkit-details-marker { display: none; }
details.quiz > summary::before { content: "Show"; flex: none; font: 600 11px/1 var(--mono); text-transform: uppercase; letter-spacing: .06em;
  color: var(--accent); background: var(--accent-bg); border-radius: 6px; padding: 6px 7px; height: fit-content; margin-top: 2px; }
details.quiz[open] > summary::before { content: "Hide"; }
details.quiz .ans { padding: 0 14px 10px; border-top: 1px dashed var(--line); }

.tablewrap { overflow-x: auto; margin: 12px 0 18px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; vertical-align: top; padding: 9px 12px; border-bottom: 1px solid var(--line); }
th { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); background: var(--sunk); }
tr:last-child td { border-bottom: 0; }
@media (max-width: 680px) {
  .tablewrap { overflow: visible; border: 0; background: none; }
  table.reflow thead { display: none; }
  table.reflow, table.reflow tbody, table.reflow tr, table.reflow td { display: block; width: 100%; }
  table.reflow tr { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 8px 12px; margin-bottom: 10px; }
  table.reflow td { display: grid; grid-template-columns: minmax(80px, 30%) minmax(0, 1fr); gap: 10px; padding: 5px 0; border-bottom: 1px dashed var(--line); }
  table.reflow td:last-child { border-bottom: 0; }
  table.reflow td::before { content: attr(data-label); font-size: 12px; color: var(--muted); padding-top: 2px; }
  table.reflow td:first-child { font-weight: 600; }
}
.diagram { overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 12px; margin: 12px 0; }
pre { overflow-x: auto; font: 13px/1.5 var(--mono); }
hr { border: 0; border-top: 1px solid var(--line); margin: 24px 0; }
.totop { position: fixed; right: max(16px, env(safe-area-inset-right, 0px)); bottom: calc(16px + env(safe-area-inset-bottom, 0px)); z-index: 8; box-shadow: 0 2px 10px rgba(0,0,0,.18); }
@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
</style>

<header class="bar">
  <div class="in">
    <span class="nm">%%SHORT%%</span>
    <button type="button" class="btn" id="tocbtn" aria-expanded="false" aria-controls="toc">Contents</button>
  </div>
  <nav class="toc" id="toc" hidden aria-label="Contents"><ol>%%TOC%%</ol></nav>
</header>

<main class="wrap">
  <section class="hero" id="top">
    <div class="eyebrow">Comprehension pack</div>
    <h1>%%NAME%%</h1>
    <div class="when">%%WHEN%%</div>
    <div class="tiles">%%TILES%%</div>
    <div class="front">%%FRONT%%</div>
  </section>
  <div class="content">%%DOC%%</div>
</main>
<a class="btn totop" href="#top" aria-label="Back to top">Top</a>

<script>
(() => {
  const btn = document.getElementById("tocbtn"), toc = document.getElementById("toc");
  btn.addEventListener("click", () => { toc.hidden = !toc.hidden; btn.setAttribute("aria-expanded", String(!toc.hidden)); });
  toc.addEventListener("click", (e) => { if (e.target.closest("a")) { toc.hidden = true; btn.setAttribute("aria-expanded", "false"); } });
})();
</script>
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render a comprehension pack as a phone-friendly HTML page.")
    ap.add_argument("pack")
    ap.add_argument("out")
    ap.add_argument("--repo-url", help="https://github.com/<owner>/<repo> (default: the pack checkout's origin)")
    ap.add_argument("--sha", help="commit to pin links to (default: the one named in the pack's header)")
    a = ap.parse_args()
    with open(a.pack, encoding="utf-8") as f:
        page, stats = build(f.read(), a.pack, a.repo_url, a.sha)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page)
    for k, v in stats.items():
        print(f"{k}: {v}")
    if stats["restriction"]:
        print("WARNING: the pack carries a restriction line; check it allows hosting before publishing.", file=sys.stderr)
