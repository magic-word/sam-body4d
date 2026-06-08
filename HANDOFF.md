# HANDOFF — Golf-grip 4D rigged-animation project (context transfer)

> Read this first if you're a fresh Claude Code agent picking this up (e.g. on the Windows PC). It captures the goal, the journey, what's validated, and exactly what to do next. The step-by-step runbooks are `glb_joint_viewer/PLAN_windows_pipeline_run.md` and `glb_joint_viewer/PLAN_blender_mhr_rig.md`.

## The user & the goal
The user is a golfer analyzing a **right-hand grip-technique change**. They captured a **video** of themselves performing the change and pulled **two stills** (grip A = "before", grip B = "after") from it. The end goal: a **clean, rigged, editable 3D animation** (Blender, plays in the timeline, ideally IK-able) of the right hand/arm rotating from grip A to grip B — left hand and body held fixed — to visualize/measure the technique change in slow motion.

## What's been DONE and VALIDATED (don't redo)
Working from two GLBs exported from Meta's **SAM-3D-Body web demo** (`gripA.glb`, `gripB.glb` in this folder):
- Those GLBs are **lossy**: a `THREE.GLTFExporter` scene with the baked surface mesh + 88 joint-marker spheres + 85 bone sticks — **no skeleton, no skin weights, no pose params, no joint names**. Everything below was *recovered* from geometry.
- The `HumanMesh` is the **exact canonical MHR (Momentum Human Rig) template**: **18,439 vertices / 36,874 faces**, identical in both files. (MHR = the parametric body model SAM-3D-Body uses.)
- Recovered an 86-joint skeleton from the markers/bones; **validated the right & left hands, all 5 fingers each (the user confirmed the finger labels), wrists (R=node 108, L=node 135), and topology.**
- **Headline measurement: the right hand rotates ≈ 33.5° relative to the left hand between grip A and grip B**, about the club-shaft axis. Triple cross-checked (Kabsch), global-rotation-invariant. (Use this as an end-to-end sanity check for any new pipeline output.)
- Built an **interactive viewer** (`index.html` + `joint_annotations.json`) and many renders (`renders/`).
- Attempted Blender animations via **blendshape morph** and **segment linear-blend-skinning** — these are *workarounds* and have known artifacts (wrist crease, finger shear, left-hand drift if masked badly). **They are superseded** by the plan below.

## The KEY pivot (why we changed approach)
The morph/LBS hacks were needed only because we lacked the *real* rig. The correct solution: **use the actual MHR rig + the real captured motion.**
1. **SAM-3D-Body outputs the rig**, not just the mesh — per frame it produces the 127-joint MHR pose (joint rotations + coords). The web demo just discarded it.
2. **`gaomingqi/sam-body4d` is THIS repo's upstream** (the user's `magic-word/sam-body4d` fork, also deployed to HF Space `troutmoose/sam-body4d`). It does **video → temporally-consistent 4D mesh sequence + per-frame pose params**.
3. So instead of interpolating 2 static poses, **run the user's video through this pipeline** to get the *real* per-frame motion + pose, and the canonical MHR **skin weights** drop out of the loaded model — then build ONE MHR armature in Blender and key the per-frame poses. Identical rig for all frames; only the right arm moves because only its joints change.

## CURRENT STATE / what to do NEXT
We pivoted to running the pipeline **locally on the user's Windows 11 PC + RTX 5070 Ti (Blackwell, 16 GB VRAM)** (the HF Space is paused/billed). Execute, in order:
1. **`glb_joint_viewer/PLAN_windows_pipeline_run.md`** — stand up the pipeline in **WSL2 Ubuntu** with **CUDA 12.8 + a `cu128` PyTorch** (Blackwell needs this; repo's cu121 won't run). Trimmed pipeline (SAM-3 + SAM-3D-Body + MoGe; Diffusion-VAS *off*; `batch_size=16` → fits 16 GB). Add a ~20-line hook to dump per-frame `pred_joint_coords (127,3)` + `pred_global_rots (127,3,3)` → `poses.npz` and the MHR rig (skin weights 18439×127, parents, rest, faces) → `mhr_rig.npz`. Run on `grip_front_1_cropped.mp4`.
2. **`glb_joint_viewer/PLAN_blender_mhr_rig.md`** — build the 127-bone MHR armature in Blender, bind the mesh with the skin weights, key the per-frame poses → the final rigged animation.

It starts with a **Stage −1** ("when the session reopens on Windows"): verify `nvidia-smi`/WSL2, `git clone`, locate video + `HF_TOKEN`, confirm Blender+MCP.

## Critical facts / gotchas
- **Blackwell (sm_120)** → CUDA 12.8 + PyTorch `cu128` (stable that ships sm_120 kernels, else `nightly/cu128`). Symptom of wrong build: "no kernel image is available".
- **detectron2 is the top risk** (unmaintained; may not build on Blackwell). It's only the *human detector* → bypass with a manual/SAM-3 bbox (single centered subject) or YOLO.
- **Windows-hostile deps** (`decord`, `pyrender`, `detectron2`) → that's why we use **WSL2**, not native Windows. `pyrender` offscreen needs `PYOPENGL_PLATFORM=egl` (or skip render — we only need mesh+pose).
- **Gated checkpoints** (`facebook/sam3`, `facebook/sam-3d-body-dinov3` incl. `mhr_model.pt`) need the user's **`HF_TOKEN`** + already-granted access. ~10 GB without Diffusion-VAS.
- **Bring to the Windows machine manually** (git-ignored): the video `grip_front_1_cropped.mp4` and `HF_TOKEN`. The repo uses **Git LFS** — run `git lfs install` before cloning or binaries arrive as stubs.
- **Coordinate frames:** MHR is Y-up; the GLB `HumanMesh` already un-does the camera flip (== raw MHR forward output). For Blender use a fixed −90°-about-X (Y-up→Z-up). The recovered *markers* (`analysis/data/grip2.json`) are in a *different* flipped frame — trust the mesh, not the markers, for framing.

## Repos & assets
- GitHub (work tracked here): **https://github.com/magic-word/sam-body4d** (`origin`). HF Space deploy remote: `hf` → `troutmoose/sam-body4d` (paused).
- This folder `glb_joint_viewer/`: `gripA.glb`/`gripB.glb` (source MHR-template meshes), `index.html` viewer, `renders/`, the Blender scenes (`*.blend`), `analysis/` (scripts + `data/` JSONs + its own README; `restore_to_tmp.sh` rehydrates the analysis), `STATUS_REPORT.md` (the validated report), and the two `PLAN_*.md` runbooks. (This HANDOFF lives at the repo root.)
- Source video (NOT in repo): `grip_front_1_cropped.mp4` — 1080p, 30 fps, 253 frames, single person.
- Pipeline entry: `scripts/offline_app.py`; config `configs/body4d.yaml`; checkpoints via `scripts/setup.py`; per-frame params already collected in `utils/mesh_export.py` (`PersonExportData`); MHR model loaded in `models/sam_3d_body/.../mhr_head.py`.

## User preferences (from CLAUDE.md / global rules)
- One shell command per call; never pipe/chain/redirect (`|`, `&&`, `;`, `>`); use `git -C <path>`.
- **No "Co-Authored-By: Claude"** or any AI attribution in commits or code.
- Use `uv` for local Python env management (the HF/Docker side uses pip).
