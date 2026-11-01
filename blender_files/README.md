# Active Blender sources

Only the projects associated with currently referenced aircraft models are tracked:

| Blender project | Runtime model |
| --- | --- |
| `integrated_collision/exposed_controls/f-117-nighthawk-exposed-controls.blend` | `Shapes/f-117-nighthawk.edm` |
| `f-117-nighthawk_canopy.blend` | `Shapes/f-117-nighthawk_canopy.edm` |
| `f-117-nighthawk-oblomok.blend` | `Shapes/f-117-nighthawk-oblomok.edm` |

`docs/model-efm-compatibility.md` records which project and scene hold each model,
and which Lua damage table and EFM each model needs.

The exterior model is built by script rather than exported, so do not export it from
Blender. `integrated_collision/damage_sections/README.md` explains how to rebuild it.
The exterior project's `F-117 Damage Sections` scene is a review copy of the installed
collision, and its other scenes hold earlier geometry.
Older collision candidates, the original exterior project, detached-wing projects,
and development outputs remain local and ignored. The aircraft currently selects
a stock ejection seat, so the separate custom seat project is also excluded.

These `.blend` files use Blender compression and are stored directly in Git.
Keep compression enabled when saving future revisions.
Changes to the canopy and wreck projects should be exported with the official Blender
EDM exporter into the corresponding runtime model paths above.

Blender source projects are excluded from the installable runtime ZIP. No source
projects or historical files have been moved or deleted by this tracking setup.

