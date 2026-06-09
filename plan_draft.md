# Plan Draft — Run SAM-Body4D locally (Windows + RTX 5070 Ti) → rigged 4D grip animation

> Review draft with rendered architecture figures. Diagram sources live in
> [`docs/diagrams/*.dot`](docs/diagrams/); PNGs are rendered via Graphviz 15.0.0
> (`dot -Tpng -Gdpi=140`). Re-render after edits with the same command.

## Context

The user is a golfer analyzing a **right-hand grip change** (grip A → grip B). The goal is a
**clean, rigged, editable Blender 4D animation** of the right hand/arm rotating from A to B so the
technique change can be reviewed in slow motion. The validated headline result to reproduce as an
end-to-end sanity check: **the right hand rotates ≈ 33.5° relative to the left hand** between A and B.

We pivoted away from interpolating two static SAM-3D-Body web-demo GLBs (lossy — no skeleton/weights/pose)
to **running the real video through this pipeline** to recover per-frame MHR meshes + 127-joint pose
params + the canonical MHR skin weights, then building **one MHR armature** in Blender and keying the
per-frame poses. This session is resuming on the **Windows 11 PC + RTX 5070 Ti** (the paused/billed HF
Space is abandoned for this run).

### Environment already verified this session
- **GPU**: RTX 5070 Ti, 16 GB, driver 591.74 (CUDA 13.1-capable). Blackwell = **sm_120**.
- **WSL2** 2.7.3 + **Ubuntu 24.04** present (stopped). Windows-hostile deps (`decord`, `pyrender`,
  `detectron2`) → run the pipeline in WSL2, not native Windows.
- **Blender 5.1** running on Windows with the **MCP add-on connected** (verified) → Stage 5 drives it.
- Repo cloned to `C:\dev\projects\sam-body4d` (models are **vendored**, not submodules — present).

### Decisions locked with the user
- **Video**: user committed `grip_front_1_cropped.mp4` to `origin/main` → `git pull` to fetch (LFS).
  User will **manually trim** the A→B segment and save it to **`C:\dev\projects\sam-body4d\data\grip_AB_trimmed.mp4`** — this trimmed clip is what we run.
- **HF token**: user will create `C:\dev\projects\sam-body4d\.env.local` with `HF_TOKEN=...` and confirm
  gated access to `facebook/sam3` + `facebook/sam-3d-body-dinov3`.
- **Rig**: **MHR end-to-end** (native 127-bone, full finger detail, weights from the loaded model).

### Execution mechanics
This Claude Code session runs on **Windows** (Git Bash / PowerShell). All pipeline steps run **inside
WSL2** via `wsl bash -lc "..."`. For IO/compute speed we work on the WSL **ext4** filesystem
(`~/sam-body4d`, `~/checkpoints`), not `/mnt/c`. The Windows-side checkout supplies the trimmed video +
`.env.local` (copied across `/mnt/c`). Blender is driven directly through the MCP tools (Windows-side).

---

## Stage 0 — Assets + sync
1. `git -C C:\dev\projects\sam-body4d pull` then `git -C ... lfs pull` — fetch the committed video.
2. Confirm the user has saved the trimmed clip to `data\grip_AB_trimmed.mp4` and created `.env.local`.
3. In WSL2: fresh `git clone` of the repo to `~/sam-body4d` (with `git lfs install` first), then
   copy `grip_AB_trimmed.mp4` and `.env.local` from `/mnt/c/dev/projects/sam-body4d/` into it.

## Stage 1 — WSL2 Python env (Blackwell-correct)
- `apt install` (WSL): `ffmpeg git-lfs python3.12-venv libegl1-mesa-dev libglvnd-dev`; add
  `cuda-toolkit-12-8` **only if** building detectron2.
- `python3.12 -m venv .venv` (matches `pyproject.toml` `requires-python >=3.12`).
- **Torch first**: `pip install torch torchvision torchaudio --index-url .../whl/cu128`. As of
  mid-2026 stable cu128 ships sm_120 kernels (the plan's old "nightly" worry is stale). Verify
  `torch.cuda.get_device_capability() == (12, 0)` + a GPU matmul ("no kernel image" ⇒ wrong build).
- `pip install -e .` (decord, pyrender, diffusers==0.29.1, transformers, MoGe, roma). Fallbacks:
  decord→`pyav`/`torchvision.io`; xformers→cu128 wheel/omit.
- **detectron2**: try `pip install 'git+https://github.com/facebookresearch/detectron2.git'
  --no-build-isolation`. If it won't build/run on Blackwell → **bypass** (Stage 3).

## Stage 2 — Checkpoints (~10 GB, no Diffusion-VAS)
- `python scripts/setup.py --ckpt-root ~/checkpoints` (token read from `.env.local`/env). This also
  pulls the config template from GitHub Release `v0.1.0` and generates `configs/body4d.yaml`.
- Needed: `sam3/sam3.pt`, `sam-3d-body-dinov3/{model.ckpt,model_config.yaml,assets/mhr_model.pt}`,
  `moge-2-vitl-normal/model.pt`. **Skip** Diffusion-VAS dirs + `depth_anything_v2_vitl.pth` (only used
  when completion is on) — optionally comment those entries in `scripts/setup.py:build_specs()`.
- Edit `configs/body4d.yaml`: `paths.ckpt_root: ~/checkpoints`, `completion.enable: false`,
  `sam_3d_body.batch_size: 16`, `runtime.output_dir: out/`.

## Stage 3 — Code changes (detector bypass if needed + export hook)
**3a. Detector bypass (only if detectron2 fails).** `scripts/offline_app.py:101` always builds
`HumanDetector(name="vitdet")`, and `inference()` (lines 497–501) calls `process_one_image` for the
initial bbox. Single centered subject ⇒ add a `name="manual"` branch in
`models/sam_3d_body/tools/build_detector.py:HumanDetector` that returns a centered/full-image box
(`run_detectron2_vitdet` already has `default_to_full_image`), and select it in
`build_sam3_3d_body_config` (`offline_app.py:100`) behind a config/env flag — no detectron2 import.

**3b. Export hook** (the heavy lifting is already written — reuse `utils/mesh_export.py`). Currently
`offline_app.py` saves only OBJ/renders; it does **not** export poses/GLB. In `on_4d_generation`:
- accumulate per-frame data via `utils.mesh_export.collect_frame_data(export_data, mask_output,
  id_current, self.sam3_3d_body_model.faces, fps)` inside the batch loop (per-person `mask_output`
  already carries `pred_vertices`, `pred_joint_coords`, and the global rotations);
- after the loop, dump **`poses.npz`** (`joint_coords (F,127,3)`, `global_rots (F,127,3,3)`, fps, faces)
  and the **baked-vertex GLB** sequence via `export_all_persons_glb`.
- **Verify key names at runtime**: `mhr_head.py:365` emits `joint_global_rots`, but
  `collect_frame_data` reads `pred_global_rots` — confirm the rename in `process_image_with_mask` and
  adapt the hook to whatever keys `mask_output` actually contains.

**3c. MHR rig dump → `mhr_rig.npz`** (KEY RISK). The rig lives in the loaded MHR at
`mhr_head.py:114` `self.mhr = torch.jit.load(mhr_model_path)` (TorchScript). Probe its
`named_buffers()/named_parameters()/state_dict()` for: **skin weights (18439×127)**, joint
**parents**, **rest joint transforms**, and **faces** (`self.faces` (36874,3) is already exposed at
`mhr_head.py:87`/`:364`). Write a small one-shot probe script first to locate these tensors.
**Fallback**: if clean LBS weights can't be extracted, the **baked-vertex GLB still delivers the
playable 4D motion** (Tier 1); the editable rig (Tier 2) can then approximate weights or fall back to
SMPL-X conversion (`scripts/eval/mhr2smpl.py`) — but attempt MHR extraction first.

## Stage 4 — Run inference
- `cd ~/sam-body4d && source .venv/bin/activate && PYTHONUTF8=1 python scripts/offline_app.py
  --input_video data/grip_AB_trimmed.mp4 --output_dir out/grip_ab`.
- Outputs: rendered overlay MP4 (**sanity-check tracking quality on first frames before trusting
  the rest**), per-frame meshes, `poses.npz`, `mhr_rig.npz`, baked GLB.
- If VRAM spikes: `batch_size` 16→8.

## Stage 5 — Blender MHR rig + animation (drive Windows Blender via MCP)
- Copy `poses.npz`, `mhr_rig.npz`, baked GLB out of WSL to `C:\dev\projects\sam-body4d\out\grip_ab\`.
- **Tier 1 (quick win)**: import the baked-vertex GLB → plays the true 4D motion; validates capture.
- **Tier 2 (deliverable)**: build the **127-bone MHR armature** (rest + parents from `mhr_rig.npz`,
  Z-up via fixed **−90° about X**), bind the mesh with the 18439×127 weights (vertex groups + Armature
  modifier), key each pose bone per frame from `poses.npz` (global→local). Editable, IK-able.
- **Coordinate note**: trust the **mesh** for framing (MHR Y-up; the GLB `HumanMesh` already un-does
  the camera flip), **not** the recovered markers (different flipped frame).

## Stage 6 — Verify + deliver
- Overlay shows correct tracking; baked GLB plays; rigged armature reproduces per-frame pipeline meshes
  to a **few mm** at rest + sample frames; **only the right arm moves**; **right-hand rotation A→B
  cross-checks ≈ 33.5°** (endpoints of the trimmed clip = grip A and grip B). Deliver the `.blend` + MP4.

## Risks → fallbacks
| Risk | Fallback |
|---|---|
| **MHR skin-weight extraction from TorchScript** (top) | Probe `self.mhr` buffers first; else baked-GLB (Tier 1) delivers motion, rig via SMPL-X `mhr2smpl.py` |
| detectron2 won't build on Blackwell | `name="manual"` centered-bbox bypass (3a); or YOLO |
| Stable torch lacks sm_120 | `nightly/cu128`; last resort source build (`TORCH_CUDA_ARCH_LIST=12.0`) |
| `decord` wheel/ABI on py3.12 | `pyav` / `torchvision.io.VideoReader` |
| Export-dict key mismatch (`joint_global_rots` vs `pred_global_rots`) | Inspect `mask_output` keys at runtime; adapt hook |
| VRAM spikes | `batch_size` 16→8 |
| Gated access not granted | Confirm HF approval for `facebook/sam3` + `sam-3d-body-dinov3` |

---

# Architecture & low-level interaction diagrams

## A. Hardware / driver stack — how WSL2 reaches the GPU (GPU-PV paravirtualization)

There is **no native NVIDIA Linux kernel module** in WSL2. CUDA user-space calls hit WSL shim
libraries (`/usr/lib/wsl/lib/libcuda.so`, `libdxcore.so`), which issue ioctls to the **`/dev/dxg`**
device (the `dxgkrnl` Linux driver). Those are forwarded over **VMBus** to the Windows host's
`dxgkrnl.sys` + `nvlddmkm.sys` (the real WDDM driver), which schedules work on the silicon. Blender
runs **natively on Windows** and talks to the same driver directly (no VM hop) over Vulkan/OpenGL/OptiX.

![Hardware / driver stack](docs/diagrams/A_hw_stack.png)

## B. End-to-end pipeline dataflow (API calls + device placement)

Each box is annotated with the actual call site and whether it runs on CPU (host RAM) or GPU (VRAM).
Arrows note the host↔device transfers (`cudaMemcpyAsync` over PCIe DMA) that bound throughput.

![End-to-end pipeline dataflow](docs/diagrams/B_pipeline.png)

## C. One GPU op — how a single torch call reaches the silicon under WSL2

This is the latency-critical path repeated millions of times per inference. The extra VMBus hop is
the only structural difference from native Linux; compute throughput on-die is identical.

![Single GPU op path](docs/diagrams/C_gpu_op.png)

## D. MHRHead forward + rig/pose export internals (Stage 3b/3c detail)

Shows exactly where `poses.npz`, the baked GLB, and the risky `mhr_rig.npz` are tapped out of the
already-computed graph — and that the skin weights live inside the TorchScript `self.mhr` buffers.

![MHRHead forward + export internals](docs/diagrams/D_mhr_internals.png)

## E. Per-stage compute, device & VRAM budget (16 GB ceiling)

| Stage | Call site | Device | Kernels / libs | Peak VRAM (est.) | H2D / D2H |
|---|---|---|---|---|---|
| Frame decode | `read_frame_at`, `init_state` | CPU | ffmpeg/libavcodec (decord) | — | RGB frames H2D |
| SAM-3 propagate | `predictor.propagate_in_video` (`offline_app.py:160`) | **GPU** | cuDNN conv, cuBLAS GEMM, flash-attn | ~4–6 GB | masks D2H per frame |
| MoGe-2 FOV | `FOVEstimator('moge2')` (`offline_app.py:99`) | **GPU** | ViT-L GEMM/attn | ~1–2 GB (transient) | intrinsics D2H |
| ViTDet detect | `HumanDetector('vitdet')` (`offline_app.py:101`) | **GPU** | detectron2 CUDA: nms, roi_align | ~2–3 GB (transient) | boxes D2H |
| SAM-3D-Body + MHR | `process_image_with_mask` → `mhr_head.forward` | **GPU** | DINOv3 ViT, FFN, TorchScript LBS, roma | ~3–5 GB @ `batch_size=16` | per-person dict D2H |
| Export hook | `collect_frame_data`, `np.savez`, pygltflib | CPU | numpy, pygltflib | — | — |
| pyrender overlay (optional) | `visualize_sample*` | GPU(EGL)/CPU | OpenGL via EGL (or skip) | small | framebuffer D2H |
| Blender rig | bpy via MCP (Windows-native) | **GPU (native)** | Vulkan/OpenGL viewport, Cycles-OptiX | separate process | — |

Sequential stage execution + `batch_size=16` + `completion.enable=false` keeps peak well under 16 GB;
the caching allocator (`cudaMalloc` arenas) holds the largest single model's footprint, not the sum.

---

## Critical files
- `scripts/offline_app.py` — run path; detector build (`:100-101`), initial detection
  (`:497-501`), export-hook site (`on_4d_generation`, batch loop ~`:443-477`).
- `utils/mesh_export.py` — `collect_frame_data`, `PersonExportData`, `export_all_persons_glb`,
  `export_baked_vertex_glb` (reuse as-is).
- `models/sam_3d_body/sam_3d_body/models/heads/mhr_head.py` — `self.mhr` (`:114`), output dict
  (`:346-367`), `self.faces` (`:87`,`:364`) → rig/weight dump site.
- `models/sam_3d_body/tools/build_detector.py` — `HumanDetector` (bypass site).
- `scripts/setup.py` — checkpoints + gating (`build_specs()`), config generation.
- `configs/body4d.yaml` — generated; set `ckpt_root`, `completion.enable`, `batch_size`, `output_dir`.
- Source: `data/grip_front_1_cropped.mp4` (via git LFS), `data/grip_AB_trimmed.mp4` (user-trimmed).
- Prior runbooks (superseded by this file): `glb_joint_viewer/PLAN_windows_pipeline_run.md`,
  `glb_joint_viewer/PLAN_blender_mhr_rig.md`; validated result in `glb_joint_viewer/STATUS_REPORT.md`.
