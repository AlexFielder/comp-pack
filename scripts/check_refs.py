"""Check a comprehension pack's code references against the reference contract (version 2).

Usage: python check_refs.py [--show] <pack.md> [<pack.md> ...]

--show prints the first lines each line anchor points at, so you can eyeball that every
reference lands on the code it describes (readers' line numbers are sometimes off,
especially in JSON and YAML files).

For every Markdown link it reports:
  - targets that are neither relative (../..), a URL nor an in-page anchor (BAD-TARGET)
  - link text that doesn't match the target's repository path (TEXT-MISMATCH)
  - targets whose file or folder doesn't exist (MISSING)
  - line anchors beyond the end of the file (OUT-OF-RANGE)
It also lists bare `file.ext:line` mentions outside links (BARE), which usually need a link.
Exit code 1 if any BAD-TARGET, MISSING or OUT-OF-RANGE was found.
"""
import os
import re
import sys
from urllib.parse import unquote

LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
ANCHOR = re.compile(r"#L(\d+)(?:-L(\d+))?$")
BARE = re.compile(r"(?<![/\[\w.-])[\w.-]+\.(?:cs|razor|cshtml|ts|tsx|js|json|yml|yaml|ps1|sql|md|iss|csproj):\d+")


def check(pack: str, show: bool = False) -> int:
    base = os.path.dirname(os.path.abspath(pack))
    text = open(pack, encoding="utf-8").read()
    # Skip fenced code blocks: links there are examples, not references.
    stripped = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    problems, hard = [], 0
    line_counts = {}
    shown = set()
    for lineno, line in enumerate(stripped.splitlines(), 1):
        for label, target in LINK.findall(line):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not target.startswith("../"):
                problems.append(f"{lineno}: BAD-TARGET {target}")
                hard += 1
                continue
            m = ANCHOR.search(target)
            path_part = target[: m.start()] if m else target.split("#")[0]
            full = os.path.normpath(os.path.join(base, unquote(path_part)))
            if not os.path.exists(full):
                problems.append(f"{lineno}: MISSING {target}")
                hard += 1
                continue
            # Link text should be the repo path (+ :line). Compare the path part only.
            repo_path = re.sub(r"^(\.\./)+", "", unquote(path_part))
            text_path = label.split(":")[0].strip("` ")
            if "/" in text_path and text_path.rstrip("/") != repo_path.rstrip("/"):
                problems.append(f"{lineno}: TEXT-MISMATCH [{label}] -> {repo_path}")
            if m and os.path.isfile(full):
                if full not in line_counts:
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        line_counts[full] = sum(1 for _ in fh)
                end = int(m.group(2) or m.group(1))
                if end > line_counts[full]:
                    problems.append(f"{lineno}: OUT-OF-RANGE {target} (file has {line_counts[full]} lines)")
                    hard += 1
                elif show and target not in shown:
                    shown.add(target)
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        src = fh.read().splitlines()
                    start = int(m.group(1))
                    snippet = " | ".join(s.strip() for s in src[start - 1 : min(end, start + 2)])
                    problems.append(f"{lineno}: SHOW {repo_path}:{start}-{end}: {snippet[:160]}")
        no_links = LINK.sub("", line)
        for bare in BARE.findall(no_links):
            problems.append(f"{lineno}: BARE {bare}")
    links = len(LINK.findall(stripped))
    print(f"{pack}: {links} links, {len(problems)} notes, {hard} hard problems")
    for p in problems:
        print("  " + p)
    return hard


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    show = "--show" in args
    total = sum(check(p, show) for p in args if p != "--show")
    sys.exit(1 if total else 0)
