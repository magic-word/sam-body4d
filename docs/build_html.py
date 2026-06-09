#!/usr/bin/env python3
"""Render a markdown file to a self-contained HTML doc with images inlined as base64.

Usage: python docs/build_html.py <input.md> <output.html>
Image paths in the markdown are resolved relative to the markdown file's directory,
read off disk, and embedded as data: URIs so the HTML works anywhere.
"""
import base64
import mimetypes
import os
import re
import sys

import markdown


def inline_images(html: str, base_dir: str) -> str:
    def repl(m):
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        path = os.path.normpath(os.path.join(base_dir, src))
        if not os.path.isfile(path):
            return m.group(0)
        mime = mimetypes.guess_type(path)[0] or "image/png"
        b64 = base64.b64encode(open(path, "rb").read()).decode("ascii")
        return f'src="data:{mime};base64,{b64}"'

    return re.sub(r'src="([^"]+)"', repl, html)


CSS = """
:root { color-scheme: light dark; }
body { max-width: 1100px; margin: 2rem auto; padding: 0 1.5rem;
  font: 16px/1.6 -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  color: #1b1f24; background: #fff; }
h1, h2, h3 { line-height: 1.25; }
h1 { border-bottom: 2px solid #e1e4e8; padding-bottom: .3em; }
h2 { border-bottom: 1px solid #e1e4e8; padding-bottom: .3em; margin-top: 2.2rem; }
code { background: #f3f4f6; padding: .15em .35em; border-radius: 4px;
  font: 13px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace; }
pre { background: #f6f8fa; padding: 1rem; border-radius: 8px; overflow-x: auto; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 14px; }
th, td { border: 1px solid #d0d7de; padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: #f6f8fa; }
blockquote { border-left: 4px solid #d0d7de; margin: 1rem 0; padding: .2rem 1rem; color: #57606a; }
img { max-width: 100%; height: auto; border: 1px solid #e1e4e8; border-radius: 8px;
  background: #fff; display: block; margin: 1rem auto; }
a { color: #0969da; }
hr { border: none; border-top: 1px solid #e1e4e8; margin: 2rem 0; }
"""


def main():
    src, out = sys.argv[1], sys.argv[2]
    base_dir = os.path.dirname(os.path.abspath(src))
    text = open(src, encoding="utf-8").read()
    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "toc", "sane_lists"]
    )
    body = inline_images(body, base_dir)
    title = os.path.splitext(os.path.basename(src))[0]
    html = (
        f"<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title><style>{CSS}</style></head><body>\n{body}\n</body></html>\n"
    )
    open(out, "w", encoding="utf-8").write(html)
    print(f"wrote {out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
