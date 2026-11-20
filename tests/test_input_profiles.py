"""Load complete input profiles, including translated inherited commands."""
import re
from pathlib import Path
import pytest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize("kind", ["keyboard", "joystick"])
def test_input_profile_loads_with_inherited_landing_binding(kind):
    path = ROOT / "Input/F-117-NightHawk" / kind / "default.lua"
    source = path.read_text(encoding="utf-8-sig")
    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    g.folder = path.parent.as_posix() + "/"
    g.dofile = lambda name: lua.execute(Path(name).read_text(encoding="utf-8-sig"))
    for index, name in enumerate(sorted(set(re.findall(r"\biCommand\w+", source))), 20000):
        g[name] = index
    lua.execute("""
        function _(text) return text end
        function defaultDeviceAssignmentFor(name) return {} end
        function external_profile(path)
            return {keyCommands={{down=iCommandPlaneHeadLightOnOff,
                name='Gear Light Near/Far/Off', combos={{key='L'}}}}, axisCommands={}}
        end
        function join(destination, additions)
            for i, entry in ipairs(additions) do table.insert(destination, entry) end
        end
    """)
    profile = lua.execute(source)
    assert len(profile.keyCommands) > 100
    landing = profile.keyCommands[1]
    assert landing.name == "Landing Light ON/OFF"
    assert landing.down == g.iCommandPlaneHeadLightOnOff
    assert landing.combos[1].key == "L"
    assert callable(g['_'])
    assert any(entry.name == "Taxi Light ON/OFF" for entry in profile.keyCommands.values())
    if kind == "joystick":
        assert len(profile.axisCommands) >= 5

@pytest.mark.parametrize("mission_frequency,mission_modulation,expected_frequency,expected_modulation", [
    (None, None, 251e6, 0), (127.5, 0, 127.5e6, 0), (40, 1, 40e6, 1),
    (999, 7, 251e6, 0),
])
def test_native_radio_initializes_once_and_preserves_tuning(mission_frequency, mission_modulation,
                                                          expected_frequency, expected_modulation):
    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    lua.execute("""
        calls=0
        radio={
            push_frequency_range=function(self, low, high, step)
                assert(low==30e6 and high==399.975e6 and step==25e3)
            end,
            set_frequency=function(self, f) frequency=f; calls=calls+1 end,
            set_modulation=function(self, m) modulation=m end,
            set_on_off=function(self, on) powered=on end,
        }
        function GetSelf() return radio end
        LockOn_Options={common_script_path='common/'}
        function dofile(path)
            assert(path=='common/Radio.lua')
            function getInnerNoise(u, sn) return u/(10^(sn/20)-1) end
            function rangeUtoDb(a,b) return 20*math.log10(b/a) end
        end
    """)
    mission = {"frequency": mission_frequency, "modulation": mission_modulation}
    g.get_aircraft_mission_data = lambda name: mission.get(name)
    lua.execute((ROOT / 'Cockpit/Scripts/Systems/Radio.lua').read_text())
    g.update()
    assert g.frequency == expected_frequency
    assert g.modulation == expected_modulation
    assert g.powered is True
    g.radio.set_frequency(g.radio, 264e6)
    g.update()
    assert g.frequency == 264e6
    assert g.calls == 2


def test_native_intercom_link_is_declared():
    lua = LuaRuntime()
    lua.execute((ROOT/'Cockpit/Scripts/devices.lua').read_text())
    devices = lua.globals().devices
    assert devices.RADIO == 14 and devices.INTERCOM == 15
    source = (ROOT/'Cockpit/Scripts/device_init.lua').read_text()
    assert '[devices.RADIO]         = {"avDefaultLuaRadio"' in source
    assert '[devices.INTERCOM]      = {"avIntercomWWII"' in source
    assert '{{"VHF_Radio", devices.RADIO}}' in source
