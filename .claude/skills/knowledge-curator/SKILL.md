---
name: knowledge-curator
description: >-
  Create or update a domain technical note in docs/knowledge/ (the project knowledge base):
  GPU virtualization, the SAM-Body4D pipeline, dev environment, mocap tools, research topics, etc.
  Use when capturing what was just learned/decided about a domain, adding a source excerpt, or when
  the user asks to start/update a knowledge doc. Enforces the template, full-URL citations, diagrams,
  the source-embedding pattern, the changelog, and refreshes the index via scripts/kb.py.
---

# Knowledge curator

Maintain `docs/knowledge/` to a consistent spec so both the user and future sessions can rely on it.

## When to invoke
- After substantively exploring or deciding something about a **domain** → create/update its doc.
- When the user says "make a knowledge doc / note", "add this source", "document X".
- One file per domain. Check `docs/knowledge/README.md` first; **update an existing doc** rather than duplicating.

## Procedure
1. **Locate or create the file.** `docs/knowledge/<slug>.md`. New docs start from `docs/knowledge/_TEMPLATE.md`.
2. **Front-matter block** (the `>` blockquote): Domain · `Status:` · `Last updated:` (today, absolute date) ·
   Maintainer · `Related:` links to sibling docs · a labeled `[[wikilink]]` demo line.
3. **Verification legend** on every non-trivial claim: `[V]` verbatim/observed · `[D]` documented (cited) ·
   `[I]` inference · `[M]` verify on-machine. Prefer `[V]`/`[D]`; never present `[I]` as fact.
4. **Citations (required style):** show the **full URL as the link text**, with a retrieved date —
   `<Title> · retrieved YYYY-MM-DD — [https://full/url](https://full/url)`. Never a bare domain.
5. **Diagrams:** author Graphviz under `docs/knowledge/assets/<topic>/<name>.dot`; render to **SVG** with
   `python scripts/kb.py render`; embed `![cap](assets/<topic>/<name>.svg)` **followed by a source/render block**:
   `**Diagram**` then `- **source:** [<name>.dot](assets/<topic>/<name>.dot)` and
   `- **render:** [<name>.svg](assets/<topic>/<name>.svg)`.
6. **Embedding source material** — choose per need (see `worked_example_source_embedding.md`):
   - *Source-excerpt callout* (blockquote + code fences) — portable, searchable. Default.
   - *Screenshot* — pixel-perfect original; image in `assets/<topic>/` (small → git; large → git-ignored + GCS).
   - *Raw HTML + inline CSS* — exact custom styling, **MkDocs-only**.
   - *monolith snapshot* — exact original CSS, offline: `python scripts/kb.py capture <url> [name]`
     → `sources/<name>.html` (git-ignored; link locally, iframe in MkDocs).
7. **Asset tiering:** diagrams/small images committed to git; large media + `sources/*.html` are git-ignored
   and mirrored to GCS (`python scripts/kb.py backup <bucket>`).
8. **Changelog:** append a dated bullet describing what changed and why. Update `Last updated:`.
9. **Cross-link** related docs both ways (the `Related:` line).
10. **Refresh + verify:** run `python scripts/kb.py build` (render + index + linkcheck) and fix any
    `BROKEN` links it reports. The README index table is auto-generated between its KB-INDEX markers — do
    not hand-edit it.

## Preview
The MkDocs site renders everything (incl. raw-HTML embeds and external-link highlighting):
`python -m mkdocs serve` → http://127.0.0.1:8000. Obsidian/Foam open the same files locally.

## Files
- Template: `docs/knowledge/_TEMPLATE.md` · Index: `docs/knowledge/README.md` (auto)
- Tool: `scripts/kb.py` (render / index / linkcheck / capture / backup / build)
- Conventions reference: `docs/knowledge/README.md` (Conventions section)
