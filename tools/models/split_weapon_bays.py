"""Give each weapon bay its own animation argument in the exterior Blender scene.

Run with Blender 5.2, the iEDM_10 importer and the ED EDM exporter installed:

    blender -b <exterior.blend> --python tools/models/split_weapon_bays.py -- [--save OUT.blend] [--export OUT.edm]

The model drove both bays from argument 26: two separate door chains, but one trapeze assembly
that carried both pylon connectors. The EFM now drives the left bay on 27 and the right bay on
28, and writes 26 as "either bay open" with nothing in the model animated by it. DCS hides the
stores unless the standard bay argument 26 is open, so a store whose own bay is open would
otherwise vanish while the other bay was shut. This script moves the left door chain, lights and
trapeze to 27 and the right ones to 28:

* the door chains (`Bone.161` left, `Bone.157` right) and the lights over them
  (`v_VisibilityNode.101/.104` left, `.102/.103` right) only change argument;
* the trapeze chain (`Bone.191` and below) goes to 27 and is duplicated on 28 with the same keys.
  Every trapeze motion is about the lateral axis, so the copy moves exactly like the original. The
  right-hand meshes and the `Pylon2` connector move to the copy, the beams that span both bays are
  cut at the centre line.

Nothing is saved or exported unless asked: without --save and --export it only checks the result.
The script does nothing to a scene that already has argument 27 or 28 animations, and expects the
parts to start on 26.

The scene is checked before it is changed (names and sides as expected) and after: with both
arguments on the same frame every mesh must sit where it did, and with the right bay's animation
removed the left bay must still move while the right stays closed.
"""
import argparse
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ORIGINAL_ARG, LEFT_ARG, RIGHT_ARG = 26, 27, 28
FRAMES = (0, 100, 150, 170, 185, 200)
TOLERANCE_M = 1e-4

RIGHT_DOOR_ROOT = 'Bone.157'     # FUSELAGE_BOTTOM, the right door
LEFT_DOOR_ROOT = 'Bone.161'      # FUSELAGE_BOTTOM.001, the left door
LIGHTS = {'v_VisibilityNode.101': 'left', 'v_VisibilityNode.102': 'right',
          'v_VisibilityNode.103': 'right', 'v_VisibilityNode.104': 'left'}
TRAPEZE_ROOT = 'Bone.191'
RIGHT_CONNECTOR_TRANSFORM = 'Connector Transform_tf.007'   # holds Pylon2
LEFT_CONNECTOR_TRANSFORM = 'Connector Transform_tf.006'    # holds Pylon1
# Blender +Y is the aircraft's left (Bay_Left sits at +Y).


def descendants(obj):
    for child in obj.children:
        yield child
        yield from descendants(child)


def side_of(obj):
    """'left', 'right' or 'both' from the mesh's lateral extent at the current frame."""
    ys = [(obj.matrix_world @ Vector(c))[1] for c in obj.bound_box]
    if min(ys) > -0.01:
        return 'left'
    if max(ys) < 0.01:
        return 'right'
    return 'both'


def action_of(obj):
    data = obj.animation_data
    return data.action if data and data.action else None


def set_argument(obj, arg):
    action = action_of(obj)
    assert action is not None, f'{obj.name} has no action'
    assert action.users == 1, f'{obj.name} shares action {action.name}'
    old = action.get('argument')
    action.name = f'{arg}_{action.name.split("_", 1)[1]}'
    if old is not None:
        action['argument'] = arg if isinstance(old, int) else str(arg)


def copy_with_action(obj, arg):
    new = obj.copy()
    for collection in obj.users_collection:
        collection.objects.link(new)
    data = new.animation_data
    action = obj.animation_data.action
    slot = obj.animation_data.action_slot
    copy = action.copy()
    copy.name = f'{arg}_{action.name.split("_", 1)[1]}'
    old = action.get('argument')
    if old is not None:
        copy['argument'] = arg if isinstance(old, int) else str(arg)
    data.action = copy
    if slot is not None:
        data.action_slot = next(s for s in copy.slots if s.identifier == slot.identifier)
    return new


def keep_half(obj, left):
    """Cut a mesh at the aircraft centre line and keep one side."""
    matrix = obj.matrix_world
    inverse = matrix.inverted()
    centre = inverse @ Vector((0.0, 0.0, 0.0))
    normal = (matrix.to_3x3().transposed() @ Vector((0.0, 1.0, 0.0))).normalized()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geometry, plane_co=centre, plane_no=normal, dist=1e-6,
                           clear_inner=left, clear_outer=not left)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def evaluated_bounds(obj):
    """Min and max corner of an evaluated object in world space; an empty is a point."""
    if obj.type == 'MESH':
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    else:
        corners = [obj.matrix_world.translation.copy()]
    return [min(c[i] for c in corners) for i in range(3)] + [max(c[i] for c in corners) for i in range(3)]


def pose(scene, frame, names):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    return {name: evaluated_bounds(bpy.data.objects[name].evaluated_get(graph)) for name in names}


def worst(a, b, names):
    return max((abs(x - y) for n in names for x, y in zip(a[n], b[n])), default=0.0)


def split(scene):
    scene.frame_set(0)
    objects = bpy.data.objects
    already = [a.name for a in bpy.data.actions if a.name.startswith((f'{LEFT_ARG}_', f'{RIGHT_ARG}_'))]
    if already:
        print('SPLIT_SKIPPED: argument', LEFT_ARG, 'or', RIGHT_ARG, 'already animated by', already[:3])
        return False

    # Sides as expected.
    for root, expected in ((RIGHT_DOOR_ROOT, 'right'), (LEFT_DOOR_ROOT, 'left')):
        meshes = [o for o in descendants(objects[root]) if o.type == 'MESH' and o.data.vertices]
        assert meshes and {side_of(m) for m in meshes} <= {expected, 'both'} and any(side_of(m) == expected for m in meshes), \
            f'{root} is not the {expected} door'
    for name, expected in LIGHTS.items():
        light = next(o for o in descendants(objects[name]) if o.type == 'LIGHT')
        y = light.matrix_world.translation.y
        assert (y > 0) == (expected == 'left'), f'{name} is not a {expected} light'
    assert objects['Pylon1'].matrix_world.translation.y > 0 > objects['Pylon2'].matrix_world.translation.y
    assert objects['Pylon1'].parent == objects[LEFT_CONNECTOR_TRANSFORM]
    assert objects['Pylon2'].parent == objects[RIGHT_CONNECTOR_TRANSFORM]
    for name in (RIGHT_DOOR_ROOT, LEFT_DOOR_ROOT, TRAPEZE_ROOT, *LIGHTS):
        assert action_of(objects[name]), name
        assert action_of(objects[name]).name.startswith(f'{ORIGINAL_ARG}_'), name

    chain = [objects[TRAPEZE_ROOT]] + [o for o in descendants(objects[TRAPEZE_ROOT]) if o.type == 'EMPTY' and action_of(o)]
    chain_set = set(chain)
    meshes = [o for o in descendants(objects[TRAPEZE_ROOT]) if o.type == 'MESH']
    connectors = [objects[LEFT_CONNECTOR_TRANSFORM], objects[RIGHT_CONNECTOR_TRANSFORM]]
    for mesh in meshes:
        assert mesh.parent in chain_set, f'{mesh.name} is not attached to the trapeze chain'
    sides = {m.name: side_of(m) for m in meshes}
    for connector in connectors:
        assert connector.parent in chain_set, connector.name
    print('TRAPEZE chain', [o.name for o in chain])
    print('TRAPEZE sides', sides)

    part_side = dict(sides)
    part_side.update({'Pylon1': 'left', 'Pylon2': 'right'})
    for root, side in ((RIGHT_DOOR_ROOT, 'right'), (LEFT_DOOR_ROOT, 'left')):
        part_side.update({o.name: side for o in descendants(objects[root]) if o.type == 'MESH'})
    watched = list(part_side)
    before = {f: pose(scene, f, watched) for f in FRAMES}

    # Doors and lights: argument only. The trapeze chain becomes the left one and is copied for the right.
    for root, arg in ((LEFT_DOOR_ROOT, LEFT_ARG), (RIGHT_DOOR_ROOT, RIGHT_ARG)):
        for obj in [objects[root], *[o for o in descendants(objects[root]) if action_of(o)]]:
            set_argument(obj, arg)
    for name, side in LIGHTS.items():
        set_argument(objects[name], LEFT_ARG if side == 'left' else RIGHT_ARG)
    scene.frame_set(0)
    copies = {}
    for obj in chain:  # parents before children
        new = copy_with_action(obj, RIGHT_ARG)
        new.parent = copies.get(obj.parent, obj.parent)
        copies[obj] = new
    for obj in chain:
        set_argument(obj, LEFT_ARG)

    # Right trapeze: the copy of the chain made above, carrying the right-hand parts.
    bpy.context.view_layer.update()
    pieces = []
    for mesh in meshes:
        side = sides[mesh.name]
        if side == 'right':
            mesh.parent = copies[mesh.parent]
        elif side == 'both':
            half = mesh.copy()
            half.data = mesh.data.copy()
            half.name = mesh.name + '.R'
            for collection in mesh.users_collection:
                collection.objects.link(half)
            half.parent = copies[mesh.parent]
            keep_half(half, left=False)
            keep_half(mesh, left=True)
            pieces.append(half.name)
    objects[RIGHT_CONNECTOR_TRANSFORM].parent = copies[objects[RIGHT_CONNECTOR_TRANSFORM].parent]
    bpy.context.view_layer.update()
    print('SPLIT moved to', RIGHT_ARG, ':', [m.name for m in meshes if sides[m.name] == 'right'], 'cut:', pieces)

    # Every part must still sit where it did with both arguments on the same frame.
    after = {f: pose(scene, f, watched) for f in FRAMES}
    drift = max(worst(before[f], after[f], [n for n in watched if part_side[n] != 'both']) for f in FRAMES)
    assert drift < TOLERANCE_M, f'parts moved by {drift:.6f} m'
    for name in (n for n in watched if part_side[n] == 'both'):
        halves = [bpy.data.objects[name], bpy.data.objects[name + '.R']]
        for f in FRAMES:
            scene.frame_set(f)
            bpy.context.view_layer.update()
            graph = bpy.context.evaluated_depsgraph_get()
            corners = [h.evaluated_get(graph).matrix_world @ Vector(c) for h in halves for c in h.bound_box]
            union = [min(c[i] for c in corners) for i in range(3)] + [max(c[i] for c in corners) for i in range(3)]
            # Compare the union to the original with the cut ignored: the lateral extent stays, depth and length must match.
            for i in (0, 2):
                assert abs(union[i] - before[f][name][i]) < TOLERANCE_M and abs(union[i + 3] - before[f][name][i + 3]) < TOLERANCE_M, \
                    f'{name} cut changed its pose at frame {f}'
    print(f'POSES unchanged to {drift * 1000:.4f} mm at {len(FRAMES)} frames')

    # Independence: with the right bay's animation removed the left bay still moves and the right stays shut.
    right_objects = [o for o in bpy.data.objects if action_of(o) and action_of(o).name.startswith(f'{RIGHT_ARG}_')
                     and not o.name.startswith('v_')]
    left_names = [n for n in watched if part_side[n] in ('left', 'both')]  # a cut beam keeps its left half's name
    right_names = [n for n in watched if part_side[n] == 'right'] + [n + '.R' for n in watched if part_side[n] == 'both']
    watched_all = watched + [n for n in right_names if n.endswith('.R')]
    saved = [(o, o.animation_data.action, o.animation_data.action_slot) for o in right_objects]
    closed = pose(scene, 0, watched_all)
    for o in right_objects:
        o.animation_data.action = None
    open_left = pose(scene, 200, watched_all)
    for o, action, slot in saved:
        o.animation_data.action = action
        if slot is not None:
            o.animation_data.action_slot = slot
    both_open = pose(scene, 200, watched_all)
    assert worst(open_left, both_open, left_names) < TOLERANCE_M, 'left bay depends on the right bay animation'
    assert worst(open_left, closed, right_names) < TOLERANCE_M, 'right bay moves without its own animation'
    assert worst(both_open, closed, right_names) > 0.1, 'right bay does not move with its animation'
    print('INDEPENDENT: left', len(left_names), 'parts and right', len(right_names), 'parts move on their own argument')
    scene.frame_set(0)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save')
    parser.add_argument('--export')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    scene = bpy.context.scene
    changed = split(scene)
    if args.save and changed:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.save).resolve()), compress=True)
        print('SAVED', args.save)
    if args.export:
        import io_scene_edm
        messages = []

        class Reporter:
            def report(self, level, message):
                messages.append((sorted(level), message))

        target = Path(args.export).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        result = io_scene_edm.run_edm_export(str(target), bpy.context, Reporter(), run_model_viewer=False)
        for message in messages:
            print('EXPORT', message)
        assert result == {'FINISHED'} and target.is_file(), f'export failed: {result}'
        print('EXPORTED', target, target.stat().st_size)
    print('SPLIT_OK')


main()
