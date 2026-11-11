"""Rewrite each exterior livery's material table from the exterior model.

DCS applies a livery texture only to the materials its description.lua names.
A Blender re-export renames materials (Aircraft_01 -> Aircraft_01.006 and so
on), and any material the livery misses keeps the default texture. This tool
reads every material and its diffuse texture from Shapes/f-117-nighthawk.edm
and lists, in each livery, every material whose texture that livery supplies.

    python tools/models/sync_livery_materials.py          # rewrite the liveries
    python tools/models/sync_livery_materials.py --check  # exit 1 if any are stale
"""
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDM = ROOT / 'Shapes' / 'f-117-nighthawk.edm'
LIVERIES = ROOT / 'Liveries' / 'F-117-NightHawk'
BLOCK = re.compile(r'livery\s*=\s*\{.*?\n\}', re.S)


def edm_materials(path=EDM):
    """Return {material name: diffuse texture name} for a version 10 EDM."""
    data = path.read_bytes()
    if data[:3] != b'EDM' or struct.unpack_from('<H', data, 3)[0] != 10:
        raise ValueError(f'{path}: not a version 10 EDM')
    size = struct.unpack_from('<I', data, 5)[0]
    strings = [s.decode('latin1') for s in data[9:9 + size].split(b'\x00')]
    index = {s: i for i, s in enumerate(strings)}
    name_key, tex_key = index['NAME'], index['TEXTURES']
    materials = {}
    # Material property maps sit at the start of the node data; scan for
    # NAME <string> followed by TEXTURES <count> (channel, -1, <string>, ...).
    start = 9 + size
    end = min(len(data) - 16, start + 400_000)
    p = start
    while p < end:
        if struct.unpack_from('<I', data, p)[0] == name_key:
            value = struct.unpack_from('<I', data, p + 4)[0]
            if value < len(strings):
                for r in range(p + 8, min(p + 808, end)):
                    word = struct.unpack_from('<I', data, r)[0]
                    if word == name_key:
                        break
                    if word == tex_key:
                        count = struct.unpack_from('<I', data, r + 4)[0]
                        channel, _, tex = struct.unpack_from('<iiI', data, r + 8)
                        if 0 < count < 10 and channel == 0 and tex < len(strings):
                            materials[strings[value]] = strings[tex]
                        break
                p += 8
                continue
        p += 1
    return materials


def livery_table(folder, materials):
    """Lua livery table entries for every material this folder can texture."""
    files = {f.stem.lower(): f.stem for f in folder.glob('*.dds')}
    rows = [(m, files[t.lower()]) for m, t in sorted(materials.items(), key=lambda kv: kv[0].lower())
            if t.lower() in files]
    width = max(len(m) for m, _ in rows) + 3
    body = ''.join(f'\t{{{f"{chr(34)}{m}{chr(34)},":<{width}} DIFFUSE, "{tex}", false}};\n'
                   for m, tex in rows)
    return 'livery = {\n' + body + '}'


def sync(check=False):
    materials = edm_materials()
    stale = []
    for desc in sorted(LIVERIES.glob('*/description.lua')):
        newline = '\r\n' if b'\r\n' in desc.read_bytes() else '\n'
        text = desc.read_text(encoding='utf-8')
        new = BLOCK.sub(lambda _: livery_table(desc.parent, materials), text, count=1)
        if new != text:
            stale.append(desc.parent.name)
            if not check:
                desc.write_text(new, encoding='utf-8', newline=newline)
    return stale


if __name__ == '__main__':
    check = '--check' in sys.argv
    stale = sync(check)
    verb = 'stale' if check else 'updated'
    for name in stale:
        print(f'{verb}: {name}')
    print(f'{len(stale)} livery file(s) {verb}')
    sys.exit(1 if check and stale else 0)
