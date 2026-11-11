# Active Blender sources

The exterior painted candidate also contains the installed
[USAF HO 830 default livery](../texture_sources/uv_work/finish/USAF_DEFAULT.md).

2026-11-07: both `uv_work/f117-*-painted-candidate.blend` projects are current
with the installed control-artwork and exterior HUD material repairs.
See [installation and validation](../texture_sources/uv_work/finish/glass-debug/control-art-repair.md).

The 2026-11-05 replacement-UV review projects (`uv_work/f117-*-replacement-uv-review.blend`)
were deleted on 2026-11-07; the painted projects below superseded them. Their UV
templates, assignment tables and checks are still described in
[`texture_sources/uv_work/README.md`](../texture_sources/uv_work/README.md).
The original masters remain unchanged as baselines. The painted projects below
are the current development export sources.

Sources associated with the currently referenced aircraft models (the `uv_work`
projects remain local/ignored):

| Blender project | Runtime model |
| --- | --- |
| `uv_work/f117-exterior-painted-candidate.blend` | `Shapes/f-117-nighthawk.edm` |
| `uv_work/f117-cockpit-painted-candidate.blend` | `Cockpit/Shape/Cockpit_F-117.edm` |
| `f-117-nighthawk_canopy.blend` | `Shapes/f-117-nighthawk_canopy.edm` |
| `f-117-nighthawk-oblomok.blend` | `Shapes/f-117-nighthawk-oblomok.edm` |

`docs/models/model-efm-compatibility.md` records which project and scene hold each model,
and which Lua damage table and EFM each model needs.

The exterior painted candidate retains the original master's `F-117 Exterior`
scene and exports the whole exterior model. `Vehicle` holds the visuals, and
`Vehicle/Collision` holds the 25
damage-cell sections, the control-surface shells and the wheel contacts. The collision
objects are hidden and drawn as wireframe; press Alt+H to show them. Don't hide the
`Collision` collection itself: the exporter skips hidden collections, and the model
would lose its damage cells. "Exporting from Blender" in
`docs/models/model-efm-compatibility.md` gives the steps.

`integrated_collision/exposed_controls/f-117-nighthawk-exposed-controls.blend` is kept
as history. Its scenes are imports of earlier models and review copies, so don't export
from it.
Older collision candidates, the original exterior project, detached-wing projects,
and development outputs remain local and ignored. The aircraft currently selects
a stock ejection seat, so the separate custom seat project is also excluded.

These `.blend` files use Blender compression and are stored directly in Git.
Keep compression enabled when saving future revisions.
Changes to the canopy and wreck projects should be exported with the official Blender
EDM exporter into the corresponding runtime model paths above.

Blender source projects are excluded from the installable runtime ZIP. No source
projects or historical files have been moved or deleted by this tracking setup.


Both `f-117-nighthawk-exterior.blend` and `Cockpit_F-117.blend` hold the reworked
textures (2026-11-05). Their images load PNGs from `work/exterior-texture-remake/sources/`
and `work/cockpit-texture-remake/sources/`, so keep those folders.

`_archive/` (local, ignored) holds every superseded blend moved out of this folder and
`dist/`: the pre-texture-rework masters, detached-wing, seat and uncompressed copies, and
`dist` checkpoints and originals.

The subsequent UV checker and paint candidates live locally in `uv_work/`.
`f117-exterior-painted-candidate.blend` and
`f117-cockpit-painted-candidate.blend` use fresh UVs, 34 new EDM material groups
and packed albedo/RoughMet/normal maps on the existing meshes. Their build and
save/reopen checks are in `texture_sources/uv_work/finish/`. These are the current
source projects for the installed development models; the original masters are
retained as baselines. Use Blender 5.2 and the current updated EDM exporter.
The user accepted corrected HUD/gauge glass visibility in DCS on 2026-11-06 at
12:30. The later matched dusk comparison exposed lost cockpit emission; 18
object-specific settings are now restored in the painted cockpit source and
installed EDM, with DCS dusk retesting pending.
Final artwork, gauge calibration, night lighting and broader runtime
acceptance remain open. Read `texture_sources/uv_work/finish/README.md` for the
glass configuration, installed hashes and backups before export or DCS use.
