"""Add an arg-26 fallback without re-exporting geometry or materials.

Run in Blender (iEDM_10 installed):
  blender -b --python tools/models/weapon_bay_replay.py -- INPUT.edm OUTPUT.edm

904/905 carry left/right positions; 906 carries max(left, right). Each existing
animation becomes 26 * inverse(906) * individual (translations add). With only
26 supplied, as for AI or an old track, the original paired motion is restored.
With all four supplied, the first two channels cancel exactly. The bay lamps
follow the shared standard argument, including on AI. Cockpit lights stay per bay.

Only animation channel byte ranges change. All geometry, materials, collision,
connectors and node indices remain byte-for-byte intact. The parser records the
channel offsets, so this does not search for magic byte patterns in the model.
"""
import copy
import struct
import sys
from pathlib import Path

import addon_utils
from mathutils import Quaternion, Vector

addon_utils.enable('iEDM_10')
from iEDM_10.edm_format import EDMFile
from iEDM_10.edm_format.types.core_animation import ArgAnimationBase

LEFT, RIGHT, CANCEL = 904, 905, 906


def read_offsets(path):
    offsets = []
    original_base = ArgAnimationBase.read.__func__

    def base_read(cls, stream):
        base = original_base(cls, stream)
        offsets.append(stream.tell())
        return base

    ArgAnimationBase.read = classmethod(base_read)
    try:
        model = EDMFile(str(path))
    finally:
        ArgAnimationBase.read = classmethod(original_base)
    nodes = [n for n in model.nodes if hasattr(n, 'base')]
    assert len(nodes) == len(offsets)
    return model, dict(zip((id(n) for n in nodes), offsets))


def channel_bytes(channels, rotation=False):
    data = struct.pack('<I', len(channels))
    for arg, keys in channels:
        data += struct.pack('<II', arg, len(keys))
        for key in keys:
            value = tuple(key.value)
            if rotation:
                value = value[1:] + value[:1]  # EDM stores xyzw
            data += struct.pack('<' + 'd' * (len(value) + 1), key.frame, *value)
    return data


def evaluate(channels, args, rotation=False):
    result = Quaternion() if rotation else Vector((0, 0, 0))
    for arg, keys in channels:
        t = args.get(arg, 0)
        value = keys[0].value.copy()
        for a, b in zip(keys, keys[1:]):
            if t >= b.frame:
                value = b.value.copy()
            elif t > a.frame:
                f = (t - a.frame) / (b.frame - a.frame)
                value = a.value.slerp(b.value, f) if rotation else a.value.lerp(b.value, f)
                break
            else:
                break
        result = result @ value if rotation else result + value
    return result


def patch(source, target):
    model, offsets = read_offsets(source)
    data = source.read_bytes()
    all_args = {a for n in model.nodes for kind in ('posData', 'rotData', 'scaleData', 'visData')
                for a, _ in getattr(n, kind, [])}
    assert not all_args.intersection((LEFT, RIGHT, CANCEL)), 'model already patched or arguments occupied'
    assert model.root.maxArgPlusOne > CANCEL
    changes = []
    tested = 0
    for node in model.nodes:
        pos, rot = getattr(node, 'posData', []), getattr(node, 'rotData', [])
        if not any(a in (27, 28) for a, _ in pos + rot):
            continue
        assert not node.scaleData
        old_bytes = channel_bytes(pos) + channel_bytes(rot, True) + struct.pack('<I', 0)
        start = offsets[id(node)]
        assert data[start:start + len(old_bytes)] == old_bytes, node.name
        new_channels = []
        for channels, rotation in ((pos, False), (rot, True)):
            if not channels:
                new_channels.append([])
                continue
            assert len(channels) == 1 and channels[0][0] in (27, 28)
            old_arg, keys = channels[0]
            individual = LEFT if old_arg == 27 else RIGHT
            inverse = copy.deepcopy(keys)
            for key in inverse:
                key.value = key.value.inverted() if rotation else -key.value
            replacement = [(26, keys), (CANCEL, inverse), (individual, keys)]
            # Check every combination, including one bay closing while the other opens.
            for l in range(21):
                for r in range(21):
                    left, right = l / 20, r / 20
                    args = {26: max(left, right), CANCEL: max(left, right), LEFT: left, RIGHT: right}
                    expected = evaluate(channels, {old_arg: left if old_arg == 27 else right}, rotation)
                    actual = evaluate(replacement, args, rotation)
                    error = min((actual - expected).magnitude, (actual + expected).magnitude) if rotation else (actual - expected).length
                    assert error < 2e-6, (node.name, args, error)
            for i in range(101):
                t = i / 100
                expected = evaluate(channels, {old_arg: t}, rotation)
                actual = evaluate(replacement, {26: t}, rotation)
                error = min((actual - expected).magnitude, (actual + expected).magnitude) if rotation else (actual - expected).length
                assert error < 2e-6, (node.name, 'AI', t, error)
            new_channels.append(replacement)
        changes.append((start, len(old_bytes), channel_bytes(new_channels[0]) + channel_bytes(new_channels[1], True) + struct.pack('<I', 0)))
        tested += 1
    # Visibility records retain their lengths: only replace the argument number.
    # Record their ranges through the parser, rather than guessing node offsets.
    from iEDM_10.edm_format.types.core_animation import ArgVisibilityNode
    original = ArgVisibilityNode._read_AANVisibilityArg
    descriptor = ArgVisibilityNode.__dict__['_read_AANVisibilityArg']
    vis_offsets = []

    def visibility(stream):
        start = stream.tell()
        result = original(stream)
        if result[0] in (27, 28):
            vis_offsets.append(start)
        return result

    ArgVisibilityNode._read_AANVisibilityArg = staticmethod(visibility)
    try:
        EDMFile(str(source))
    finally:
        ArgVisibilityNode._read_AANVisibilityArg = descriptor
    changes.extend((offset, 4, struct.pack('<I', 26)) for offset in vis_offsets)
    assert tested == 20 and len(vis_offsets) == 4, (tested, vis_offsets)
    for start, length, replacement in sorted(changes, reverse=True):
        data = data[:start] + replacement + data[start + length:]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    check = EDMFile(str(target))
    assert len(check.nodes) == len(model.nodes)
    assert len(check.connectors) == len(model.connectors)
    args = {a for n in check.nodes for kind in ('posData', 'rotData', 'scaleData', 'visData')
            for a, _ in getattr(n, kind, [])}
    assert {27, 28}.isdisjoint(args)
    assert {26, LEFT, RIGHT, CANCEL}.issubset(args)
    print('BAY_REPLAY_OK', tested, 'transforms: 441 asymmetric and 101 AI positions each;', len(changes), 'animation-only edits')


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    patch(Path(argv[0]), Path(argv[1]))
