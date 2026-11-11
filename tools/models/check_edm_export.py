"""Compare an exterior model exported from Blender against a reference model.

Run with Blender 5.2 and the iEDM_10 importer:

    blender -b --python tools/models/check_edm_export.py -- [candidate.edm] [reference.edm | git:REF]

The candidate defaults to Shapes/f-117-nighthawk.edm and the reference to the same file at
git HEAD, so after exporting over the installed model, run it with no arguments.

Collision, connectors, lights and the bounding and light boxes must match, or the script exits
with status 1. The damage cells, the gear contacts and the Lua connector names depend on them.
The left weapon bay is animated by argument 27 and the right by 28 (older models used 26 for both),
so the comparison reads 27 and 28 as 26. A model that uses 27 or 28 must also pass the bay check:
Pylon1 and the left door on 27 only, Pylon2 and the right door on 28 only, and nothing on 26.
Visual differences are reported, but don't fail the check, because changing the visuals is the
point of an edit. Triangles with no area are ignored: the exporter drops them.
"""
import hashlib
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import addon_utils
import bpy

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'Shapes/f-117-nighthawk.edm'
FRAMES = (0, 25, 50, 75, 100, 110, 125, 150, 175, 200)
POSE_TOLERANCE_M = 0.006  # The nose wheel contact is resampled by up to 5 mm mid-travel.
AREA_TOLERANCE_M2 = 0.002
BAY_ARG_ALIASES = {27: 26, 28: 26}  # the left and right weapon bays; see the module docstring

addon_utils.enable('iEDM_10')
from iEDM_10.edm_format import EDMFile  # noqa: E402  (needs the add-on enabled first)


def resolve(argument, default):
    value = argument or default
    if value.startswith('git:'):
        data = subprocess.run(['git', '-C', str(ROOT), 'show', f'{value[4:]}:{MODEL}'],
                              capture_output=True, check=True).stdout
        path = Path(tempfile.gettempdir()) / f'f117-reference-{value[4:].replace("/", "_")}.edm'
        path.write_bytes(data)
        return path
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def args_above(node, aliases=BAY_ARG_ALIASES):
    args = set()
    while node is not None:
        for key in ('posData', 'rotData', 'scaleData', 'visData'):
            for channel in getattr(node, key, None) or []:
                args.add(aliases.get(channel[0], channel[0]))
        node = node.parent
    return tuple(sorted(args))


def bay_report(path):
    """Weapon bay arguments over the pylon connectors and the door collision, with no aliasing."""
    model = EDMFile(str(path))
    pylons = {c.name: args_above(c.parent, {}) for c in model.connectors if c.name in ('Pylon1', 'Pylon2')}
    doors = Counter(args_above(s.parent, {}) for s in model.shellNodes if s.name.startswith('FUSELAGE_BOTTOM'))
    return pylons, doors


def check_bays(path):
    pylons, doors = bay_report(path)
    uses_split = any(set(args) & {27, 28} for args in list(pylons.values()) + list(doors))
    if not uses_split:
        print('INFO bays: one argument (26) drives both bays; the model predates the split')
        return True
    left_ok = pylons.get('Pylon1') == (27,)
    right_ok = pylons.get('Pylon2') == (28,)
    door_ok = sum(doors.values()) == 2 and set(doors) == {(27,), (28,)}
    print(f'{"PASS" if left_ok and right_ok and door_ok else "FAIL"} bays: Pylon1 {pylons.get("Pylon1")}, '
          f'Pylon2 {pylons.get("Pylon2")}, door collision {dict(doors)}')
    return left_ok and right_ok and door_ok


def triangle_area(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return sum(x * x for x in cross) ** 0.5 / 2


def material_key(material):
    textures = tuple(sorted(getattr(t, 'name', '') for t in getattr(material, 'textures', None) or []))
    return (material.material_name, material.blending, material.culling, material.decal,
            repr(material.shadows), textures)


def structure(path):
    model = EDMFile(str(path))
    root = model.root
    shells = Counter((type(s).__name__, s.name, len(getattr(s, 'vertexData', None) or getattr(s, 'data', None) or []),
                      args_above(s.parent)) for s in model.shellNodes)
    visuals = defaultdict(lambda: [0, 0.0, set()])
    for node in model.renderNodes:
        entry = visuals[material_key(node.material)]
        entry[2].add((args_above(node.parent), node.damage_argument))
        vertices, indices = node.vertexData, node.indexData
        for i in range(0, len(indices), 3):
            area = triangle_area(*(vertices[j] for j in indices[i:i + 3]))
            if area > 1e-12:
                entry[0] += 1
                entry[1] += area
    return dict(
        shells=shells,
        connectors=Counter(c.name for c in model.connectors),
        lights=Counter((l.name, args_above(l.parent)) for l in model.lightNodes),
        boxes=[tuple(round(x, 3) for v in box for x in v) for box in (root.scene_bounds_box, root.light_box)
               if box is not None],
        visuals=visuals,
    )


def poses(path):
    """World-space bounds of every mesh at sample frames, as the importer animates them."""
    bpy.ops.wm.read_homefile(use_empty=True)
    for addon in ('io_scene_edm', 'iEDM_10'):
        addon_utils.enable(addon)
    bpy.ops.import_mesh.edm(filepath=str(path))
    scene = bpy.context.scene
    collision = set(bpy.data.collections['Collision'].all_objects)
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        rows = defaultdict(list)
        for obj in scene.objects:
            if obj.type != 'MESH' or not obj.data.vertices:
                continue
            evaluated = obj.evaluated_get(graph)
            points = [evaluated.matrix_world @ v.co for v in evaluated.data.vertices]
            bounds = [min(p[i] for p in points) for i in range(3)] + [max(p[i] for p in points) for i in range(3)]
            if obj in collision:
                key = ('collision', obj.name.split('.')[0])
            else:
                key = ('visual', obj.active_material.name.split('.')[0] if obj.active_material else '')
            rows[key].append(bounds)
        result[frame] = rows
    return result


def compare_poses(reference, candidate):
    worst = defaultdict(float)
    for frame in FRAMES:
        a, b = reference[frame], candidate[frame]
        for key in set(a) | set(b):
            if len(a.get(key, [])) != len(b.get(key, [])):
                # A part was cut in two (the beams that span both bays), so compare what the group covers.
                if not a.get(key) or not b.get(key):
                    worst[key] = float('inf')
                    continue
                cover = [[min(x[i] for x in boxes[key]) if i < 3 else max(x[i] for x in boxes[key]) for i in range(6)]
                         for boxes in (a, b)]
                worst[key] = max(worst[key], max(abs(x - y) for x, y in zip(*cover)))
                continue
            remaining = list(b[key])
            for bounds in a[key]:
                match = min(remaining, key=lambda other: max(abs(x - y) for x, y in zip(bounds, other)))
                remaining.remove(match)
                worst[key] = max(worst[key], max(abs(x - y) for x, y in zip(bounds, match)))
    return worst


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    candidate = resolve(argv[0] if argv else None, MODEL)
    reference = resolve(argv[1] if len(argv) > 1 else None, 'git:HEAD')
    for label, path in (('reference', reference), ('candidate', candidate)):
        print(f'{label}: {path} sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}')
    ref, cand = structure(reference), structure(candidate)
    failures = []
    for key in ('shells', 'connectors', 'lights', 'boxes'):
        if ref[key] == cand[key]:
            print(f'PASS {key}: {sum(ref[key].values()) if isinstance(ref[key], Counter) else len(ref[key])} match')
            continue
        failures.append(key)
        print(f'FAIL {key}')
        if isinstance(ref[key], Counter):
            for item in sorted((ref[key] - cand[key]).elements(), key=repr):
                print('   reference only:', item)
            for item in sorted((cand[key] - ref[key]).elements(), key=repr):
                print('   candidate only:', item)
        else:
            print('   reference', ref[key], '\n   candidate', cand[key])

    if not check_bays(candidate):
        failures.append('bays')

    changed = 0
    for key in sorted(set(ref['visuals']) | set(cand['visuals']), key=repr):
        a = ref['visuals'].get(key, [0, 0.0, set()])
        b = cand['visuals'].get(key, [0, 0.0, set()])
        if abs(a[1] - b[1]) > AREA_TOLERANCE_M2 or a[2] != b[2]:
            changed += 1
            print(f'INFO visual {key[0]} {key[5]}: area {a[1]:.3f} -> {b[1]:.3f} m2, '
                  f'triangles {a[0]} -> {b[0]}, animation {"same" if a[2] == b[2] else "changed"}')
    print(f'{"PASS" if not changed else "INFO"} visuals: {len(ref["visuals"])} material groups, {changed} changed')

    worst = compare_poses(poses(reference), poses(candidate))
    for kind in ('collision', 'visual'):
        keys = [k for k in worst if k[0] == kind]
        moved = sorted((k for k in keys if worst[k] > POSE_TOLERANCE_M), key=lambda k: -worst[k])
        largest = max((worst[k] for k in keys), default=0.0)
        if not moved:
            print(f'PASS {kind} poses: {len(keys)} groups within {POSE_TOLERANCE_M * 1000:.0f} mm '
                  f'at {len(FRAMES)} frames (largest {largest * 1000:.1f} mm)')
            continue
        if kind == 'collision':
            failures.append('collision poses')
        print(f'{"FAIL" if kind == "collision" else "INFO"} {kind} poses:')
        for k in moved:
            print(f'   {k[1]}: up to {worst[k]:.3f} m')
    print('EDM_CHECK_FAILED: ' + ', '.join(failures) if failures else 'EDM_CHECK_OK')
    return 1 if failures else 0


if __name__ == '__main__':
    code = main()
    sys.stdout.flush()
    if code:
        import os
        os._exit(code)
