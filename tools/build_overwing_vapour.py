"""Build Shapes/f-117-nighthawk_overwingVapor.owv from the exterior model.

The real aircraft's overwing condensation forms as one cloud over the upper
aft body and inner wings. In photographs of high-g passes it starts behind
the canopy, is densest on the centreline just ahead of the ruddervator roots,
and thins out across the inner wings. The leading-edge vortices are drawn
separately by the EFM.

This places spawn points on the top skin of the model and weights them with
that cloud shape, where the weight says how early vapour forms at a point.
DCS draws one of ten slices of the file, picked by the current vapour power.
The slices are built so the cloud first appears on the aft centreline and
spreads forward and outward as the power rises, at most MAX_POINTS points in
each. It needs Blender 4.5 or later and the Blender_iEDM_10 add-on
(https://github.com/halfmanbear/Blender_iEDM_10), which reads the EDM and
writes the .owv:

    blender --background --factory-startup --python tools/build_overwing_vapour.py
        -- <Blender_iEDM_10 folder> [output.owv]

The three header values with no known meaning are kept from the file the
model shipped with.
"""

import math
import sys
from pathlib import Path

import bpy

MOD = Path(__file__).resolve().parents[1]
EDM = MOD / "Shapes" / "f-117-nighthawk.edm"
OWV = MOD / "Shapes" / "f-117-nighthawk_overwingVapor.owv"

# Cloud shape, in DCS model axes (x forward from the model origin, z right).
FRONT_START = 3.0  # behind the canopy (canopy aft edge is near x = 4.5)
FRONT_FULL = 0.0
REAR_FULL = -4.6
REAR_END = -5.8  # ruddervator root leading edge
HALF_WIDTH = 3.0  # lateral 1/e distance; the cloud covers the inner wings
MIN_WEIGHT = 0.03
SPACING = 0.10
MAX_POINTS = 2500  # per slice; the file shipped with the model used 2500
HEADER_EXTRA = (0.0, -0.18548858165740967, -5.449772189081159e-08)


def smoothstep(edge0, edge1, x):
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def cloud_weight(x, z):
    along = smoothstep(FRONT_START, FRONT_FULL, x) * smoothstep(REAR_END, REAR_FULL, x)
    aft_bias = 0.6 + 0.4 * smoothstep(1.5, -3.5, x)
    return along * aft_bias * math.exp(-((z / HALF_WIDTH) ** 2))


def main():
    args = sys.argv[sys.argv.index("--") + 1 :]
    sys.path.insert(0, str(Path(args[0]).resolve()))
    output = Path(args[1]) if len(args) > 1 else OWV

    import iEDM_10
    from iEDM_10.owv.owv_format import build_slices, from_slices, write_owv
    from iEDM_10.owv.owv_sampling import SampleSettings, sample_objects

    iEDM_10.register()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_mesh.edm(filepath=str(EDM))
    meshes = [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and not any(c.name == "Collision" for c in obj.users_collection)
    ]
    settings = SampleSettings(spacing=SPACING, weight_group="", top_only=True)
    sampled = sample_objects(meshes, bpy.context.evaluated_depsgraph_get(), settings)
    points = []
    for point in sampled:
        weight = cloud_weight(point[0], point[2])
        if weight >= MIN_WEIGHT:
            points.append((*point[:6], weight))
    slices = build_slices(points, MAX_POINTS)
    write_owv(output, from_slices(slices, HEADER_EXTRA))
    counts = [len(part) for part in slices]
    print(f"Wrote {sum(counts)} spawn points in slices {counts} to {output}")


main()
