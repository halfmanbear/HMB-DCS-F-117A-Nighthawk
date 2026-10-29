"""Build a runtime-only ZIP from committed mod files and a separately built EFM."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import tarfile
import tempfile
import zipfile


EFM_REPOSITORY = "halfmanbear/HMB-DCS-F-117A-EFM"
MOD_FOLDER = "F-117-NightHawk"
DLL_NAME = "F_117_NightHawk.dll"
RUNTIME_DIRS = {
    "Cockpit", "Effects", "FM", "ImagesGui", "Input", "l10n", "Liveries",
    "Missions", "Options", "Shapes", "Sounds", "Textures", "Theme",
    "UnitPayloads", "Weapons",
}
ROOT_FILES = {"comm.lua", "credits.txt", "entry.lua", "F-117-NightHawk.lua", "IRADS.lua", "Views.lua"}
RUNTIME_EXTENSIONS = {".lua", ".dds", ".png", ".tga", ".edm", ".lods", ".owv", ".ogg", ".wav", ".miz", ".dlg", ".mo", ".ttf", ".otf"}
VERSION = re.compile(r'(?m)^(\s*version\s*=\s*)([\"\x27])([0-9]+\.[0-9]+\.[0-9]+)\2(\s*,?\s*)$')
PRIVATE_PATH = re.compile(r"(?i)(?:[a-z]:[\\/](?:Users|Saved Games)[\\/]|/home/(?!runner/)[^/\s]+/)")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode("utf-8").strip()


def metadata(root, channel, tag=""):
    if channel not in {"dev", "main"}:
        raise ValueError("Only dev and main can be packaged")
    commit = git(root, "rev-parse", "HEAD")
    entry = git(root, "show", "HEAD:entry.lua")
    matches = list(VERSION.finditer(entry))
    if len(matches) != 1:
        raise ValueError("entry.lua must contain exactly one numeric version = 'major.minor.patch'")
    base = matches[0].group(3)
    if tag and (channel != "main" or tag != f"v{base}"):
        raise ValueError(f"Stable release tag must match entry.lua: v{base}")
    version = f"{base}-dev-{commit[:7]}" if channel == "dev" else base
    return {"base_version": base, "version": version, "channel": channel,
            "mod_commit": commit, "archive_name": f"F-117-Nighthawk-{version}.zip"}


def runtime_file(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        return False
    if name in ROOT_FILES:
        return True
    if len(path.parts) < 2 or path.parts[0] not in RUNTIME_DIRS:
        return False
    if any(part.lower() in {"old_test_files", "tests", "backup", "backups", "__pycache__"}
           or part.startswith((".", "_")) for part in path.parts[:-1]):
        return False
    if path.name.lower().startswith(("old-", "old_", "bak_", "bak-", "dev_", "damage_working_", "v1-")):
        return False
    return path.suffix.lower() in RUNTIME_EXTENSIONS


def check_private_paths(data, label):
    # Inspect both ordinary strings and Windows wide strings without printing paths.
    strings = (data.decode("latin-1"), data.decode("utf-16-le", errors="ignore"),
               data[1:].decode("utf-16-le", errors="ignore"))
    if any(PRIVATE_PATH.search(value) for value in strings):
        raise ValueError(f"Personal absolute path detected in {label}; packaging stopped")


def validate_dll(data):
    if len(data) < 64 or data[:2] != b"MZ":
        raise ValueError("EFM input is not a Windows DLL")
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    if offset + 24 > len(data) or data[offset:offset + 4] != b"PE\0\0":
        raise ValueError("Invalid EFM PE header")
    machine = struct.unpack_from("<H", data, offset + 4)[0]
    characteristics = struct.unpack_from("<H", data, offset + 22)[0]
    if machine != 0x8664 or not characteristics & 0x2000:
        raise ValueError("EFM must be an x64 DLL")
    if b"ed_fm_simulate" not in data:
        raise ValueError("DLL is missing the EFM simulation entry point")
    if b"efm.proxy.ini" in data.lower() or "efm.proxy.ini".encode("utf-16-le") in data.lower():
        raise ValueError("Refusing to package a development proxy DLL")
    check_private_paths(data, DLL_NAME)


def package(root, dll, efm_root, channel, output, tag=""):
    info = metadata(root, channel, tag)
    # Check the actual EFM checkout, not a caller-supplied provenance string.
    if git(efm_root, "branch", "--show-current") != channel:
        raise ValueError("EFM checkout branch must match the mod channel")
    efm_commit = git(efm_root, "rev-parse", "HEAD")
    data = dll.read_bytes()
    validate_dll(data)
    info.update({"efm_repository": EFM_REPOSITORY, "efm_branch": channel,
                 "efm_commit": efm_commit, "dll_sha256": hashlib.sha256(data).hexdigest()})
    output.mkdir(parents=True, exist_ok=True)
    destination = output / info["archive_name"]
    if destination.exists():
        raise ValueError("Output ZIP already exists; use a fresh output directory")
    with tempfile.TemporaryDirectory(prefix="f117-package-") as scratch:
        scratch = Path(scratch)
        source = scratch / "source.tar"
        subprocess.run(["git", "-C", str(root), "archive", "--format=tar",
                        f"--output={source}", info["mod_commit"]], check=True)
        archive = scratch / info["archive_name"]
        included = set()
        with tarfile.open(source) as tree, zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as release:
            for member in tree:
                if not member.isfile() or not runtime_file(member.name):
                    continue
                included.add(member.name)
                target = f"{MOD_FOLDER}/{member.name}"
                with tree.extractfile(member) as stream:
                    if PurePosixPath(member.name).suffix.lower() in {".lua", ".dlg", ".lods", ".txt"}:
                        content = stream.read()
                        check_private_paths(content, member.name)
                        if member.name == "entry.lua":
                            content = VERSION.sub(lambda m: f'{m[1]}{m[2]}{info["version"]}{m[2]}{m[4]}', content.decode("utf-8")).encode("utf-8")
                        release.writestr(target, content)
                    else:
                        with release.open(target, "w", force_zip64=True) as sink:
                            shutil.copyfileobj(stream, sink)
            required = ROOT_FILES | {"Shapes/f-117-nighthawk.edm", "Shapes/f-117-nighthawk.lods",
                                     "Cockpit/Shape/Cockpit_F-117.edm", "Cockpit/Scripts/device_init.lua"}
            missing = required - included
            if missing:
                raise ValueError(f"Required runtime files are not committed: {', '.join(sorted(missing))}")
            # These are loaded by the current cockpit; catch accidentally uncommitted modules.
            displays = git(root, "show", f'{info["mod_commit"]}:Cockpit/Scripts/Systems/Displays.lua')
            for module in ("IRADS_Terrain.lua", "IRADS_Diagnostics.lua"):
                if module in displays and f"Cockpit/Scripts/Systems/{module}" not in included:
                    raise ValueError(f"Displays.lua requires uncommitted module: {module}")
            release.writestr(f"{MOD_FOLDER}/bin/{DLL_NAME}", data)
            release.writestr(f"{MOD_FOLDER}/build-manifest.json", json.dumps(info, indent=2) + "\n")
            release.writestr(f"{MOD_FOLDER}/README.txt", (
                f'F-117A Nighthawk {info["version"]} ({channel})\n\n'
                f'Extract {MOD_FOLDER} into Saved Games/DCS/Mods/aircraft/.\n'
                'See credits.txt for contributor credits.\n'
                'Mod fork: https://github.com/WatchBambi/DCS-F-117\n'
                'EFM fork: https://github.com/WatchBambi/DCS-F-117-EFM\n'
                f'EFM development: https://github.com/{EFM_REPOSITORY}\n'
                'Build provenance is recorded in build-manifest.json.\n'))
        shutil.copyfile(archive, destination)
    with destination.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("metadata", "package"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--channel", required=True, choices=("dev", "main"))
    parser.add_argument("--tag", default="")
    parser.add_argument("--dll", type=Path)
    parser.add_argument("--efm-root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    if args.command == "metadata":
        info = metadata(args.root, args.channel, args.tag)
        print(json.dumps(info, indent=2))
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
                for key, value in info.items():
                    stream.write(f"{key}={value}\n")
    else:
        if not args.dll or not args.efm_root:
            parser.error("package requires --dll and --efm-root")
        print(package(args.root, args.dll, args.efm_root, args.channel, args.output, args.tag))


if __name__ == "__main__":
    main()
