"""Every store on the pylons must classify to a release profile the EFM, VSD and MFD all know."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_display_calibration import runtime  # noqa: E402

SCRIPTS = ROOT / 'Cockpit/Scripts'
EFM = Path(r'C:\Users\Fraser\Git\HMB-DCS-F-117A-EFM\EFM Source Code\F_117_NightHawk.cpp')
EXPECTED = {
    '{GBU-31}': 0, '{GBU-31V3B}': 1, '{GBU_32_V_2B}': 2,
    '{DB769D48-67D7-42ED-A2BE-108D566C8B1E}': 3,  # GBU-12
    '{EF0A9419-01D6-473B-99A3-BEBDB923B14D}': 4,  # GBU-27
    '{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}': 5,  # GBU-10
    '{BCE4E030-38E9-423E-98ED-24BE3DA87C32}': 6,  # Mk-82
    '{AB8B8299-F1CC-4359-89B5-2172E0CF4A5A}': 7,  # Mk-84
    '{CBU_105}': 8,
    '{AGM-154A}': 9, '{AGM-154B}': 10,
    '{9BCC2A2B-5708-4860-B1F1-053A18442067}': 11,  # AGM-154C
    '{444BA8AE-82A7-4345-842E-76154EFCCA47}': 12,  # AGM-65D
    '{F16A4DE0-116C-4A71-97F0-2CF85B0313EF}': 13,  # AGM-65E
}
EFM_NAMES = ['GBU-31(V)1/B', 'GBU-31(V)3/B', 'GBU-32(V)2/B', 'GBU-12', 'GBU-27', 'GBU-10', 'MK-82', 'MK-84',
             'CBU-105', 'AGM-154A', 'AGM-154B', 'AGM-154C', 'AGM-65D', 'AGM-65E']


def pylon_clsids():
    text = (ROOT / 'F-117-NightHawk.lua').read_text(encoding='utf-8')
    return [c for c in re.findall(r'\{CLSID\s*=\s*"([^"]+)"\s*\}', text) if c != '<CLEAN>']


class StoreProfileTests(unittest.TestCase):
    def classify(self, station_info):
        lua, load = runtime()
        lua.execute('''
            function GetSelf() return {listen_command=function()end,
                get_station_info=function(_,i) if i==0 then return STATION end end,
                get_weapon_count=function(_,i) return i==0 and 1 or 0 end} end
            function make_default_activity()end
            log={write=function()end,INFO=0}
        ''')
        lua.globals().STATION = lua.table_from(station_info)
        load(SCRIPTS / 'Systems/Weapons.lua')
        lua.globals().post_initialize()
        params = lua.globals()._parameters
        return params.F117_CCRP_PROFILE if params.F117_STORE_VALID == 1 else None

    def test_both_pylons_carry_every_store(self):
        clsids = pylon_clsids()
        self.assertEqual(sorted(set(clsids)), sorted(EXPECTED))
        for clsid in EXPECTED:
            self.assertEqual(clsids.count(clsid), 2, clsid)

    def test_every_pylon_store_classifies_to_its_profile(self):
        for clsid in sorted(set(pylon_clsids())):
            self.assertEqual(self.classify({'count': 1, 'CLSID': clsid}), EXPECTED[clsid], clsid)

    def test_weapon_names_classify_like_clsids(self):
        # A station can report the weapon's name rather than the loadout ID.
        names = {'GBU_10': 5, 'Mk_82': 6, 'Mk_84': 7, 'CBU_105': 8, 'AGM_154A': 9, 'AGM_154B': 10,
                 'AGM_154': 9, 'AGM_65D': 12, 'AGM_65E': 13, 'AGM_65L': 13, 'GBU_27': 4, 'GBU_31_V_3B': 1}
        for name, profile in names.items():
            self.assertEqual(self.classify({'count': 1, 'name': name}), profile, name)

    def test_unknown_store_is_not_released(self):
        self.assertIsNone(self.classify({'count': 1, 'CLSID': '{FUEL_TANK}'}))

    def test_vsd_and_mfd_label_every_profile(self):
        for page in ('MFD/Indicator/Left/Left_vsd_page.lua', 'MFD/Indicator/MFD_indication_page.lua'):
            text = (SCRIPTS / page).read_text(encoding='utf-8')
            labels = {int(i) for i in re.findall(r'\[(\d+)\]="(?:GBU|MK|CBU|AGM)', text)}
            self.assertEqual(labels, set(range(len(EFM_NAMES))), page)

    @unittest.skipUnless(EFM.exists(), 'EFM source not checked out')
    def test_efm_store_table_matches_profile_order(self):
        text = EFM.read_text(encoding='utf-8-sig')
        table = text[text.index('kCcrpStoreModels[] ='):text.index('kCcrpStoreCount')]
        self.assertEqual(re.findall(r'\{\s*"([^"]+)"', table), EFM_NAMES)


if __name__ == '__main__':
    unittest.main()
