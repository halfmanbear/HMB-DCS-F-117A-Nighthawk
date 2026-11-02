"""Loads the built EFM DLL outside DCS and exposes the ed_fm_* calls the bench needs."""
import configparser
import ctypes as C
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD_ROOT = HERE.parents[1]
CACHE = HERE / '.cache'
STUB = CACHE / 'CockpitBase.dll'

D = C.c_double

# Command numbers from the EFM's Inputs.h.
CMD_PITCH_AXIS = 2001
CMD_ROLL_AXIS = 2002
CMD_YAW_AXIS = 2003
CMD_THROTTLE_AXIS = 2004
CMD_GEAR_DOWN = 431

# ed_fm_param_enum value of ED_FM_ENGINE_1_THRUST: newtons from one engine.
PARAM_ENGINE_1_THRUST = 104


def default_dll():
    """The EFM build named by F117_EFM_ROOT or the mod's local proxy configuration."""
    if os.environ.get('F117_EFM_ROOT'):
        return Path(os.environ['F117_EFM_ROOT']) / 'EFM Source Code/bin/F_117_NightHawk.dll'
    config = configparser.ConfigParser()
    config.read(MOD_ROOT / 'bin/efm.proxy.ini')
    if config.has_option('General', 'target'):
        return Path(config.get('General', 'target'))
    raise SystemExit('EFM DLL not found: pass --dll, set F117_EFM_ROOT or create bin/efm.proxy.ini')


def build_stub():
    """Compile the cockpit parameter stand-in once. It needs the Visual Studio C++ tools, as the EFM does."""
    source = HERE / 'cockpit_stub.cpp'
    if STUB.exists() and STUB.stat().st_mtime >= source.stat().st_mtime:
        return STUB
    vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    install = subprocess.run([str(vswhere), '-latest', '-property', 'installationPath'],
                             capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(install) / 'VC/Auxiliary/Build/vcvars64.bat'
    CACHE.mkdir(exist_ok=True)
    script = CACHE / 'build_stub.bat'
    script.write_text(f'@call "{vcvars}" >nul\r\n@cl /nologo /LD /O2 /EHsc /MT "{source}" /Fe:CockpitBase.dll >nul\r\n')
    result = subprocess.run(['cmd', '/c', str(script)], cwd=CACHE, capture_output=True, text=True)
    if result.returncode or not STUB.exists():
        raise SystemExit(f'Could not build {STUB.name}:\n{result.stdout}\n{result.stderr}')
    return STUB


class SuspensionInfo(C.Structure):
    _fields_ = [('acting_force', D * 3), ('acting_force_point', D * 3), ('integrity_factor', D),
                ('struct_compression', D), ('wheel_speed_x', D)]


class Efm:
    """One loaded copy of the EFM. It has global state, so each worker process gets its own copy."""

    def __init__(self, dll_path, work_dir):
        # The DLL writes logs beside itself and to the current folder, so run a private copy in a scratch folder.
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(work_dir)
        os.environ['F117_LOG_ROOT'] = str(work_dir)
        os.environ['USERPROFILE'] = str(work_dir)
        copy = work_dir / 'F_117_NightHawk.dll'
        shutil.copyfile(dll_path, copy)
        self._stub = C.CDLL(str(STUB))  # Must load first: the EFM finds it by module name.
        d = self.dll = C.CDLL(str(copy))
        for name, args, res in (
            ('ed_fm_set_atmosphere', [D] * 8, None),
            ('ed_fm_set_current_mass_state', [D] * 7, None),
            ('ed_fm_set_current_state', [D] * 19, None),
            ('ed_fm_set_current_state_body_axis', [D] * 20, None),
            ('ed_fm_simulate', [D], None),
            ('ed_fm_set_internal_fuel', [D], None),
            ('ed_fm_unlimited_fuel', [C.c_bool], None),
            ('ed_fm_set_command', [C.c_int, C.c_float], None),
            ('ed_fm_get_param', [C.c_uint], D),
            ('ed_fm_change_mass', [C.POINTER(D)] * 7, C.c_bool),
            ('ed_fm_hot_start_in_air', [], None),
            ('ed_fm_release', [], None),
            ('ed_fm_suspension_feedback', [C.c_int, C.POINTER(SuspensionInfo)], None),
        ):
            function = getattr(d, name)
            function.argtypes = args
            function.restype = res
        self.set_atmosphere = d.ed_fm_set_atmosphere
        self.set_mass_state = d.ed_fm_set_current_mass_state
        self.set_state = d.ed_fm_set_current_state
        self.set_state_body = d.ed_fm_set_current_state_body_axis
        self.simulate = d.ed_fm_simulate
        self.command = d.ed_fm_set_command
        self.get_param = d.ed_fm_get_param
        self.set_fuel = d.ed_fm_set_internal_fuel
        self.unlimited_fuel = d.ed_fm_unlimited_fuel
        self._fx, self._fy, self._fz, self._px, self._py, self._pz = (D() for _ in range(6))
        self._mx, self._my, self._mz = (D() for _ in range(3))
        self._refs = tuple(C.byref(v) for v in (self._fx, self._fy, self._fz, self._px, self._py, self._pz))
        self._mrefs = tuple(C.byref(v) for v in (self._mx, self._my, self._mz))
        self._add_force = d.ed_fm_add_local_force
        self._add_moment = d.ed_fm_add_local_moment
        self._mass_refs = tuple(D() for _ in range(7))
        self._mass_ptrs = tuple(C.pointer(v) for v in self._mass_refs)

    def restart(self):
        """Clear all flight state and start again in the air, as DCS does for an air start."""
        self.dll.ed_fm_release()
        self.dll.ed_fm_hot_start_in_air()

    def forces(self):
        self._add_force(*self._refs)
        return self._fx.value, self._fy.value, self._fz.value

    def moments(self):
        self._add_moment(*self._mrefs)
        return self._mx.value, self._my.value, self._mz.value

    def mass_change(self):
        """Mass to add to the aircraft since the last call (kg), collected as DCS collects it."""
        change = 0.0
        while self.dll.ed_fm_change_mass(*self._mass_ptrs):
            change += self._mass_refs[0].value
        return change

    def wheel_contact(self, on_ground):
        """Report all three wheels on the ground or clear of it, as DCS does each frame. There's no gear model here."""
        info = SuspensionInfo(struct_compression=0.05 if on_ground else 0.0)
        for wheel in range(3):
            self.dll.ed_fm_suspension_feedback(wheel, C.byref(info))

    def thrust(self):
        return 2.0 * self.get_param(PARAM_ENGINE_1_THRUST)
