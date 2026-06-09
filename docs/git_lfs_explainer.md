# Git LFS — what it is and how it handles large files (e.g. videos)

## The problem it solves
Plain Git was built for **text/source code**. It stores the *full* contents of every version of
every file in the repository history (`.git`). That is fine for code, but terrible for large binaries
like **videos, `.mp4`, `.blend`, `.glb`, model weights**, because:

- Binaries don't "diff" — each edit stores another whole copy, so `.git` balloons and never shrinks.
- Every `clone`/`fetch` drags down the **entire history** of those big blobs.
- Hosts reject huge files (GitHub blocks pushes >100 MB on the normal path).

**Git LFS (Large File Storage)** is a Git extension (a separate CLI, `git lfs`) that keeps big files
*out* of normal Git history. Git tracks only a tiny **text pointer**; the real bytes live in a
separate **LFS store** and are downloaded on demand.

## How it works — the object model
`.gitattributes` says "*.mp4 is an LFS file". On `git add`, a **clean filter** swaps the real bytes
for a ~130-byte pointer (an `oid` SHA-256 + size); Git commits only that pointer. The real bytes are
cached in `.git/lfs/objects/` and uploaded to the LFS store on push.

![Git LFS object model](diagrams/LFS_A_object_model.png)

A pointer file is just plain text and looks like:
```
version https://git-lfs.github.com/spec/v1
oid sha256:4d7a214614ab2935c943f9e0ff69d22eadbb8f32b1258daaa5e2ca24d17e2393
size 264338510
```

## How it works — cross-machine workflow (your exact case)
Authoring on the Mac, then pulling on this Windows PC:

![Git LFS workflow across machines](diagrams/LFS_B_workflow.png)

On `clone`/`pull`, the **pointer** arrives through normal Git; the **smudge filter** (or an explicit
`git lfs pull`) then fetches the real blob by `oid` from the LFS store and reconstitutes the file in
your working tree. The "Filtering content: 100% (52/52)" line you saw during the initial clone *was*
the smudge filter pulling LFS blobs.

## The commands you actually use
| Command | What it does |
|---|---|
| `git lfs install` | One-time per machine: registers the clean/smudge filters in your Git config. **Do this before cloning** an LFS repo. |
| `git lfs track "*.mp4"` | Start tracking a pattern; writes/updates `.gitattributes` (commit that file). |
| `git lfs track` | List the patterns currently tracked. |
| `git add … && git commit` | Normal — the clean filter makes the committed blob a pointer automatically. |
| `git push` | Uploads new LFS blobs to the store, pushes pointers to Git. |
| `git lfs pull` | Download LFS blobs for the current checkout (real bytes). |
| `git lfs fetch [--all]` | Download blobs into the local cache without touching the working tree (`--all` = every ref). |
| `git lfs checkout` | Replace pointers in the working tree with real bytes already in the cache. |
| `git lfs ls-files` | List which files in the checkout are LFS-managed (and whether the blob is present). |
| `git lfs status` | Show LFS files that are modified/staged. |
| `git lfs env` | Print LFS config + the resolved LFS endpoint (useful when debugging). |

## Gotchas relevant to this repo
- **Install before clone.** If `git lfs install` wasn't run first, LFS files come down as the tiny
  *pointer text* (stub files), not the real video. Fix: `git lfs install` then `git lfs pull`.
- **Spot a stub:** if `data/grip_front_1_cropped.mp4` is ~130 bytes and opens as text starting with
  `version https://git-lfs…`, the real blob hasn't been fetched — run `git lfs pull`.
- **`.gitattributes` must be committed** for tracking to apply on other machines.
- **GitHub LFS has quotas** (storage + monthly bandwidth on the free tier); large/repeated pulls
  count against bandwidth. The HF side rejects binaries entirely without git-xet (why this project
  keeps a separate text-only `hf-space` repo).
- Verify what's tracked + present here with `git lfs ls-files` after a pull.
