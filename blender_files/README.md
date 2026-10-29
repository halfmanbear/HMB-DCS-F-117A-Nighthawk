# Active Blender sources

Only the projects associated with currently referenced aircraft models are tracked:

| Blender project | Runtime model |
| --- | --- |
| `integrated_collision/exposed_controls/f-117-nighthawk-exposed-controls.blend` | `Shapes/f-117-nighthawk.edm` |
| `f-117-nighthawk_canopy.blend` | `Shapes/f-117-nighthawk_canopy.edm` |
| `f-117-nighthawk-oblomok.blend` | `Shapes/f-117-nighthawk-oblomok.edm` |

The exterior project's companion EDM matches the installed exterior model byte
for byte. This project contains the current exposed-control collision geometry.
Older collision candidates, the original exterior project, detached-wing projects,
and development outputs remain local and ignored. The aircraft currently selects
a stock ejection seat, so the separate custom seat project is also excluded.

These `.blend` files use Blender compression and are stored directly in Git.
Keep compression enabled when saving future revisions.
Changes to the active sources should be exported with the official Blender EDM
exporter into the corresponding runtime model paths above.

Blender source projects are excluded from the installable runtime ZIP. No source
projects or historical files have been moved or deleted by this tracking setup.

