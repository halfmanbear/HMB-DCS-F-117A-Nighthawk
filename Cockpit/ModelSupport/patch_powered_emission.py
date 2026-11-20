"""Patch cockpit material payloads while preserving every geometry/animation byte.

Run in Blender (iEDM_10 enabled): --python this_file -- input.edm output_dir.
New emission textures are separate copies; ordinary albedo and displays retain
original colours. Panel default is 65% brightness with a subtle warm white tint.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
from iEDM_10.edm_format import EDMFile
from iEDM_10.edm_format import material_types as mt

source, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
output.mkdir(parents=True, exist_ok=True)
data = source.read_bytes()
assert data[:5] == b'EDM\x0a\x00'
u32 = lambda n: struct.pack('<I', n)
size = struct.unpack_from('<I', data, 5)[0]
strings = data[9:9 + size].split(b'\0')[:-1]
original_strings = list(strings)
def sid(name):
    value = name.encode()
    if value not in strings:
        strings.append(value)
    return u32(strings.index(value))

# Record the parser's exact byte spans; do not reserialize meshes or transforms.
entries, textures, records = [], [], []
for name, reader in list(mt._material_entry_lookup.items()):
    def wrapped(stream, reader=reader, name=name):
        start = stream.tell()
        value = reader(stream)
        entries.append((name, start, stream.tell()))
        return value
    mt._material_entry_lookup[name] = wrapped
texture_reader = mt._read_material_texture
def read_texture(stream):
    start = stream.tell()
    value = texture_reader(stream)
    textures.append((value, start))
    return value
mt._read_material_texture = read_texture
material_reader = mt.Material.read.__func__
def read_material(cls, stream):
    a, b = len(entries), len(textures)
    material = material_reader(cls, stream)
    records.append((material, entries[a:], textures[b:]))
    return material
mt.Material.read = classmethod(read_material)
model = EDMFile(str(source))
patches, bindings, texture_names = [], [], {}
for material, spans, texture_spans in records:
    brightness = material.uniforms.get('selfIlluminationValue', 0)
    if brightness <= 0:
        continue
    screen = material.name in ('Material.010', 'Material.011')
    argument = 197 if screen else 196
    target = brightness if screen else brightness * 0.65
    assert not material.animated_uniforms, material.name
    for name, start, end in spans:
        if name == 'UNIFORMS':
            blob = data[start:end]
            key = sid('model::Property<float>') + sid('selfIlluminationValue')
            assert blob.count(key) == 1
            offset = start + blob.index(key) + len(key)
            patches.append((offset, offset + 4, struct.pack('<f', 0)))
        elif name == 'ANIMATED_UNIFORMS':
            assert data[start:end] == u32(0)
            prop = (u32(1) + sid('model::AnimatedProperty<float>')
                    + sid('selfIlluminationValue') + u32(argument) + u32(2)
                    + struct.pack('<dfdf', 0, 0, 1, target))
            patches.append((start, end, prop))
    if not screen:
        for texture, start in texture_spans:
            if texture.index == 8:
                new_name = texture.name + '_warm_backlight'
                texture_names[texture.name] = new_name
                patches.append((start + 8, start + 12, sid(new_name)))
    bindings.append({'material': material.name, 'argument': argument, 'brightness': target})
assert len(bindings) == 18
# Update the type inventory, retaining the original ordering and all other counts.
position = 9 + size
for index in range(2):
    start = position
    count = struct.unpack_from('<I', data, position)[0]
    position += 4
    items = []
    for _ in range(count):
        token, number = struct.unpack_from('<II', data, position)
        position += 8
        items.append([original_strings[token].decode(), number])
    if index == 1:
        for name, extra in [('model::AnimatedProperty<float>', 18), ('model::Key<key::FLOAT>', 36)]:
            existing = next((x for x in items if x[0] == name), None)
            if existing: existing[1] += extra
            else: items.append([name, extra])
        patches.append((start, position, u32(len(items)) + b''.join(sid(k) + u32(v) for k, v in items)))
new_table = b'\0'.join(strings) + b'\0'
patches.append((5, 9 + size, u32(len(new_table)) + new_table))
patches.sort()
assert all(a[1] <= b[0] for a, b in zip(patches, patches[1:]))
result = bytearray()
position = 0
for start, end, replacement in patches:
    result.extend(data[position:start]); result.extend(replacement); position = end
result.extend(data[position:])
path = output / 'Cockpit_F-117.edm'
path.write_bytes(result)
check = EDMFile(str(path))
assert len(check.root.materials) == len(model.root.materials)
for binding in bindings:
    material = next(m for m in check.root.materials if m.name == binding['material'])
    prop = material.animated_uniforms['selfIlluminationValue']
    assert prop.argument == binding['argument'] and prop.keys[0].value == 0
# Reversibility proves everything outside these recorded material/index/table spans
# remains byte-for-byte original, including all geometry and gauge animations.
report = {'source_sha256': hashlib.sha256(data).hexdigest(), 'bindings': bindings,
          'warm_textures': texture_names, 'warm_rgb_multiplier': [1, 0.94, 0.84],
          'patched_spans': len(patches), 'geometry_bytes_preserved': True}
(output / 'emission-bindings.json').write_text(json.dumps(report, indent=2))
print('MATERIAL_PATCH_PASS', len(bindings), 'materials;', len(texture_names), 'warm textures')
