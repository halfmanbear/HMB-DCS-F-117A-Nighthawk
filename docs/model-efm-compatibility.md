# Model, Blender and EFM compatibility

The exterior model, the Lua `Damage` table and the EFM have to agree on damage names and cell
numbers. This page records which versions belong together, and which Blender file holds each model.
Model hashes are SHA256, shortened to 12 characters except in the current state.

## Current state

As of 2026-11-01. None of this is committed yet.

| Part | Location | Identity |
|---|---|---|
| Exterior model | `Shapes/f-117-nighthawk.edm` | `b314ca7fa7f66af7d663a3da017bc41776c8b392fff3bf86b5a9157b371117ac` |
| Damage table | `F-117-NightHawk.lua` | 25 cells, `00a6e68c8947` |
| EFM source | `EFM Source Code/F_117_NightHawk.cpp` in the EFM repository | `43bf632` plus uncommitted changes, `9f2ca3c9379f` |
| EFM binary | Build output, loaded through the local proxy | `d5e7019fdf70`, built 2026-11-01 13:50 |
| Blender scene | `F-117 Damage Sections`, in the two projects listed below | Stamped with the model hash |

## Blender projects

Paths are under `blender_files/`, and `IC` means `blender_files/integrated_collision/`. The first
six rows were checked by comparing triangle counts per damage name against the model. The others
come from each folder's README and overall counts.

| Project | Scene | Model | Damage table | EFM | Status |
|---|---|---|---:|---|---|
| `IC/exposed_controls/f-117-nighthawk-exposed-controls.blend` (tracked) | `F-117 Damage Sections` | `b314ca7fa7f6` | 25 | 25-cell | **Current** |
| `IC/f-117-nighthawk-integrated-collision.blend` | `F-117 Damage Sections` | `b314ca7fa7f6` | 25 | 25-cell | **Current** |
| `IC/exposed_controls/f-117-nighthawk-exposed-controls.blend` | `F117 complete EDM - exposed controls` | `57e1fb9298d6` | 9 | 9-cell | Both 2.0.0 dev releases |
| `IC/exposed_controls/f-117-nighthawk-exposed-controls.compressed.blend` | `F117 complete EDM - exposed controls` | `57e1fb9298d6` | 9 | 9-cell | The file committed in `f1bb490` |
| `IC/exposed_controls/f-117-nighthawk-exposed-controls.blend` | `F117 symmetric collision export` | `8c95f0985f0c` | 9 | 9-cell | Local only |
| `IC/f-117-nighthawk-integrated-collision.blend` | `F-117 Integrated Collision` | `c2774c843bed` | 3 | 3-cell | Local only, 2026-09-25 |
| `f-117-nighthawk.blend` | `Scene` | Same collision names as `c2774c843bed` | 3 | 3-cell | Local only |
| `IC/damage_wiring/f-117-nighthawk-damage-wired.blend` | `Scene` | `5a09d241a44e` | 9 | 9-cell | Local only |
| `IC/gear_contacts/f-117-nighthawk-gear-contacts.blend` | Both | `989a82a83010` | 9 | 9-cell | Local only |
| `IC/simple_collision/f-117-nighthawk-simple-collision.blend` | `Simplified collision - 544 triangles` | `c3a9844d7975` | 9 | 9-cell | Local only |
| `IC/symmetric_collision/f-117-nighthawk-symmetric-collision.blend` | `F117 symmetric collision export` | `8c95f0985f0c` | 9 | 9-cell | Local only |
| `IC/damage_sections/f-117-nighthawk-integrated-collision.before-damage-sections.blend` | As the integrated project, without the sections | `c2774c843bed` | 3 | 3-cell | Backup |

- `F-117 Integrated Collision` has 16 fewer `MAIN` triangles than its model (33,207 against 33,223),
  so it isn't an exact copy. `f-117-nighthawk.blend` has the same totals.
- The `Scene` in the integrated project has an empty collision collection. `Scene`,
  `Simplified collision - 544 triangles` and `Collision symmetry review` in the exposed-controls
  project are older working scenes, and none of them matches a released model.
- No Blender project has been identified for the v1.x model (`16b543775446`, kept locally as
  `Shapes/old-f-117-nighthawk.edm`).

Each scene in the two current projects has `f117_status` and, where known, `f117_model_sha256` under
Scene properties > Custom Properties. The current sections also have `f117_efm`.

## EFM generations

| Generation | Cells handled | EFM commits | Behaviour |
|---|---|---|---|
| 3-cell | 3, 10, 11 | Up to `49846e7`, whose source `317af86` kept | Cockpit, `MAIN` and `ENGINE` |
| 9-cell | Adds 25, 26, 37, 38, 53, 54 | `02fb8f2` to `43bf632` | Adds the six control surfaces. Cell 10 damages both wings, cell 11 both engines |
| 25-cell | 0, 3, 8, 9, 10, 11, 12, 15, 16, 23, 24, 25, 26, 35, 36, 37, 38, 53, 54, 56, 57, 82, 83, 84, 85 | Uncommitted, on top of `43bf632` | One section per cell. Cell 10 is the right fuselage, cell 11 the left engine |

The 9-cell source was first built locally on 2026-09-25, and first committed in `02fb8f2`.

## Releases

The dev releases are taken from their `build-manifest.json`. Older releases have no manifest, so
their EFM commit is only the nearest earlier commit by date. Dev release names keep the commit hash they were built from; the table gives the current hash.

| Release | Mod commit | Model | Damage table | EFM commit | EFM binary |
|---|---|---|---:|---|---|
| v1.9.8 | `86b9501` | `16b543775446`, with `f-117-nighthawk_collision.edm` | 3 | Probably `84ec0ee` | Not recorded |
| v1.9.9 | `867a42a` | Same | 3 | Probably `69db088` | Not recorded |
| v1.10.0 | `fa80585` | Same | 3 | Probably `c99e91f` | Not recorded |
| 2.0.0-dev-45fc697 | `f1bb490` | `57e1fb9298d6` | 9 | `daf28a5` | `11670d12e6c9` |
| 2.0.0-dev-eac3e6b | `c721019` | `57e1fb9298d6` | 9 | `ab6e78e` | `f17b7db2af05` |

Both dev releases have mismatched damage names: the Lua table has `ENGINE`, which the model lacks,
and the model has `WHEEL_F`, `WHEEL_L` and `WHEEL_R`, which the Lua table lacks. DCS logs "Corrupt
damage model" for that kind of mismatch. Later releases also record `model_sha256` in the manifest.

## Mixing versions

| Combination | Result |
|---|---|
| Current model and Lua with the 9-cell EFM | 16 cells are ignored. A right fuselage hit damages both wings, and a left engine hit damages both engines |
| Older model and Lua with the 25-cell EFM | `MAIN` hits only count as right fuselage, so wings take no damage. `ENGINE` hits only reach the left engine |
| Older model with the current Lua, or the reverse | DCS logs "Corrupt damage model" |

The package workflow builds whatever EFM commit is on the matching branch when the job starts, so
**push the EFM before the mod** for any change to damage cells.

## Exporting from Blender

Do not export the exterior model from any of these projects.

- The installed model is built by `IC/add_damage_sections.py`, which patches the collision section
  of `IC/exposed_controls/f-117-nighthawk.edm`.
- `F-117 Damage Sections` holds plain meshes for review, without the parent links or collision node
  types the model needs.
- The older `Scene` collision uses names the `Damage` table doesn't have, such as `CABIN_LEFT_SIDE`
  and `ELERON_L`.

Getting a visual edit from Blender into the model while keeping the sections has not been tested.

## Keeping this page current

When the model or the damage cells change:

1. Rebuild and install the model, as described in `IC/damage_sections/README.md`.
2. Run `IC/add_damage_section_scene.py` on the current projects, adding any new scene to its
   `HISTORICAL` list.
3. Update **Current state**, then add a row to the tables above.
4. Run `python -m pytest tests/test_damage_model.py`.

The test fails if this page names a different model from the installed one, if the Lua table and
model names differ, or if the EFM's cells differ from the model's. It also fails if the built EFM is
older than its source. The EFM checks read `F117_EFM_ROOT` or `bin/efm.proxy.ini`, and skip if
neither finds the source.
