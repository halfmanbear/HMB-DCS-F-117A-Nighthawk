# Model, Blender and EFM compatibility

The exterior model, the Lua `Damage` table and the EFM have to agree on damage names and cell
numbers. This page records which versions belong together, and which Blender file holds each model.
Model hashes are SHA256, shortened to 12 characters except in the current state.

## Current state

Model/source identities updated 2026-11-07. The EFM and damage-table records
below are retained from the 2026-11-04 audit; this glass/material update did not
change those interfaces or independently re-audit the EFM build.

| Part | Location | Identity |
|---|---|---|
| Exterior model | `Shapes/f-117-nighthawk.edm`, USAF default livery source, corrected glass and opaque non-emissive HUD glyph material, left bay on arg 27 and right bay on arg 28 (2026-11-08) | `c616aeb0e7b14b04eb3a00c8e9eb6951536bd449def81a4f33b457cb4593ab0d` |
| Cockpit model | `Cockpit/Shape/Cockpit_F-117.edm`, corrected glass and 18 restored emissive objects | `340590d438e433b667c24cb54802078ee40a98cfcf0360726946ea1598c84f36` |
| Damage table | `F-117-NightHawk.lua` | 25 cells, `00a6e68c8947` |
| EFM source | `EFM Source Code/F_117_NightHawk.cpp` in the EFM repository | `d241a56` plus uncommitted changes, `b09f58c2f0cf` |
| EFM binary | Build output, loaded through the local proxy | `32d64e264d8a`, built 2026-11-03 16:10 |
| Store profiles | `Cockpit/Scripts/Systems/Weapons.lua` `classify()` and the EFM `kCcrpStoreModels` | 14 profiles in the same order; `tests/test_store_profiles.py` checks both |
| Exterior Blender source | `blender_files/uv_work/f117-exterior-painted-candidate.blend`, with the bay split in `f117-exterior-painted-candidate.baysplit.blend` | Packed new atlases on retained geometry; refreshed after the clear-glass DDS change. The installed model was exported from the split copy. Run `tools/models/split_weapon_bays.py` on the painted candidate before its next export |
| Cockpit Blender source | `blender_files/uv_work/f117-cockpit-painted-candidate.blend` | Packed new atlases, corrected glass and object-specific emission on retained geometry |

The user accepted basic HUD/gauge glass visibility in DCS on 2026-11-06 at 12:30.
Both installed exports previously passed structural and sampled animation checks
against the user's pre-correction exports. All 102 development DDS files are in
the existing mounted folders. The later correction changed only two glass albedo
DDS files to clear RGBA; installed EDM hashes remained unchanged. The current
staged exterior export differs in binary hash and was not the model used for this
texture-only test. See `texture_sources/uv_work/finish/glass-debug/README.md` and
its installation JSON records for exact hashes, backups and scope. Final artwork,
night lighting, gauge calibration and broader runtime acceptance remain open.

The subsequent matched dusk test exposed lost cockpit emission. Eighteen
object-specific emissive settings were restored and the checked cockpit EDM
above installed with a backup; see `glass-debug/emission-installation.json`
under the material handoff. All DDS files and the exterior remain unchanged.
Saved geometry/UV/interface checks and exported emission/interface checks pass;
the dusk appearance requires DCS retesting. Missing engraving remains artwork work.

## Weapon bay arguments

The left bay moves on arg 27 and the right bay on arg 28. Each argument opens that bay's door over 0
to 0.7 and lowers its trapeze over 0.6 to 1, and `Pylon1` (station 1) is under 27 and `Pylon2` under 28.
Nothing in the model is animated by arg 26, but the EFM writes it as "either bay open": DCS draws the
stores only while arg 26 is open (checked in DCS with `tools/missions/bay_shots.py`). The model used to
drive both bays from 26, so this model needs the per-bay EFM (`Inputs.h` commands 10130 to 10132, servos
writing 27 and 28). With an older EFM the bays stay shut and the stores hidden. An older model works
with the new EFM, but both bays then move together on arg 26.
`tools/models/split_weapon_bays.py` makes the change in a Blender scene, starting from a scene with
the bays on 26, and checks it; `tools/models/check_edm_export.py` reads 27 and 28 as 26 when it compares
against an older model, and checks the assignment of the pylons and doors. See [../systems/weapon-bays.md](../systems/weapon-bays.md).

## Blender projects

Paths are under `blender_files/`, and `IC` means `blender_files/integrated_collision/`. The
exterior project was checked with `tools/models/check_edm_export.py`. The next six rows were checked by
comparing triangle counts per damage name against the model. The others come from each folder's
README and overall counts.

| Project | Scene | Model | Damage table | EFM | Status |
|---|---|---|---:|---|---|
| `uv_work/f117-exterior-painted-candidate.blend` | `F-117 Exterior` | `f111c24eb3b2` installed | 25 | 25-cell | **Current development source**; glass visibility accepted in DCS |
| `uv_work/f117-cockpit-painted-candidate.blend` | Saved cockpit scene | `340590d438e4` installed | n/a | Existing arguments | **Current cockpit development source**, restored emission |
| `f-117-nighthawk-exterior.blend` (tracked) | `F-117 Exterior` | `991a733a6711` historical | 25 | 25-cell | Original master/baseline; predates replacement UVs and paint |
| `IC/exposed_controls/f-117-nighthawk-exposed-controls.blend` (tracked) | `F-117 Damage Sections` | `b314ca7fa7f6` | 25 | 25-cell | Review copy of the collision only |
| `IC/f-117-nighthawk-integrated-collision.blend` | `F-117 Damage Sections` | `b314ca7fa7f6` | 25 | 25-cell | Review copy of the collision only |
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

For the installed painted development configuration, export the exterior from
`F-117 Exterior` in `blender_files/uv_work/f117-exterior-painted-candidate.blend`
and the cockpit from `blender_files/uv_work/f117-cockpit-painted-candidate.blend`.
The original master paths are historical baselines; exporting them would restore
their older UV/material configuration.

1. Open it in Blender 5.2 with the current updated EDM exporter and the iEDM_10 importer enabled. The
   importer's export hook must include the fix for reopened files (iEDM changelog, Unreleased):
   without it, visibility-animated parts export kilometres out of place.
2. Edit. The collision objects are hidden and drawn as wireframe; Alt+H shows them. Don't hide
   the `Collision` collection, because the exporter skips hidden collections.
3. Export to `Shapes/f-117-nighthawk.edm`. The scene's EDM export path is already set to it.
4. Run `blender -b --python tools/models/check_edm_export.py`. It compares the export with the model at
   git HEAD, and fails if the collision, connectors, lights or boxes changed. Visual changes are
   listed, but don't fail the check.
5. Update **Current state**, then run `python -m pytest tests/test_damage_model.py`.

A historical fresh export of the unedited original master passed the check against `b314ca7fa7f6`. It wasn't
byte-identical, for three reasons:

- The exporter drops triangles with no area, about 2% of the total. The surface area per material
  is unchanged.
- The wheel contacts' gear bones are written as position and rotation argument nodes. The
  contacts sit in the same place with the gear up and down, and within 5 mm mid-travel.
- Node names change. DCS doesn't use them; connector names are unchanged.

`tools/models/build_exterior_blend.py` reconstructs an exterior project from an EDM;
it does not rebuild the painted source pipeline. For painted atlas/material
rebuild instructions, use `texture_sources/uv_work/finish/README.md`.

Don't export from the other projects:

- `F-117 Damage Sections` holds plain meshes for review, without the parent links or collision node
  types the model needs.
- The older `Scene` collision uses names the `Damage` table doesn't have, such as `CABIN_LEFT_SIDE`
  and `ELERON_L`.

`IC/add_damage_sections.py` built `b314ca7fa7f6` by patching the collision section of
`IC/exposed_controls/f-117-nighthawk.edm`. Section changes can now be made in Blender instead.

## Keeping this page current

When the model or the damage cells change:

1. Export the model from `F-117 Exterior`, as described above, and run `tools/models/check_edm_export.py`.
2. Update **Current state**, then add a row to the tables above.
3. Run `python -m pytest tests/test_damage_model.py`.

The test fails if this page names a different model from the installed one, if the Lua table and
model names differ, or if the EFM's cells differ from the model's. It also fails if the built EFM is
older than its source. The EFM checks read `F117_EFM_ROOT` or `bin/efm.proxy.ini`, and skip if
neither finds the source.



