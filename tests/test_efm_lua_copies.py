"""The EFM repository keeps copies of some cockpit Lua files. They must match this mod's, which DCS loads."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EFM_SCRIPTS = Path(r'C:\Users\Fraser\Git\HMB-DCS-F-117A-EFM\Cockpit\Scripts')


def text(path):
    return path.read_bytes().decode('utf-8-sig').replace('\r\n', '\n')


@unittest.skipUnless(EFM_SCRIPTS.is_dir(), 'EFM repository not checked out here')
class EfmLuaCopiesTests(unittest.TestCase):
    def test_copies_match_the_mod(self):
        copies = sorted(p.relative_to(EFM_SCRIPTS) for p in EFM_SCRIPTS.rglob('*.lua'))
        self.assertTrue(copies)
        for relative in copies:
            with self.subTest(file=relative.as_posix()):
                mod = ROOT / 'Cockpit/Scripts' / relative
                self.assertTrue(mod.is_file(), 'copy of a file the mod no longer has')
                self.assertEqual(text(EFM_SCRIPTS / relative), text(mod),
                                 'out of date: copy the mod file over it')


if __name__ == '__main__':
    unittest.main()
