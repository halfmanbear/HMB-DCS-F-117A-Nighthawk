# Active Blender sources

Only the projects associated with currently referenced aircraft models are tracked:

| Blender project | Runtime model |
| --- | --- |
| `f-117-nighthawk-exterior.blend` | `Shapes/f-117-nighthawk.edm` |
| `Cockpit_F-117.blend` (local, ignored) | `Cockpit/Shape/Cockpit_F-117.edm` |
| `f-117-nighthawk_canopy.blend` | `Shapes/f-117-nighthawk_canopy.edm` |
| `f-117-nighthawk-oblomok.blend` | `Shapes/f-117-nighthawk-oblomok.edm` |

`docs/model-efm-compatibility.md` records which project and scene hold each model,
and which Lua damage table and EFM each model needs.

`f-117-nighthawk-exterior.blend` has one scene, `F-117 Exterior`, which exports the
whole exterior model. `Vehicle` holds the visuals, and `Vehicle/Collision` holds the 25
damage-cell sections, the control-surface shells and the wheel contacts. The collision
objects are hidden and drawn as wireframe; press Alt+H to show them. Don't hide the
`Collision` collection itself: the exporter skips hidden collections, and the model
would lose its damage cells. "Exporting from Blender" in
`docs/model-efm-compatibility.md` gives the steps.

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
textures (2026-11-05). Their images load PNGs from `dist/exterior-texture-remake/sources/`
and `dist/cockpit-texture-remake/sources/`, so keep those folders.

`_archive/` (local, ignored) holds every superseded blend moved out of this folder and
`dist/`: the pre-texture-rework masters, detached-wing, seat and uncompressed copies, and
`dist` checkpoints and originals.
