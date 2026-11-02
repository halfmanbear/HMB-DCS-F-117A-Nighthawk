"""The aircraft carries the stock DCS JDAMs, so the mod must not refer to its old copies."""
import re
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOCK = Path(r'E:\Eagle Dynamics\DCS World\CoreMods\aircraft\AircraftWeaponPack\JDAM.lua')
STOCK_IDS = ('{GBU-31}', '{GBU-31V3B}', '{GBU_32_V_2B}')
OLD_IDS = ('GBU31_JDAM', 'GBU31_V3B_JDAM', 'GBU32_JDAM')


class StockJdamTests(unittest.TestCase):
    def test_both_pylons_offer_each_stock_jdam(self):
        text = (ROOT / 'F-117-NightHawk.lua').read_text(encoding='utf-8')
        for clsid in STOCK_IDS:
            self.assertEqual(text.count(f'{{CLSID = "{clsid}"}}'), 2, clsid)

    def test_old_ids_and_definitions_are_gone(self):
        for name in ('F-117-NightHawk.lua', 'UnitPayloads/F-117-NightHawk.lua', 'entry.lua'):
            text = (ROOT / name).read_text(encoding='utf-8')
            for clsid in OLD_IDS:
                self.assertNotIn(clsid, text, name)
        for name in ('gbu-31.lua', 'gbu-31v3b.lua', 'gbu-32.lua'):
            self.assertFalse((ROOT / 'Weapons' / name).exists(), name)

    def test_bundled_missions_use_no_old_ids(self):
        missions = list((ROOT / 'Missions').rglob('*.miz'))
        self.assertTrue(missions)
        for path in missions:
            with zipfile.ZipFile(path) as archive:
                mission = archive.read('mission').decode('utf-8', errors='replace')
            for clsid in OLD_IDS:
                self.assertNotIn(clsid, mission, path.name)

    @unittest.skipUnless(STOCK.exists(), 'DCS is not installed')
    def test_stock_ids_are_declared_by_dcs(self):
        declared = re.findall(r'CLSID\s*=\s*"([^"]+)"', STOCK.read_text(encoding='latin-1'))
        for clsid in STOCK_IDS:
            self.assertIn(clsid, declared)


if __name__ == '__main__':
    unittest.main()
