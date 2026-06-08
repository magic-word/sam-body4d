# Plan: Run SAM-Body4D locally on Windows (RTX 5070 Ti) → rigged 4D grip animation

## Context

Pivoting from the paused/billed HF Space to the user's **Windows 11 PC + RTX 5070 Ti (Blackwell, 16 GB VRAM)**. **This Claude Code session will be reopened on the Windows PC**, so Claude executes this runbook directly (in **WSL2 Ubuntu**) — it is no longer a hand-off document.

Goal unchanged: run the real grip video `grip_front_1_cropped.mp4` (1080p, 253 frames, single person) through SAM-Body4D to get **per-frame MHR meshes + 127-joint pose params** + the canonical MHR **skin weights**, then build one MHR armature in Blender and key the per-frame poses → a real, rigged, editable 4D animation (Blender stage reuses `~/.claude/plans/distributed-orbiting-torvalds.md`).

### Hard constraints
- **Blackwell sm_120** → **CUDA 12.8 + PyTorch `cu128`** (repo's cu121 won't run; symptom "no kernel image available"). Newest stable cu128 torch that ships sm_120 kernels; fall back to `nightly/cu128`.
- **Windows-hostile deps** (`decord`, `pyrender`/PyOpenGL, `detectron2`) → run in **WSL2 Ubuntu**, not native Windows.
- **16 GB VRAM** → `completion.enable=false`, `sam_3d_body.batch_size=16`; skip Diffusion-VAS entirely (clean single-person clip).
- **Gated checkpoints** (SAM-3 ~2.5 GB; SAM-3D-Body `model.ckpt` + `mhr_model.pt` ~2 GB) need user's `HF_TOKEN` + already-granted access; rest public. ~10 GB total (no Diffusion-VAS).
- **detectron2 = top risk** (Blackwell build may fail) — it's only the human *detector* → bypassable.

## Stage −1 — Get onto the Windows machine (first steps when session reopens there)
- Verify we're on Windows + WSL2: `nvidia-smi` (must show RTX 5070 Ti), `wsl --version`, Ubuntu 24.04 present (install if not).
- `git clone git@github.com:magic-word/sam-body4d.git ~/sam-body4d` (or https). Confirm branch parity with the Mac copy.
- The video is tracked in the repo (LFS) at `~/sam-body4d/assets/videos/grip_front_1_cropped.mp4` — confirm `git lfs install` ran and it's a real file (`ffprobe`), not a pointer stub.
- Put `HF_TOKEN` in `~/sam-body4d/.env.local` (gated-model access).
- Confirm **Blender** is installed on Windows with the **MCP add-on** running, so the Stage 4 rig build can drive it from this session.

## Stage 0 — WSL2 + CUDA + GPU
- Windows: latest NVIDIA Studio/Game-Ready driver (Blackwell-capable). In WSL2: `nvidia-smi` shows the GPU (passthrough is driver-side). `sudo apt install -y cuda-toolkit-12-8 ffmpeg git git-lfs python3.11-venv libegl1-mesa-dev libglvnd-dev` (cuda-toolkit only needed to build detectron2).

## Stage 1 — Python env (Blackwell-correct)
1. `cd ~/sam-body4d && python3.11 -m venv .venv && source .venv/bin/activate`.
2. **Torch cu128 first:** `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128` (use `--pre .../nightly/cu128` if stable lacks sm_120). Verify `torch.cuda.get_device_capability()==(12,0)` + a GPU matmul.
3. `pip install -e .` (decord, pyrender, diffusers==0.29.1, transformers, MoGe, roma). Fallbacks: decord→`pyav`/`torchvision.io`; xformers→cu128 wheel/`flash-attn`/omit.
4. **detectron2:** try `pip install 'git+https://github.com/facebookresearch/detectron2.git' --no-build-isolation`. If build/runtime "no kernel image" → **bypass** (Stage 3).

## Stage 2 — Checkpoints (~10 GB, no Diffusion-VAS)
- `python scripts/setup.py --ckpt-root ~/checkpoints` (token from `.env.local`). If it forces Diffusion-VAS weights, fetch only SAM-3 + SAM-3D-Body (+ mhr_model.pt) + MoGe + Depth-Anything + detectron2 ViTDet. Set `configs/body4d.yaml` `paths.ckpt_root: ~/checkpoints`.

## Stage 3 — Minimal config + run
- Config: `completion.enable=false`, `sam_3d_body.batch_size=16`; optionally skip the pyrender overlay (we only need mesh+pose; if kept, set `PYOPENGL_PLATFORM=egl`).
- **detectron2 bypass (if needed):** single centered subject → seed the human bbox/point manually (or from a SAM-3 mask) and short-circuit `HumanDetector` (`models/sam_3d_body/tools/build_detector.py` / the detect step in `scripts/offline_app.py`); or swap to `ultralytics` YOLO.
- **Add pose/rig export hook (~20 lines; params already in `utils/mesh_export.py` `PersonExportData`):** per frame dump `pred_joint_coords (127,3)` + `pred_global_rots (127,3,3)` → `poses.npz`; dump canonical rig from loaded `self.mhr` (`mhr_head.py`) — skin weights `(18439×127)`, parents, rest transforms, faces → `mhr_rig.npz`.
- Run: `python scripts/offline_app.py --input_video assets/videos/grip_front_1_cropped.mp4 --output_dir out/`. Sanity-check first frames/overlay for tracking quality. (Trim to the grip-change window first if it shortens runtime.)

## Stage 4 — Blender rig + animation (drive Windows Blender via MCP; reuse prior plan)
- Build 127-bone MHR armature from `mhr_rig.npz` (Z-up −90°X), bind mesh with skin weights, key each pose bone per frame from `poses.npz`. Verify rest + sample frames reproduce pipeline meshes to a few mm; only the right arm moves; cross-check ~33.5° endpoint. Native, editable, IK-able.

## Risks → fallbacks
| Risk | Fallback |
|---|---|
| **detectron2 won't build on Blackwell** (top) | Manual/SAM-3 bbox bypass (single subject); or YOLO |
| Stable torch lacks sm_120 | `nightly/cu128`; last resort build torch from source (`TORCH_CUDA_ARCH_LIST=12.0`) |
| `decord` wheel/ABI | `pyav` / `torchvision.io.VideoReader` |
| `pyrender` offscreen | `PYOPENGL_PLATFORM=egl` (or `osmesa`); or skip render |
| `xformers` mismatch | cu128 wheel / `flash-attn` / omit |
| VRAM spikes | `batch_size` 16→8; completion off |
| Gated access | confirm HF account approved for `facebook/sam3` + `sam-3d-body-dinov3` |

## Open decisions (resolve at start of execution)
1. **Environment:** WSL2 + venv (recommended) vs rebuild Dockerfile (CUDA 12.8 base + torch cu128) via Docker Desktop GPU (more reproducible, more setup).
2. **detectron2:** attempt build first, accept bypass if it fails (recommended).

## Critical files
- `pyproject.toml`, `Dockerfile` (apt/pip reference + PyOpenGL 3.1.7 Mesa fix), `configs/body4d.yaml` (`completion.enable`, `sam_3d_body.batch_size`, `paths.ckpt_root`)
- `scripts/setup.py` (checkpoints + gating), `scripts/offline_app.py` (run path, detect step to bypass, export hook site)
- `utils/mesh_export.py` (`PersonExportData` collects joint_coords/global_rots), `models/sam_3d_body/.../mhr_head.py` (loaded `self.mhr` → rig/weights), `models/sam_3d_body/tools/build_detector.py` (detector to bypass)
- Source video `assets/videos/grip_front_1_cropped.mp4` (tracked in repo via LFS)
- Prior Blender-stage plan: `~/.claude/plans/distributed-orbiting-torvalds.md`

## Note on continuity
Plans live under `~/.claude/plans/` per machine — this file is on the Mac. When the session reopens on Windows, the plan content is carried in the conversation; re-save it to the Windows `~/.claude/plans/` if a local copy is wanted. The repo comes via `git clone` (incl. the video, via LFS); only `HF_TOKEN` must be brought over manually.
