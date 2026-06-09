# Reading-Layer Bake-off — evaluate 4 ways to browse these docs

> Temporary evaluation guide. All four methods render the **same 3 canonical docs** in this folder
> ([GPU](windows_gpu_architecture_notes.md) · [Pipeline](sam_body4d_inference_pipeline.md) · [Dev env](dev_environment_and_data.md)).
> Do the **same 3 activities** in each, then score them in the table at the bottom.

## The 3 standardized activities
1. **Read rendered markdown** — headings, tables, the verification-legend callouts, code spans.
2. **View a rendered Graphviz PNG diagram** — e.g., the hardware stack in the GPU doc, the pipeline diagram.
3. **Navigate links** — (a) standard cross-doc links (the "Related" line at the top of each doc), and
   (b) the **`[[wikilink]]` demo** line just below it (native only in Obsidian/Foam).

---

## Method 1 — GitHub web
**Open:** push the branch, then browse `docs/knowledge/` on github.com (I'll give the exact URL once pushed).
**Do the activities:**
1. Open `README.md` / any doc — GitHub renders markdown, tables, and Mermaid blocks natively.
2. Diagrams: committed PNGs render inline. **Git-ignored large media shows a broken icon** (expected).
3. Standard `[text](other.md)` links navigate between files. **`[[wikilinks]]` render as literal text** (not supported).
**Watch for:** needs a push to see changes; no graph/backlinks; basic search; best for review/diffs, not study.

## Method 2 — Obsidian (recommended for local study)
**Setup (one-time):** install Obsidian (https://obsidian.md) → "Open folder as vault" → select
`C:\dev\projects\sam-body4d\docs\knowledge`. (Optional: install the **community plugin "Obsidian Git"** to auto-commit.)
**Do the activities:**
1. Click any note — live preview renders markdown, tables, callouts.
2. Diagrams: **all local PNGs render**, including git-ignored large media (files are on disk). Mermaid renders natively.
3. Both `[text](other.md)` **and** the `[[wikilink]]` demo navigate. Open **Graph view** (left ribbon) to see the doc network; hover for backlinks.
**Watch for:** separate app (free); use Graph + Backlinks panels — this is the main UX advantage.

## Method 3 — Foam (VS Code, open-source)
**Setup (one-time):** in VS Code, install extensions **Foam** (`foam.foam-vscode`) and **Markdown Preview Mermaid Support**
(`bierner.markdown-mermaid`). A `.vscode/extensions.json` in the repo will recommend these on open. Open the repo folder.
**Do the activities:**
1. Open a doc → `Ctrl+Shift+V` for Markdown preview (renders tables, images, and Mermaid via the extension).
2. Diagrams: local PNGs render in the preview (incl. git-ignored media).
3. `[[wikilinks]]` are first-class in Foam (Ctrl+click to follow, autocomplete to create); run **"Foam: Show Graph"** for the network. Standard `.md` links also work.
**Watch for:** stays inside VS Code where you run Claude Code; preview is slightly less polished than Obsidian; Mermaid needs the extra extension.

## Method 4 — MkDocs Material (local site)
**Open:** the site is already served — go to **http://127.0.0.1:8000** (run `mkdocs serve` from the repo root to restart).
**Do the activities:**
1. Polished themed pages with top nav + instant **search** (press `/`). Tables/admonitions styled.
2. Diagrams: committed PNGs render; git-ignored large media would render only if bundled at build time.
3. Standard `[text](other.md)` links are rewritten and navigate cleanly. **`[[wikilinks]]` render as literal text** unless a wikilink plugin is added.
**Watch for:** a build/serve toolchain to maintain; best when you want search + a shareable/deployable site.

---

## Scorecard (fill in your impressions)
| Capability | GitHub web | Obsidian | Foam (VS Code) | MkDocs Material |
|---|---|---|---|---|
| Setup cost | push only | install app | install 2 extensions | already running |
| Renders markdown/tables | ✅ | ✅ | ✅ | ✅ (prettiest) |
| Renders committed PNG diagrams | ✅ | ✅ | ✅ | ✅ |
| Renders git-ignored **local** large media | ❌ | ✅ | ✅ | ⚠️ build-bundle |
| Standard cross-doc links | ✅ | ✅ | ✅ | ✅ |
| `[[wikilinks]]` | ❌ literal | ✅ | ✅ | ⚠️ needs plugin |
| Backlinks / graph view | ❌ | ✅ | ✅ | ❌ |
| Full-text search | basic | ✅ | ✅ (editor) | ✅ |
| Offline | ❌ | ✅ | ✅ | ✅ (local) |
| Shareable/public | ✅ repo | ⚠️ paid Publish | ❌ | ✅ deploy |
| Your UX rating (1–5) |  |  |  |  |

**Reminder of my recommendation:** for your local-first, single-PC, large-media-stored-locally setup,
**Obsidian** (or **Foam** if you prefer staying in VS Code) is the best primary reader because it's the only
one that renders your git-ignored local media *and* gives graph/backlinks; **GitHub** stays the text/diff/backup
remote; **MkDocs** is the option to revisit if you ever want a searchable public site.
