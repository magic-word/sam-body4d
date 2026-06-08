# Plan: Recover the REAL grip motion as a rigged 4D animation via the SAM-Body4D pipeline

> Supersedes the earlier "reconstruct the rig from 2 static GLBs" plan. The user supplied the source video and confirmed the pipeline approach.

## Context

We spent many steps reverse-engineering a rig + interpolating between **two static web-demo GLB exports**, which is fragile because the web demo's GLB is **lossy** — THREE.js baked the surface + joint dots and discarded the skeleton, skin weights, and pose params.

Two corrections from the user reframed this:
1. **SAM-3D-Body DOES output the rig** — per inference it produces MHR pose parameters (127 joint rotations) + joint coordinates + the skinned mesh. The rig *template* (skeleton + skin weights) is the fixed MHR. The model gives skeleton+pose+mesh; only the web export threw it away. The pipeline already collects per-frame `joint_coords`/`global_rots` (`utils/mesh_export.py`).
2. **`gaomingqi/sam-body4d` is this very project** (the user's `magic-word/sam-body4d` fork, deployed to HF Space `troutmoose/sam-body4d`). It is purpose-built for **video → temporally-consistent 4D human mesh sequence** with per-frame pose params + Kalman smoothing.

**Source video:** `/Users/thomascummins/dev/chromatica/data/omni/grip_front_1_cropped.mp4` — 1920×1080, 30 fps, 8.44 s, **253 frames** (the user captured the two grip stills from this clip). So we can recover the **real** grip-change motion, not an interpolation.

**Decision:** run the video through the pipeline once to get the real per-frame MHR mesh + pose, plus the canonical MHR skin weights (the model is loaded during the run), then build one MHR armature in Blender and key the per-frame poses → a real, rigged, editable 4D animation.

## Current blockers (Stage 0 — environment)
- HF Space is **PAUSED**, **Hardware: None**, **Storage: none** → must resume with **L40S** GPU and confirm/re-provision the checkpoints (gated SAM-3D-Body + MHR ~20 GB; first boot ~20 min if storage was lost). This is the only place the full pipeline can run (needs CUDA + SAM-3 + Diffusion-VAS + SAM-3D-Body + MoGe + detectron2; the Mac can't — decord/CUDA).
- The local fork has SMPL-X export only **scaffolded** (`offline_app.py:148` reads the flag; `app.py:824` is commented out). We add a small hook (below) rather than depend on it.

## Approach

### Stage 0 — Prep the Space
- Resume Space, assign L40S, verify checkpoints present at `/data/checkpoints` (incl. `sam-3d-body-dinov3/assets/mhr_model.pt`); re-run `start.py`/setup if storage was wiped.
- Add a tiny **export hook** to the run (the params are already computed): dump per-frame `pred_joint_coords (127,3)` + `pred_global_rots (127,3,3)` to `poses.npz`, AND dump the canonical rig from the loaded MHR — probe `self.mhr` (the loaded `mhr_model.pt`) for the **skin weights (18439×127)**, parent hierarchy, rest joint transforms, faces → `mhr_rig.npz`. Reuse `utils/mesh_export.py`'s `PersonExportData` (already collects joint_coords/global_rots) + its baked-vertex GLB exporter for an immediate playable sequence.

### Stage 1 — Run inference on the video
- Trim to the grip-change segment if desired (fewer frames = faster/cheaper), or process all 253 (batched at `sam_3d_body.batch_size=64`).
- Run `scripts/offline_app.py --input_video grip_front_1_cropped.mp4 --output_dir ...` (single person; occlusion-completion can stay disabled). Outputs: per-frame meshes, `poses.npz`, `mhr_rig.npz`, baked-vertex GLB sequence, and the rendered overlay MP4 (sanity-check tracking quality).

### Stage 2 — Bring outputs local; build in Blender (MCP)
- **Tier 1 (quick win, real motion, playable):** import the baked-vertex GLB sequence → it plays natively as the true 4D motion. Validates capture before any rigging.
- **Tier 2 (the rig — recommended end state):** build the **MHR armature** (127 bones from `mhr_rig.npz` rest+parents, Z-up via −90°X), bind the mesh with the 18439×127 weights (vertex groups + Armature modifier), and key each pose bone per frame from `poses.npz` (global→local). Verify the rest + a couple of frames reproduce the pipeline meshes to a few mm. Plays natively + editable/IK-able.
- **Rig-type choice:** MHR end-to-end (above) is most faithful — native to the model, full finger detail (matters for grip), and the weights come free from the loaded model. *Alternative:* SMPL-X (public skeleton+weights, Blender add-on, no gated extraction) but needs MHR→SMPL-X conversion (`scripts/eval/mhr2smpl.py`) — lighter but less hand detail. **Recommend MHR end-to-end.**

### Stage 3 — Verify + deliver
- Rendered overlay shows correct tracking; baked sequence plays; rigged armature reproduces per-frame meshes (few mm); right-hand rotation over the clip cross-checks the validated ~33.5° endpoint result. Deliver the playable/rigged `.blend` + an MP4.

## Open decisions for approval
1. **GPU Space resume** (billing) + checkpoint re-provision — OK to proceed?
2. **Scope:** whole 253-frame clip vs trim to the grip-change segment (recommend trim).
3. **Rig type:** MHR end-to-end (recommended) vs SMPL-X (lighter).

## Critical files
- `scripts/offline_app.py` (CLI run; `--input_video`, `smpl_export` flag), `app.py` (Gradio path)
- `utils/mesh_export.py` (`PersonExportData` already collects joint_coords/global_rots; baked GLB exporter)
- `models/sam_3d_body/sam_3d_body/models/heads/mhr_head.py` (MHR call → verts + 127 joint coords/rots; where to add the rig/weight dump)
- `scripts/eval/mhr2smpl.py` (MHR→SMPL-X fallback)
- `scripts/setup.py`, `scripts/hf_space_info.py`, `/hf-deploy` skill (Space provisioning/run)
- Source video: `/Users/thomascummins/dev/chromatica/data/omni/grip_front_1_cropped.mp4`
- New artifacts: `poses.npz`, `mhr_rig.npz`, baked GLB sequence; Blender build via MCP.

## Why this is better than the prior plan
Real captured motion (every in-between frame is genuine, temporally smoothed) instead of a 2-pose interpolation; the rig + pose come from the model that made the mesh (no reverse-engineering); and the skin weights drop out of the same run. The earlier "extract + fit 2 poses" plan becomes unnecessary except as the Blender-rig-build mechanics (reused in Stage 2).
