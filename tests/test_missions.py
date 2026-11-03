"""Bundled missions: each loads, flies the F-117 with stores that release, and is listed in the menus."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from missions.miz import Miz  # noqa: E402
from test_store_profiles import EXPECTED  # noqa: E402

MISSIONS = ROOT / 'Missions'
LEFTOVERS = ('SU25T', 'Su-25T', 'Shkval', 'Kh-25', 'Vikhr')


def bundled():
    return sorted(MISSIONS.rglob('*.miz'))


def listed(index):
    return re.findall(r"file\s*=\s*'([^']+)'", index.read_text(encoding='utf-8'))


class MissionTests(unittest.TestCase):
    def test_missions_exist(self):
        self.assertTrue(list((MISSIONS / 'Training').glob('*.miz')))
        self.assertTrue(list((MISSIONS / 'QuickStart').glob('*.miz')))

    def test_every_f117_carries_releasable_stores_on_two_stations(self):
        for path in bundled():
            miz = Miz.load(path)
            players = list(miz.player_units())
            self.assertEqual(len(players), 1, path.name)
            for _, _, _, _, group in miz.groups():
                for unit in group['units'].values():
                    if unit['type'] != 'F-117-NightHawk':
                        continue
                    pylons = unit['payload']['pylons'] or {}
                    self.assertLessEqual(set(pylons.keys()), {1, 2}, path.name)
                    for station in pylons.values():
                        self.assertIn(station['CLSID'], EXPECTED, path.name)
            self.assertEqual(players[0][1]['type'], 'F-117-NightHawk', path.name)

    def test_missions_require_the_module_and_name_their_map(self):
        for path in bundled():
            miz = Miz.load(path)
            self.assertEqual(dict(miz.mission['requiredModules'] or {}).get('F-117-NightHawk'), 'F-117-NightHawk',
                             path.name)
            self.assertEqual(miz.files['theatre'].decode().strip(), miz.mission['theatre'], path.name)

    def test_no_material_left_from_other_aircraft(self):
        for path in bundled():
            miz = Miz.load(path)
            names = ' '.join(miz.files)
            text = names + ' '.join(str(v) for v in miz.dictionary.values())
            for word in LEFTOVERS:
                self.assertNotIn(word, text, path.name)

    def test_menus_list_exactly_the_bundled_missions(self):
        for folder, index in (('QuickStart', 'quickstart.lua'), ('Training', 'lessons.lua')):
            files = sorted(p.name for p in (MISSIONS / folder).glob('*.miz'))
            self.assertEqual(sorted(listed(MISSIONS / folder / index)), files, folder)

    def test_training_lessons_prompt_the_pilot(self):
        for path in (MISSIONS / 'Training').glob('*.miz'):
            miz = Miz.load(path)
            scripts = [str(v) for v in miz.dictionary.values() if 'Lesson prompts' in str(v)]
            self.assertEqual(len(scripts), 1, path.name)
            self.assertIn('lesson_complete', scripts[0], path.name)


if __name__ == '__main__':
    unittest.main()
