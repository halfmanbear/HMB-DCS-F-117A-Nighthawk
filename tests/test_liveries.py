"""Exterior liveries must name every model material whose texture they supply."""
import sys
import unittest
from pathlib import Path

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/models'))
import sync_livery_materials as sync  # noqa: E402


class LiveryTests(unittest.TestCase):
    def test_liveries_cover_every_textured_material(self):
        self.assertEqual(sync.sync(check=True), [],
                         'run python tools/models/sync_livery_materials.py')

    def test_model_still_has_suffixed_skin_materials(self):
        materials = sync.edm_materials()
        self.assertEqual(materials['Aircraft_01.006'].lower(), 'aircraft 01_basecolor')
        self.assertGreater(len(materials), 150)

    def test_descriptions_load_and_reference_existing_files(self):
        for desc in sorted(sync.LIVERIES.glob('*/description.lua')):
            lua = LuaRuntime()
            lua.execute('DIFFUSE=0 NORMAL_MAP=1 SPECULAR=2')
            lua.execute(desc.read_text(encoding='utf-8'))
            livery = lua.globals().livery
            files = {f.stem.lower() for f in desc.parent.glob('*.dds')}
            self.assertGreater(len(livery), 40, desc.parent.name)
            for row in livery.values():
                self.assertIn(row[3].lower(), files, f'{desc.parent.name}: {row[1]}')


if __name__ == '__main__':
    unittest.main()
