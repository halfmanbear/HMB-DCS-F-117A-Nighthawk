import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zipfile


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "package_release.py"
spec = importlib.util.spec_from_file_location("package_release", MODULE_PATH)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


def command(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT).decode().strip()


def make_repo(root, branch="dev"):
    root.mkdir()
    command(root, "init", "-b", branch)
    command(root, "config", "user.name", "Packaging test")
    command(root, "config", "user.email", "packaging@example.invalid")


def write(root, name, data):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        target.write_text(data, encoding="utf-8")
    else:
        target.write_bytes(data)


def commit(root):
    command(root, "add", ".")
    command(root, "commit", "-m", "Fixture")


def example_dll():
    # Minimal header for the packager's x64/EFM sanity checks; never executable.
    data = bytearray(160)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 64)
    data[64:68] = b"PE\0\0"
    struct.pack_into("<H", data, 68, 0x8664)
    struct.pack_into("<H", data, 86, 0x2000)
    data.extend(b"ed_fm_simulate\0")
    return bytes(data)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="f117-packaging-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.mod = self.root / "mod"
        self.efm = self.root / "efm"
        make_repo(self.mod)
        make_repo(self.efm)
        for name in packager.ROOT_FILES:
            write(self.mod, name, "-- runtime\n")
        write(self.mod, "entry.lua", 'declare_plugin("F-117", {\n    version = "2.1.0",\n})\n')
        for name in ("Shapes/f-117-nighthawk.edm", "Shapes/f-117-nighthawk.lods",
                     "Cockpit/Shape/Cockpit_F-117.edm", "Cockpit/Scripts/device_init.lua",
                     "Cockpit/Scripts/Systems/Displays.lua"):
            write(self.mod, name, "-- runtime\n")
        for name in ("bin/F_117_NightHawk.dll", "bin/DEV_F_117_NightHawk.dll",
                     "bin/efm.proxy.ini", "blender_files/model.blend", "F117-mod-status.html",
                     "Shapes/old-model.edm", "Shapes/bak_model.owv", "Shapes/model.edm.json",
                     "Cockpit/Scripts/MFD/Indicator/old_test_files/test.lua", "tools/private.py"):
            write(self.mod, name, "development-only\n")
        commit(self.mod)
        write(self.efm, "source.cpp", "// source\n")
        commit(self.efm)
        self.dll = self.root / packager.DLL_NAME
        self.dll.write_bytes(example_dll())

    def package(self, channel="dev", tag=""):
        return packager.package(self.mod, self.dll, self.efm, channel, self.root / "dist", tag)

    def test_dev_archive_is_clean_and_uses_committed_files_and_real_dll(self):
        original_proxy = (self.mod / "bin" / packager.DLL_NAME).read_bytes()
        original_entry = (self.mod / "entry.lua").read_text()
        # Working-tree changes are intentionally excluded from a release snapshot.
        write(self.mod, "comm.lua", "uncommitted\n")
        write(self.mod, "Cockpit/Scripts/untracked.lua", "untracked\n")
        archive = self.package()
        prefix = packager.MOD_FOLDER + "/"
        with zipfile.ZipFile(archive) as bundle:
            names = set(bundle.namelist())
            self.assertEqual([n for n in names if n.endswith(".dll")], [prefix + "bin/" + packager.DLL_NAME])
            self.assertEqual(bundle.read(prefix + "bin/" + packager.DLL_NAME), example_dll())
            self.assertEqual(bundle.read(prefix + "comm.lua").decode().splitlines(), ["-- runtime"])
            self.assertFalse(any("old_test_files" in n or "blender_files" in n or "proxy.ini" in n or "bak_" in n for n in names))
            self.assertNotIn(prefix + "Cockpit/Scripts/untracked.lua", names)
            manifest = json.loads(bundle.read(prefix + "build-manifest.json"))
            self.assertEqual(manifest["efm_branch"], "dev")
            self.assertEqual(manifest["efm_commit"], command(self.efm, "rev-parse", "HEAD"))
            self.assertIn(manifest["version"].encode(), bundle.read(prefix + "entry.lua"))
        self.assertTrue(archive.with_suffix(".zip.sha256").is_file())
        self.assertEqual((self.mod / "bin" / packager.DLL_NAME).read_bytes(), original_proxy)
        self.assertEqual((self.mod / "entry.lua").read_text(), original_entry)

    def test_stable_version_and_tag(self):
        command(self.efm, "branch", "-m", "main")
        archive = self.package("main", "v2.1.0")
        self.assertEqual(archive.name, "F-117-Nighthawk-2.1.0.zip")
        with zipfile.ZipFile(archive) as bundle:
            self.assertIn(b'version = "2.1.0"', bundle.read(packager.MOD_FOLDER + "/entry.lua"))

    def test_tag_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "must match"):
            packager.metadata(self.mod, "main", "v9.0.0")

    def test_branch_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "branch must match"):
            self.package("main")

    def test_proxy_and_wrong_architecture_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "proxy"):
            packager.validate_dll(example_dll() + b"efm.proxy.ini")
        data = bytearray(example_dll())
        struct.pack_into("<H", data, 68, 0x14C)
        with self.assertRaisesRegex(ValueError, "x64"):
            packager.validate_dll(data)

    def test_personal_paths_are_rejected_in_dll_and_lua(self):
        for encoding in ("utf-8", "utf-16-le"):
            with self.assertRaisesRegex(ValueError, "Personal absolute path"):
                packager.validate_dll(example_dll() + "C:\\Users\\Example\\private.pdb".encode(encoding))
        write(self.mod, "comm.lua", '-- C:\\Users\\Example\\private\n')
        commit(self.mod)
        with self.assertRaisesRegex(ValueError, "Personal absolute path"):
            self.package()
        self.assertFalse(list((self.root / "dist").glob("*.zip")))

    def test_missing_irads_module_fails(self):
        write(self.mod, "Cockpit/Scripts/Systems/Displays.lua", 'dofile("Systems/IRADS_Terrain.lua")\n')
        commit(self.mod)
        with self.assertRaisesRegex(ValueError, "uncommitted module"):
            self.package()


if __name__ == "__main__":
    unittest.main()
