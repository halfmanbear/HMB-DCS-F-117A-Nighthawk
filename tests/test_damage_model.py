"""The Lua damage table and the EDM collision names must match, or DCS rejects the damage model."""
import hashlib
import importlib.util
import os
import re
import struct
import unittest
import wave
from pathlib import Path

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
EDM = ROOT / 'Shapes/f-117-nighthawk.edm'
_spec = importlib.util.spec_from_file_location('package_release', ROOT / 'tools/package_release.py')
package_release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(package_release)
STANDARD_CELLS = {
    'NOSE_CENTER': 0, 'COCKPIT': 3, 'GEAR_F': 8, 'FUSELAGE_LEFT_SIDE': 9, 'FUSELAGE_RIGHT_SIDE': 10,
    'ENGINE_L': 11, 'ENGINE_R': 12, 'GEAR_L': 15, 'GEAR_R': 16, 'WING_L_OUT': 23, 'WING_R_OUT': 24,
    'AILERON_L': 25, 'AILERON_R': 26, 'WING_L_IN': 35, 'WING_R_IN': 36, 'FLAP_L': 37, 'FLAP_R': 38,
    'RUDDER_L': 53, 'RUDDER_R': 54, 'TAIL_LEFT_SIDE': 56, 'TAIL_RIGHT_SIDE': 57, 'FUSELAGE_BOTTOM': 82,
    'WHEEL_F': 83, 'WHEEL_L': 84, 'WHEEL_R': 85,
}


def edm_collision_nodes(path):
    """Walk the collision section. It ends the file, or is followed by another section such as
    LIGHT_NODES, depending on which tool wrote the model."""
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 5)[0]
    strings = raw[9:9 + size - 1].split(b'\0')
    shell, segments = strings.index(b'model::ShellNode'), strings.index(b'model::SegmentsNode')
    sections = {i for i, s in enumerate(strings) if s.endswith(b'_NODES') or s == b'CONNECTORS'}
    marker = struct.pack('<I', strings.index(b'SHELL_NODES'))
    start = raw.rfind(marker)
    while start > 0:
        nodes = walk(raw, start + 8, struct.unpack_from('<I', raw, start + 4)[0], shell, segments, sections)
        if nodes is not None:
            return nodes
        start = raw.rfind(marker, 0, start)
    raise AssertionError('collision section not found')


def walk(raw, pos, count, shell, segments, sections):
    nodes = []
    try:
        for _ in range(count):
            kind = struct.unpack_from('<I', raw, pos)[0]
            length = struct.unpack_from('<I', raw, pos + 4)[0]
            name = raw[pos + 8:pos + 8 + length].decode('ascii')
            pos += 8 + length + 12  # version, empty properties, parent
            if kind == segments:
                pos += 4 + struct.unpack_from('<I', raw, pos)[0] * 24
                nodes.append(('segments', name))
            elif kind == shell:
                pos += 4 + 27
                vertices = struct.unpack_from('<I', raw, pos)[0]
                pos += 8 + vertices * struct.unpack_from('<I', raw, pos + 4)[0] * 4
                index_size = {0: 1, 1: 2, 2: 4}[raw[pos]]
                pos += 1 + 8 + struct.unpack_from('<I', raw, pos + 1)[0] * index_size
                nodes.append(('shell', name))
            else:
                return None
    except (struct.error, UnicodeDecodeError, KeyError):
        return None
    if pos == len(raw) or (pos + 4 <= len(raw) and struct.unpack_from('<I', raw, pos)[0] in sections):
        return nodes
    return None


def efm_source():
    """Find the EFM source from F117_EFM_ROOT or the local proxy configuration. It is a separate repository."""
    if os.environ.get('F117_EFM_ROOT'):
        path = Path(os.environ['F117_EFM_ROOT']) / 'EFM Source Code/F_117_NightHawk.cpp'
    else:
        ini = ROOT / 'bin/efm.proxy.ini'
        target = re.search(r'target=(.+)', ini.read_text()) if ini.is_file() else None
        if not target:
            return None
        path = Path(target.group(1).strip()).parent.parent / 'F_117_NightHawk.cpp'
    return path if path.is_file() else None


def lua_damage_table():
    text = (ROOT / 'F-117-NightHawk.lua').read_text(encoding='utf-8-sig', errors='replace')
    block = re.search(r'Damage = verbose_to_dmg_properties\((.*?)\n    \),', text, re.S).group(1)
    return LuaRuntime(unpack_returned_tuples=True).execute('return ' + block)


class DamageModelTests(unittest.TestCase):
    def test_every_edm_name_and_lua_record_match(self):
        names = {name for _, name in edm_collision_nodes(EDM)}
        self.assertEqual(names, set(lua_damage_table().keys()))
        self.assertEqual(names, set(STANDARD_CELLS))

    def test_section_nodes_replace_the_broad_cells(self):
        nodes = edm_collision_nodes(EDM)
        self.assertNotIn('MAIN', {name for _, name in nodes})
        for name in STANDARD_CELLS:
            self.assertIn(('shell', name), nodes)

    def test_dependencies_are_declared_and_nothing_detaches(self):
        table = lua_damage_table()
        for name, record in table.items():
            self.assertFalse(record['droppable'], name)
            self.assertGreater(record['critical_damage'], 0, name)
            for dependency in (record['deps_cells'] or {}).values():
                self.assertIn(dependency, table)

    def test_suspension_wheels_use_their_named_cells(self):
        config = (ROOT / 'FM/config.lua').read_text(encoding='utf-8-sig')
        pairs = re.findall(r'damage_element = (\d+),.*?collision_shell_name = "(\w+)"', config, re.S)
        self.assertEqual({name: int(cell) for cell, name in pairs},
                         {name: STANDARD_CELLS[name] for name in ('WHEEL_F', 'WHEEL_L', 'WHEEL_R')})

    def test_compatibility_doc_names_the_installed_model(self):
        doc = (ROOT / 'docs/model-efm-compatibility.md').read_text(encoding='utf-8')
        current = re.search(r'\| Exterior model \|[^|]*\| `([0-9a-f]{64})` \|', doc).group(1)
        self.assertEqual(current, hashlib.sha256(EDM.read_bytes()).hexdigest())

    def test_efm_handles_exactly_the_model_damage_cells(self):
        source = efm_source()
        if source is None:
            self.skipTest('EFM source not found: set F117_EFM_ROOT or bin/efm.proxy.ini')
        cells = re.findall(r'constexpr int kDamageElement\w+ = (\d+);', source.read_text(encoding='utf-8-sig'))
        self.assertEqual({int(cell) for cell in cells}, set(STANDARD_CELLS.values()))

    def test_built_efm_is_not_older_than_its_source(self):
        source = efm_source()
        if source is None:
            self.skipTest('EFM source not found: set F117_EFM_ROOT or bin/efm.proxy.ini')
        dll = source.parent / 'bin/F_117_NightHawk.dll'
        if not dll.is_file():
            self.skipTest('EFM has not been built here')
        self.assertGreaterEqual(dll.stat().st_mtime, source.stat().st_mtime)

    def test_cockpit_livery_textures_exist_in_the_livery(self):
        folder = ROOT / 'Liveries/Cockpit_F-117/Default'
        for texture, stock in re.findall(r'DIFFUSE\s*,\s*"([^"]+)",\s*(true|false)',
                                         (folder / 'description.lua').read_text()):
            self.assertEqual(stock, 'false', texture)
            self.assertTrue((folder / f'{texture}.dds').is_file(), texture)

    def test_cockpit_click_sound_is_bundled(self):
        lights = (ROOT / 'Cockpit/Scripts/Systems/lights_system.lua').read_text(encoding='utf-8-sig')
        proto = re.search(r'click = sound_host:create_sound\("([^"]+)"\)', lights).group(1)
        definition = (ROOT / 'Sounds/sdef' / f'{proto}.sdef').read_text()
        wave_name = re.search(r'wave = "([^"]+)"', definition).group(1)
        with wave.open(str(ROOT / 'Sounds' / f'{wave_name}.wav')) as sound:
            self.assertGreater(sound.getnframes(), 0)
        self.assertTrue(package_release.runtime_file(f'Sounds/sdef/{proto}.sdef'))
        self.assertTrue(package_release.runtime_file(f'Sounds/{wave_name}.wav'))


if __name__ == '__main__':
    unittest.main()
