# Worked example — embedding source material alongside your notes

> **Purpose:** show the same critical source excerpt (NVIDIA CUDA-on-Windows install guide, §4.1
> Prerequisites) in **three representations**, each wrapped with our analysis, so you can see how each
> renders across GitHub / Obsidian / Foam / MkDocs and pick the habit you like.
> **Source page:** https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html · retrieved 2026-06-08
> **Related:** [Windows GPU architecture](windows_gpu_architecture_notes.md)

The pattern in every case: **your note above → the source excerpt → your analysis below.**

---

## Representation 1 — "Source excerpt" callout (portable: renders in all 4 readers)

**My note:** Before the CUDA *wheels* will install on Windows you must bootstrap NVIDIA's private
package index (`nvidia-pyindex`). This is the prerequisite the rest of the wheel install depends on.

> **Source — NVIDIA CUDA Installation Guide (Windows), §4.1 Prerequisites** · retrieved 2026-06-08
> [https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html](https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html)
>
> To install Wheels, you must first install the `nvidia-pyindex` package, which is required in order to
> set up your pip installation to fetch additional Python modules from the NVIDIA NGC PyPI repo. If your
> pip and setuptools Python modules are not up-to-date, then use the following command to upgrade these
> Python modules. If these Python modules are out-of-date then the commands which follow later in this
> section may fail.
>
> ```bat
> py -m pip install --upgrade setuptools pip wheel
> ```
>
> You should now be able to install the `nvidia-pyindex` module.
>
> ```bat
> py -m pip install nvidia-pyindex
> ```
>
> If your project is using a `requirements.txt` file, then you can add the following line to your
> `requirements.txt` file as an alternative to installing the `nvidia-pyindex` package:
>
> ```text
> --extra-index-url https://pypi.ngc.nvidia.com
> ```

**Our analysis:** the `--extra-index-url https://pypi.ngc.nvidia.com` line is the load-bearing part — it
points pip at NVIDIA's NGC index so `nvidia-*` wheels resolve. For our WSL2 Linux pipeline this Windows
wheel path is *not* what we use (we install `torch` from the PyTorch cu128 index instead), but it's the
canonical reference for the native-Windows CUDA-wheel route.

*Renders:* ✅ GitHub · ✅ Obsidian · ✅ Foam · ✅ MkDocs. Text is **searchable and selectable**; commands
are real code blocks. Styling is **your reader's theme, not NVIDIA's**. Fancier callouts exist but aren't
portable (Obsidian `> [!quote]`, Material `!!! quote`), so a plain blockquote is the safe lowest common denominator.

---

## Representation 2 — Screenshot (pixel-perfect *original* styling; an image)

**My note:** when the exact visual matters for memory, drop the literal capture next to the text.

![NVIDIA §4.1 Prerequisites — exact source styling](assets/cuda/nvidia_prereq_4_1.png)

> ⚠️ **Action for you:** save the screenshot you pasted in chat to
> `docs/knowledge/assets/cuda/nvidia_prereq_4_1.png` and this image renders (it'll show a broken icon
> until you do). It's *your* capture, so it's pixel-perfect by definition.

**Our analysis:** this is the only representation that reproduces NVIDIA's **exact fonts, colors, and
syntax highlighting**, because it's a literal pixel snapshot.

*Renders:* ✅ all four (once the file exists locally). **Not** searchable/selectable (it's an image),
and large captures go to the local `assets/` + GCS backup per our asset policy.

---

## Representation 3 — Raw HTML + inline CSS (exact *custom* styling; MkDocs-only)

**My note:** markdown can also carry literal HTML, so you *can* hand-style an excerpt — but only an
HTML renderer honors it.

<div style="background:#ffffff;color:#1c1c1c;border:1px solid #e1e4e8;border-radius:6px;padding:16px 20px;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.6;max-width:900px">
  <h3 style="color:#9ccc2f;font-weight:400;margin:.2em 0 .6em;font-size:1.5em">4.1. Prerequisites</h3>
  <p style="margin:.4em 0">To install Wheels, you must first install the <code style="color:#d6336c;font-family:ui-monospace,Consolas,monospace">nvidia-pyindex</code> package, which is required in order to set up your pip installation to fetch additional Python modules from the NVIDIA NGC PyPI repo.</p>
  <pre style="font-family:ui-monospace,Consolas,monospace;margin:.6em 0"><span style="color:#2aa198">py</span> <span style="color:#6c71c4">-m</span> pip install <span style="color:#6c71c4">--upgrade</span> setuptools pip wheel</pre>
  <p style="margin:.4em 0">You should now be able to install the <code style="color:#d6336c;font-family:ui-monospace,Consolas,monospace">nvidia-pyindex</code> module.</p>
  <pre style="font-family:ui-monospace,Consolas,monospace;margin:.6em 0"><span style="color:#2aa198">py</span> <span style="color:#6c71c4">-m</span> pip install nvidia-pyindex</pre>
  <p style="margin:.4em 0">If your project is using a <code style="color:#d6336c;font-family:ui-monospace,Consolas,monospace">requirements.txt</code> file, you can add this line instead:</p>
  <pre style="font-family:ui-monospace,Consolas,monospace;margin:.6em 0"><span style="color:#6c71c4">--extra-index-url</span> https://pypi.ngc.nvidia.com</pre>
</div>

**Our analysis / honest caveat:** the CSS above is **mine, approximating** NVIDIA's look — it is *not*
their actual stylesheet. To reproduce the **original's** exact CSS you'd capture a **single-file HTML
snapshot** of the page (SingleFile extension / `monolith` CLI) and embed/link that.

*Renders:* ✅ **MkDocs** (styled — see it live at http://127.0.0.1:8000) · ⚠️ Obsidian (renders most
inline HTML) · ❌ GitHub (strips `style`/`class`, falls back to plain text) · ⚠️ Foam/VS Code preview (partial).

---

## Representation 4 — Single-file HTML snapshot (`monolith`; exact *original* CSS, offline)

**My note:** captured with `monolith -j <url>` → one ~8.5 MB **self-contained** file (NVIDIA's real CSS,
fonts, and images inlined as `data:` URIs; JS stripped). This is NVIDIA's *actual* stylesheet, frozen
2026-06-08 — the thing Representation 3 could only approximate. Text stays selectable/searchable.

- **Open the snapshot:** [nvidia_cuda_windows_install_guide.html](sources/nvidia_cuda_windows_install_guide.html) — opens offline with original styling intact.

Live embed (MkDocs renders the iframe; other readers use the link above):

<iframe src="../sources/nvidia_cuda_windows_install_guide.html" title="NVIDIA CUDA Windows install guide (monolith snapshot)" style="width:100%;height:520px;border:1px solid #ccc;border-radius:6px"></iframe>

**Our analysis / caveats:** gold standard for fidelity **and** searchability — but the file is large
(8.5 MB), so it's stored locally + mirrored to GCS and **git-ignored** (`docs/knowledge/sources/*.html`),
not committed. The iframe renders only in HTML readers (MkDocs); GitHub/Obsidian use the link. Always pin a
retrieved-date — it's a point-in-time freeze, not a live view.

*Renders:* link ✅ all four · iframe ✅ MkDocs only.

---

## How each reader treats the four representations
| Representation | GitHub | Obsidian | Foam | MkDocs |
|---|---|---|---|---|
| 1 · Source-excerpt callout | ✅ | ✅ | ✅ | ✅ |
| 2 · Screenshot (exact original) | ✅* | ✅ | ✅ | ✅* |
| 3 · Raw HTML (exact custom) | ❌ stripped | ⚠️ mostly | ⚠️ partial | ✅ styled |
| 4 · monolith snapshot (exact original) | link only | link only | link only | ✅ iframe + link |

\* once the local PNG exists.

## Takeaway
- For the **searchable canonical record** → Representation 1 (works everywhere).
- For your **"exact original styling helps me remember"** need → Representation 2 (screenshot) is the
  reliable, portable way to get NVIDIA's *actual* pixels; Representation 3 gets *custom* exact styling but
  only in an HTML renderer (MkDocs).
- The interleave (note → source → analysis) is the durable habit; the styling fidelity is a per-block choice.

## Changelog
- 2026-06-08 — Worked example created to demonstrate three source-embedding representations.
