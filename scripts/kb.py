#!/usr/bin/env python3
"""kb.py — deterministic maintenance for the docs/knowledge/ knowledge base.

No LLM. Safe to run by hand or from a hook. Subcommands:

  render             Render every docs/knowledge/assets/**/*.dot -> sibling .png (Graphviz).
  index              Rebuild the index table in docs/knowledge/README.md (between KB-INDEX markers).
  linkcheck          Verify every local (relative) markdown link/image target exists. Exit 1 if broken.
  capture <url> [name]   Snapshot a web page to docs/knowledge/sources/<name>.html (monolith, JS stripped).
  backup [bucket]    rsync docs/knowledge/assets + sources to gs://<bucket>/ (needs gcloud). No-op w/o bucket.
  build              render + index + linkcheck (the standard refresh; use after edits / from a hook).

Binary discovery works on PATH or common winget install locations on Windows.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(ROOT, "docs", "knowledge")
ASSETS = os.path.join(KB, "assets")
SOURCES = os.path.join(KB, "sources")
README = os.path.join(KB, "README.md")
INDEX_START = "<!-- KB-INDEX:START -->"
INDEX_END = "<!-- KB-INDEX:END -->"
# Docs excluded from the auto-index and from linkcheck (templates / example-laden meta pages).
INDEX_SKIP = {"README.md", "_TEMPLATE.md"}
LINKCHECK_SKIP = {"_TEMPLATE.md", "README.md"}


def _find_binary(name: str, winget_glob: str | None = None) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    candidates = []
    if name == "dot":
        candidates.append(r"C:\Program Files\Graphviz\bin\dot.exe")
    if winget_glob:
        local = os.environ.get("LOCALAPPDATA", "")
        candidates += glob.glob(os.path.join(local, "Microsoft", "WinGet", "Packages", winget_glob))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def cmd_render() -> int:
    dot = _find_binary("dot")
    if not dot:
        print("[render] ERROR: Graphviz 'dot' not found (PATH or C:\\Program Files\\Graphviz\\bin).")
        return 1
    dots = sorted(glob.glob(os.path.join(ASSETS, "**", "*.dot"), recursive=True))
    if not dots:
        print("[render] no .dot files under", ASSETS)
        return 0
    rc = 0
    for d in dots:
        svg = os.path.splitext(d)[0] + ".svg"
        r = subprocess.run([dot, "-Tsvg", d, "-o", svg])
        status = "ok" if r.returncode == 0 else "FAIL"
        if r.returncode != 0:
            rc = 1
        print(f"[render] {status}: {os.path.relpath(svg, ROOT)}")
    return rc


def _doc_meta(path: str) -> tuple[str, str, str]:
    text = open(path, encoding="utf-8").read()
    title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), os.path.basename(path))
    m_status = re.search(r"\*\*Status:\*\*\s*([A-Za-z]+)", text)
    m_upd = re.search(r"Last updated:\*\*\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
    return title, (m_status.group(1) if m_status else "—"), (m_upd.group(1) if m_upd else "—")


def cmd_index() -> int:
    docs = sorted(
        p for p in glob.glob(os.path.join(KB, "*.md"))
        if os.path.basename(p) not in INDEX_SKIP
    )
    rows = ["| Doc | Status | Updated |", "|---|---|---|"]
    for p in docs:
        title, status, updated = _doc_meta(p)
        rows.append(f"| [{title}]({os.path.basename(p)}) | {status} | {updated} |")
    table = "\n".join(rows)
    readme = open(README, encoding="utf-8").read()
    if INDEX_START not in readme or INDEX_END not in readme:
        print(f"[index] ERROR: markers {INDEX_START} / {INDEX_END} not found in README.md")
        return 1
    new = re.sub(
        re.escape(INDEX_START) + r".*?" + re.escape(INDEX_END),
        INDEX_START + "\n" + table + "\n" + INDEX_END,
        readme,
        flags=re.DOTALL,
    )
    open(README, "w", encoding="utf-8").write(new)
    print(f"[index] rebuilt index with {len(docs)} docs")
    return 0


_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def cmd_linkcheck() -> int:
    broken = []
    checked = 0
    for p in sorted(glob.glob(os.path.join(KB, "**", "*.md"), recursive=True)):
        if os.path.basename(p) in LINKCHECK_SKIP:
            continue
        base = os.path.dirname(p)
        content = open(p, encoding="utf-8").read()
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)  # drop fenced code blocks
        content = re.sub(r"`[^`]*`", "", content)                      # drop inline code spans
        for m in _LINK_RE.finditer(content):
            target = m.group(1).strip().split(" ")[0]  # drop optional "title"
            if target.startswith(("http://", "https://", "mailto:", "tel:", "#")) or "://" in target:
                continue
            target = target.split("#")[0]
            if not target:
                continue
            checked += 1
            if not os.path.exists(os.path.normpath(os.path.join(base, target))):
                broken.append(f"{os.path.relpath(p, ROOT)} -> {target}")
    print(f"[linkcheck] checked {checked} local links")
    for b in broken:
        print(f"[linkcheck] BROKEN: {b}")
    return 1 if broken else 0


def cmd_capture(args: list[str]) -> int:
    if not args:
        print("[capture] usage: kb.py capture <url> [name]")
        return 1
    url = args[0]
    name = args[1] if len(args) > 1 else re.sub(r"[^a-z0-9]+", "_", url.split("//")[-1].lower()).strip("_")[:80]
    mono = _find_binary("monolith", os.path.join("Y2Z.Monolith_*", "monolith.exe"))
    if not mono:
        print("[capture] ERROR: monolith not found (install: winget install Y2Z.Monolith).")
        return 1
    os.makedirs(SOURCES, exist_ok=True)
    out = os.path.join(SOURCES, name + ".html")
    # NOTE: this monolith build's -o flag is buggy on Windows; capture stdout to file ourselves.
    r = subprocess.run([mono, "-j", url], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        print(f"[capture] FAILED for {url}")
        return 1
    open(out, "wb").write(r.stdout)
    print(f"[capture] wrote {os.path.relpath(out, ROOT)} ({len(r.stdout)//1024} KB) — git-ignored; back up to GCS.")
    return 0


def cmd_backup(args: list[str]) -> int:
    bucket = args[0] if args else os.environ.get("KB_GCS_BUCKET", "")
    if not bucket:
        print("[backup] no bucket given (arg or KB_GCS_BUCKET). Skipping. "
              "Once set: gcloud storage rsync docs/knowledge/assets gs://<bucket>/assets")
        return 0
    gcloud = shutil.which("gcloud")
    if not gcloud:
        print("[backup] ERROR: gcloud not found.")
        return 1
    rc = 0
    for sub in ("assets", "sources"):
        src = os.path.join(KB, sub)
        if os.path.isdir(src):
            r = subprocess.run([gcloud, "storage", "rsync", "-r", src, f"gs://{bucket}/{sub}"])
            rc = rc or r.returncode
    return rc


def cmd_build() -> int:
    rc = cmd_render()
    rc = cmd_index() or rc
    rc = cmd_linkcheck() or rc
    return rc


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd, rest = sys.argv[1], sys.argv[2:]
    dispatch = {
        "render": lambda: cmd_render(),
        "index": lambda: cmd_index(),
        "linkcheck": lambda: cmd_linkcheck(),
        "capture": lambda: cmd_capture(rest),
        "backup": lambda: cmd_backup(rest),
        "build": lambda: cmd_build(),
    }
    if cmd not in dispatch:
        print(__doc__)
        return 1
    return dispatch[cmd]()


if __name__ == "__main__":
    raise SystemExit(main())
