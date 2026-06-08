# Golf-grip hand-rotation analysis — preserved working set

Self-contained snapshot of the analysis that measured the **right-hand-vs-left-hand
relative rotation between two golf grips** from two Meta SAM-3D-Body GLB exports.

**Headline result:** the right hand rotated **≈ 33.5°** relative to the left between
grip A and grip B (axis ≈ the club-shaft/vertical). Triple cross-checked and proven
invariant to global misalignment. (Right hand = node 108, the one that moved ~39°;
left = node 135, ~6°.)

## Reproduce offline (after a reboot wipes /tmp)

The scripts use absolute `/tmp/...` paths. To re-run:

```bash
bash restore_to_tmp.sh        # copies data/*.json + *.py back to /tmp
python3 /tmp/crosscheck2.py   # prints the 33.5° result, 3 ways
python3 /tmp/verify.py        # global-invariance test + L/R trace
python3 /tmp/handprep.py      # rebuilds finger assignment + hand geometry
python3 /tmp/annotate_hands.py# rebuilds annotated hand PNGs (needs hand_proj_A.json)
```

Steps that need **Blender** (the live MCP session) cannot be re-run offline; their
*outputs* are saved here so the rest of the pipeline works without Blender:
- `data/grip2.json`, `data/grip3.json` — raw joints+bones extracted from each GLB
  (sphere world-centroids + bone-connector endpoints). **Everything derives from these.**
- `data/hand_proj_A.json` — Blender camera projection of hand joints (for the 2D label overlay).

## Pipeline order

| Stage | Script | Input → Output |
|---|---|---|
| 1. Extract (Blender) | (MCP session) | GLB → `data/grip2.json`, `data/grip3.json` |
| 2. Reconstruct tree | `recon2.py` | dedupe joints + Kruskal MST → 86-joint/85-bone tree (imported by all others) |
| 3. Measure rotation | `measure.py`, `crosscheck2.py` | Kabsch per hand → **33.5°** |
| 4. Validate | `verify.py` | global-rotation invariance + arm-trace L/R |
| 5. Label skeleton | `save_labeled.py`, `annotate.py` | → `data/labeled_*.json`, `data/joint_annotations.json` (viewer) |
| 6. Hand fingers | `handdata.py`, `handprep.py` | → `data/handgeo_*.json`, `data/hand_labels.json` |
| 7. Render hands (Blender) | (MCP session) | → `data/hand_proj_A.json` + `../renders/*.png` |
| 8. Annotate hands | `annotate_hands.py` | → `../renders/{left,right}_hand_annotated.png` |

(Exploratory/superseded: `recon.py`, `analyze.py`, `analyze2.py`, `topo.py`, `body.py`,
`crosscheck.py` (PCA method — unreliable), `overlay.py`.)

## Confidence summary (joint labels)
- **Certain (4):** wrists (108=R, 135=L), chest hub (104), neck/head base (159).
- **Likely (27):** shoulders/elbows/forearms, pelvis/hips, spine & leg joints.
- **Uncertain (55):** specific finger identities (thumb/index/…), face features.
  Finger NAMES in `hand_labels.json` are a geometric best-guess pending user validation.

The interactive viewer is the parent folder (`../index.html`); serve with
`python3 -m http.server 8731 --directory <repo>/glb_joint_viewer` and open
http://127.0.0.1:8731.
