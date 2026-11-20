"""Exercise the real lighting device with DCS parameter/draw-argument stubs."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
for birth in ('GROUND_COLD', 'GROUND_HOT', 'AIR_HOT'):
    lua = LuaRuntime()
    lua.execute('''
params, args = {}, {}
LockOn_Options = {script_path='', init_conditions={}}
function dofile(_) end
Keys={FloodLight=10141}
native_commands={LANDING_LIGHT=328,NAV_LIGHTS=175,TAXI_LIGHT=1398,BEACON_LIGHT=518,COCKPIT_LIGHT=300}
function get_param_handle(name)
 if not params[name] then params[name]={value=0,set=function(s,v) s.value=v end,get=function(s) return s.value end} end
 return params[name]
end
function make_default_activity(_) end
function GetSelf() return {listen_command=function(...) end} end
function get_base_data() return {getEngineLeftRPM=function() return 0 end,getEngineRightRPM=function() return 0 end} end
function create_sound_host(...) return {create_sound=function(...) return {play_once=function() end} end} end
function set_aircraft_draw_argument_value(arg,value) args[arg]=value end
function get_aircraft_draw_argument_value(arg) return args[arg] or 0 end
''')
    g = lua.globals()
    g.LockOn_Options.init_conditions.birth_place = birth
    lua.execute((ROOT / 'Cockpit/Scripts/Systems/lights_system.lua').read_text())
    g.post_initialize()
    g.update()
    assert g.params.PANEL_LGT.value == 0 and g.args[195] == 0
    g.params.mainpower.value = 1
    g.update()
    assert g.params.PANEL_LGT.value == 1 and g.args[195] == 1
    g.params.mainpower.value = 0
    g.update()
    assert g.params.PANEL_LGT.value == 0 and g.args[195] == 0
    g.params.mainpower.value = 1
    g.update()
    assert g.params.PANEL_LGT.value == 1  # switch setting survives power loss
    g.SetCommand(300)
    g.update()
    assert g.params.PANEL_LGT.value == 0
    print('PASS', birth, 'power gating, switch operation and power restoration')
