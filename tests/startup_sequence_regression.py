"""Run with the companion mod path: exercises workspace Electrical.lua in Lua 5.1."""
from pathlib import Path
import sys
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOD = Path(sys.argv[1])

def device(birth='GROUND_COLD'):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
values={}; listened={}; rpm_l=0; rpm_r=0
sensor={getEngineLeftRPM=function()return rpm_l end,getEngineRightRPM=function()return rpm_r end,
 getSelfVelocity=function()return 0,0,0 end}
function get_base_data()return sensor end
function get_param_handle(n)return {get=function()return values[n] or 0 end,set=function(_,v)values[n]=v end}end
function GetSelf()return {listen_command=function(_,c)listened[c]=true end}end
function make_default_activity()end
function print_message_to_user()end
LockOn_Options={script_path='',init_conditions={}}
''')
    g = lua.globals()
    g.LockOn_Options.script_path = (MOD / 'Cockpit/Scripts').as_posix() + '/'
    g.LockOn_Options.init_conditions.birth_place = birth
    def load(path):
        path = Path(str(path))
        local = ROOT / path.relative_to(MOD)
        return lua.execute((local if local.exists() else path).read_text(encoding='utf-8-sig'))
    g.dofile = load
    load(MOD / 'Cockpit/Scripts/Systems/Electrical.lua')
    g.post_initialize()
    return lua, g

def run(g, seconds):
    for _ in range(round(seconds / .05)):
        g.update()

lua, g = device()
v = g['values']
assert g.listened[87]
g.SetCommand(g.Keys.PowerOnOff, 1)
g.SetCommand(g.native_commands.APU_START, 1)
run(g, 12)
assert (v.F117_APU_STATE, v.mainpower, v.F117_PWR_IRADS) == (2, 0, 0)
g.rpm_r = .60
v.F117_ENGINE_START_R = 4
run(g, 12)
assert v.mainpower == 1 and v.F117_ON_HUD == 1 and v.F117_ON_CMDI_R == 1
assert v.F117_PWR_IRADS == 0
v.F117_ENGINE_START_L = 3
g.rpm_l = .58
run(g, 2)
assert v.F117_PWR_IRADS == 0
v.F117_ENGINE_START_L = 4
g.rpm_l = .60
run(g, 12)
assert v.F117_PWR_IRADS == 0  # both engines alone must NEVER start the IRADS BIT
print('PASS battery/APU dark; first generator boots HUD/displays; no IRADS BIT before command')
g.SetCommand(87, 0)
g.update()
assert v.F117_PWR_IRADS == 1 and v.F117_ON_IRADS == 0
run(g, 1)
assert v.F117_PWR_IRADS == 2
run(g, 9)
assert v.F117_ON_IRADS == 1
# Once startup is complete, one remaining generator keeps avionics and IRADS alive.
g.rpm_l = 0
v.F117_ENGINE_START_L = 0
run(g, 1)
assert v.F117_ON_IRADS == 1 and v.F117_ON_HUD == 1
# A new engine-start cycle inhibits the sensor again, without rebooting the HUD.
v.F117_ENGINE_START_L = 1
run(g, 1)
assert v.F117_PWR_IRADS == 0 and v.F117_ON_HUD == 1
v.F117_ENGINE_START_L = 4
g.rpm_l = .60
run(g, 10)
assert v.F117_ON_IRADS == 1
g.SetCommand(87, 0)
g.update()
assert v.F117_PWR_IRADS == 0
run(g, 15)
assert v.F117_PWR_IRADS == 0
print('PASS commanded IRADS BIT/ready/off, single-generator operation and engine-restart inhibition')
# Selecting IRADS early queues the selection but cannot bypass engine startup.
lua, g = device()
v = g['values']
g.SetCommand(87, 0)
g.SetCommand(g.Keys.PowerOnOff, 1)
g.rpm_r = .60
v.F117_ENGINE_START_R = 4
run(g, 15)
assert v.F117_PWR_IRADS == 0
g.rpm_l = .60
v.F117_ENGINE_START_L = 4
run(g, 10)
assert v.F117_ON_IRADS == 1
g.rpm_l = g.rpm_r = 0
v.F117_ENGINE_START_L = v.F117_ENGINE_START_R = 0
run(g, 1)
assert v.mainpower == 0 and v.F117_PWR_IRADS == 0
# External power remains a supported main-bus source, but cannot auto-enable IRADS.
lua, g = device()
v = g['values']
v.F117_WOW = 1
g.SetCommand(g.Keys.PowerOnOff, 1)
g.SetCommand(g.Keys.GroundPowerToggle, 1)
run(g, 12)
assert v.F117_ON_HUD == 1 and v.F117_PWR_IRADS == 0
for birth in ('GROUND_HOT', 'AIR_HOT'):
    lua, g = device(birth)
    v = g['values']
    assert v.F117_ON_HUD == 1 and v.F117_ON_IRADS == 1
    run(g, 1.5)
    assert v.F117_ON_IRADS == 1
    g.rpm_l = g.rpm_r = .60
    run(g, 2)
    assert v.F117_ON_IRADS == 1
    g.SetCommand(87, 0)
    g.update()
    assert v.F117_PWR_IRADS == 0
print('PASS early-command gating, loss of power, external power and hot/air starts')

# Display selection preserves a completed BIT; a bus outage requires a fresh BIT.
lua,g=device();v=g['values']
g.SetCommand(g.Keys.PowerOnOff,1);g.rpm_l=g.rpm_r=.60
v.F117_ENGINE_START_L=v.F117_ENGINE_START_R=4
g.SetCommand(87,0);run(g,10)
assert v.F117_ON_IRADS==1
g.SetCommand(87,0);g.update();assert v.F117_PWR_IRADS==0
g.SetCommand(87,0);g.update();assert v.F117_ON_IRADS==1
g.SetCommand(g.Keys.PowerOnOff,1);g.update();assert v.F117_PWR_IRADS==0
g.SetCommand(g.Keys.PowerOnOff,1);g.update();assert v.F117_ON_IRADS==0
print('PASS completed IRADS BIT survives display toggles; bus loss resets BIT')
