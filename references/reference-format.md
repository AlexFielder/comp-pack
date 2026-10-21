# Reference contract (version 2, 2026-10-21)

Comprehension packs cite code constantly, and those citations are only useful if a reader can open them in one click. Three consumers resolve them: the Claude desktop app's file pane, GitHub's Markdown renderer, and the "comp pack reader" VS Code extension. This contract is what all three rely on. Change it only together with the extension, and bump the version line.

Version 2 replaced version 1's root-relative targets (`/src/...`). The desktop app's file pane passes a leading-slash target through as an absolute path from the drive root, and VS Code without the extension resolves it against the workspace folder, which breaks when the open folder is a parent of the repository. All three consumers resolve a target relative to the Markdown file's own folder, so that is what the target now is.

## The form

```
[<path>](<up><path>)
[<path>:<line>](<up><path>#L<line>)
[<path>:<start>-<end>](<up><path>#L<start>-L<end>)
```

- `<path>` is relative to the **repository root**, with forward slashes and no leading `./` or `/`. That is the link text, so a reader always sees where the file lives in the repository.
- `<up>` climbs from the Markdown file's folder to the repository root. For a pack in `docs/comprehension/` it is always `../../`; for an explain-back record in `docs/comprehension/explain-back/` it is `../../../`.
- Line anchors use GitHub's form: `#L42`, `#L40-L55`. Lines are 1-based and refer to the commit pinned in the pack header.
- The link text and the target carry the same repository path. If they disagree, the target wins.

## Rules

1. **Full path every time.** No bare filenames (`Program.cs:131`), no "ibid.", no "same file". Three lines in one file are three links: `[src/A.cs:437](../../src/A.cs#L437), [src/A.cs:495](../../src/A.cs#L495)`.
2. **A range is one link**, not two: `[src/A.cs:58-92](../../src/A.cs#L58-L92)`.
3. **Folders** are linked without a line, with a trailing slash: `[src/Acme.Domain/Rules/](../../src/Acme.Domain/Rules/)`.
4. **Globs** (`src/Acme.Domain/Entities/*.cs`) are not links; write them in backticks and link the folder instead.
5. **Spaces and other reserved characters** in the target are percent-encoded (`%20`); the link text stays readable.
6. **Symbols** (a class or method name) go in backticks next to the link, not inside it: `` `OrderStore.Load` ([src/Acme.Web/Services/OrderStore.cs:58](../../src/Acme.Web/Services/OrderStore.cs#L58)) ``.
7. **No links inside Mermaid blocks or fenced code.** Name the file in the prose around the diagram.
8. **Another repository:** the full GitHub URL with a commit SHA or tag.
9. **Files that exist only on a branch** (§8 of a pack): the full GitHub URL with the branch name, because a relative link resolves against the checkout on disk.
10. **Line numbers drift.** The pack header pins the commit; a revision re-checks every line it keeps.

## Examples

Good (in a pack under `docs/comprehension/`):

```markdown
`OrderStore` loads every table once at start-up ([src/Acme.Web/Services/OrderStore.cs:58-92](../../src/Acme.Web/Services/OrderStore.cs#L58-L92)).
Pages "save" by appending to the cached lists ([src/Acme.Web/Components/Pages/Checkout.razor:437](../../src/Acme.Web/Components/Pages/Checkout.razor#L437), [src/Acme.Web/Components/Pages/Checkout.razor:495](../../src/Acme.Web/Components/Pages/Checkout.razor#L495)).
```

Bad, and why:

| Written | Problem |
|---|---|
| `` `Program.cs:131` `` | bare filename, and not a link |
| `[src/Acme.Web/Program.cs:131](/src/Acme.Web/Program.cs#L131)` | version 1 form: breaks in the desktop app and in VS Code opened on a parent folder |
| `[Program.cs:131](../../src/Acme.Web/Program.cs#L131)` | bare filename in the link text |
| `[src/A.cs:437, 495](../../src/A.cs#L437)` | two locations in one link |
| `(src/A.cs:58-92)` | plain text; nothing can open it |

## Opening packs

- **Claude desktop app:** the file pane opens only files inside the session's folders. Open the pack from a session whose working directory is the repository, or add the repository folder to the session.
- **VS Code:** relative links work from any open folder. The comp pack reader extension also reads version 1 targets, the desktop app's `path:42` form and legacy code spans, and flags missing files and out-of-range lines.
- **GitHub:** works as is, on the branch the pack is committed to.

## Checking a pack

From the repository root (PowerShell):

```powershell
$p = 'docs/comprehension/<pack>.md'
# targets that are neither pack-relative nor a URL nor an in-page anchor
Select-String -Path $p -Pattern '\]\((?!\.\./\.\./|https?://|#)'
# file:line written outside a link (read the hits; full paths in link text also match)
Select-String -Path $p -Pattern '(?<![/\[\w.-])[\w.-]+\.(cs|razor|cshtml|ts|tsx|js|json|yml|ps1|sql|md|iss):\d'
```

Then confirm every target exists: extract each `](../../<path>` and `Test-Path` it from `docs/comprehension/`.
