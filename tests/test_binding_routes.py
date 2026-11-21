"""Fast offline binding audit: real stock IDs, profile parity and device subscriptions.

Run: python -m pytest -q tests/test_binding_routes.py
Does not emulate DCS-owned commands or prove their in-game effects.
"""
import re
from pathlib import Path

import pytest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'Cockpit/Scripts'
EFM = Path(r'C:\Users\Fraser\Git\HMB-DCS-F-117A-EFM\EFM Source Code')


def cockpit():
    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    lua.execute((ROOT / 'tools/cockpit/layout_runtime.lua').read_text())
    g.LockOn_Options.script_path = SCRIPTS.as_posix() + '/'
    lua.execute('''
        listened={};calls={}
        function GetSelf() return {listen_command=function(_,id)listened[id]=true end,
            performClickableAction=function()end} end
        function make_default_activity()end
        function dispatch_action(_,id,value)calls[#calls+1]={id,value}end
        function get_absolute_model_time()return 43200 end
        function get_base_data()return {} end
        LockOn_Options.init_conditions={birth_place='GROUND_COLD'}
    ''')
    def load(path):
        path = Path(path)
        if path.parent == SCRIPTS / 'Systems' and path.name not in {
            'Displays.lua', 'AlignedSensor.lua', 'DesignateSelect.lua', 'HudCursor.lua',
            'INS.lua', 'NavUpdate.lua', 'IRADS_ImageControls.lua',
        }:
            if path.name == 'IRADS_Diagnostics.lua':
                return lua.eval('function()end')
            return lua.eval('''{new=function()return {
                initialize=function()end,update=function()end,
                set_command=function()return false end}end,
                initialize=function()end,update=function()end,
                set_command=function()return false end,
                default_side_brightness=function()return 1 end,
                default_dep_brightness=function()return 1 end}''')
        return lua.execute(path.read_text(encoding='utf-8-sig'))
    g.dofile = load
    load(SCRIPTS / 'Systems/Displays.lua')
    g.post_initialize()
    # Use actual persisted DCS IDs rather than invented enumeration values.
    lua.execute((ROOT / 'docs/reference/iCommands.lua').read_text(encoding='utf-8-sig'))
    lua.execute('''
        function _(s)return s end
        function defaultDeviceAssignmentFor()return {} end
        function external_profile()return {keyCommands={},axisCommands={}} end
        function join(dst,src)for _,v in ipairs(src)do table.insert(dst,v)end end
    ''')
    return lua, load


def profile(lua, load, kind):
    path = ROOT / 'Input/F-117-NightHawk' / kind / 'default.lua'
    lua.globals().folder = path.parent.as_posix() + '/'
    # A nil action silently disappears from a Lua table; reject misspelled symbols first.
    source = path.read_text(encoding='utf-8-sig')
    for symbol in re.findall(r'\b(?:down|up|pressed|action)\s*=\s*([\w.]+)', source):
        assert isinstance(lua.eval(symbol), (int, float)), f'{kind}: undefined {symbol}'
    return load(path)


@pytest.mark.parametrize('kind', ['keyboard', 'joystick'])
def test_every_device_binding_has_a_subscription(kind):
    lua, load = cockpit()
    p = profile(lua, load, kind)
    g = lua.globals()
    for group in (p.keyCommands, p.axisCommands):
        for entry in group.values():
            if entry.cockpit_device_id is None:
                continue
            assert entry.cockpit_device_id == g.devices.DISPLAYS, entry.name
            for event in ('down', 'up', 'pressed', 'action'):
                command = entry[event]
                if command is not None:
                    assert g.listened[command], f'{kind}: {entry.name}: {event}={command} not subscribed'


def test_keyboard_and_joystick_button_routes_match():
    lua, load = cockpit()
    def routes(kind):
        # Preserve existing display names because saved user bindings include them.
        aliases = {'Refueling Bay': 'Refueling Hatch'}
        return {aliases.get(e.name,e.name): tuple(e[k] for k in ('down','up','pressed','cockpit_device_id','value_down','value_up'))
                for e in profile(lua, load, kind).keyCommands.values()}
    assert routes('keyboard') == routes('joystick')


def test_keyboard_default_chords_are_unique():
    lua, load = cockpit()
    seen = {}
    for entry in profile(lua, load, 'keyboard').keyCommands.values():
        if entry.combos is None:
            continue
        for combo in entry.combos.values():
            modifiers = tuple(sorted(combo.reformers.values())) if combo.reformers else ()
            chord = (combo.key, modifiers)
            assert chord not in seen, f'{chord}: {seen.get(chord)} / {entry.name}'
            seen[chord] = entry.name


@pytest.mark.skipif(not EFM.is_dir(), reason='EFM source checkout required')
def test_custom_global_bindings_have_a_lua_or_efm_receiver():
    lua, load = cockpit()
    lua_ids = set()
    for path in (SCRIPTS / 'Systems').glob('*.lua'):
        source = re.sub(r'--[^\n]*', '', path.read_text(encoding='utf-8-sig'))
        for symbol in re.findall(r'\b(?:Keys|f117_commands|hotas_commands|native_commands)\.\w+', source):
            value = lua.eval(symbol)
            if isinstance(value, (int,float)):
                lua_ids.add(value)
    constants = dict((name,int(value)) for name,value in re.findall(
        r'constexpr int (\w+)\s*=\s*(\d+)\s*;', (EFM/'Inputs.h').read_text()))
    efm_ids = set()
    for path in EFM.rglob('*.cpp'):
        source = re.sub(r'//[^\n]*', '', path.read_text(encoding='utf-8-sig',errors='replace'))
        cases = re.findall(r'\bcase\s+(\w+)\s*:', source)
        cases += re.findall(r'\bcommand\s*(?:==|!=)\s*(\w+)', source)
        for case in cases:
            if case in constants:
                efm_ids.add(constants[case])
    for kind in ('keyboard','joystick'):
        for entry in profile(lua, load, kind).keyCommands.values():
            if entry.cockpit_device_id is not None:
                continue
            for event in ('down','up','pressed'):
                command = entry[event]
                if command is not None and command >= 10000:
                    assert command in lua_ids | efm_ids, f'{kind}: {entry.name}: orphan {command}'


@pytest.mark.parametrize('kind', ['keyboard', 'joystick'])
@pytest.mark.parametrize('name,param,direction', [
    ('IR Gain Increase','F117_IRADS_GAIN',1),
    ('IR Gain Decrease','F117_IRADS_GAIN',-1),
    ('IR Level Increase','F117_IRADS_LEVEL',1),
    ('IR Level Decrease','F117_IRADS_LEVEL',-1),
])
def test_bound_image_buttons_change_the_display_parameter(kind, name, param, direction):
    lua, load = cockpit()
    binding = next(e for e in profile(lua, load, kind).keyCommands.values() if e.name == name)
    g = lua.globals()
    before = g._parameters[param]
    assert g.listened[binding.down], name
    g.SetCommand(binding.down, binding.value_down)
    assert (g._parameters[param] - before) * direction > 0, name


@pytest.mark.parametrize('kind', ['keyboard', 'joystick'])
def test_bound_fov_and_nws_forward_to_efm(kind):
    lua, load = cockpit()
    g = lua.globals()
    bindings = {e.name:e for e in profile(lua, load, kind).keyCommands.values()}
    for name, command, value in [
        ('IRADS FOV - Narrow',g.f117_commands.IRADS_ZOOM_AXIS,1),
        ('IRADS FOV - Wide',g.f117_commands.IRADS_ZOOM_AXIS,-1),
        ('Nosewheel Steering Authority (Hold for 45 deg Range)',g.f117_commands.NWS_AUTHORITY_ON,1),
    ]:
        b = bindings[name]
        g.SetCommand(b.down,b.value_down)
        assert tuple(g.calls[len(g.calls)].values()) == (command,value)
    b = bindings['Nosewheel Steering Authority (Hold for 45 deg Range)']
    g.SetCommand(b.up,b.value_up)
    assert tuple(g.calls[len(g.calls)].values()) == (g.f117_commands.NWS_AUTHORITY_OFF,1)
