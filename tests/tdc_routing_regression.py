"""Exercise stock command subscription and actual Displays.lua designation routing."""
from pathlib import Path
import sys
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[1]
mod = Path(sys.argv[1])
vm = LuaRuntime()
g = vm.globals()
g.LockOn_Options = vm.table_from({'script_path': (mod/'Cockpit/Scripts').as_posix()+'/'})
vm.execute('''
parameters={}; listened={}; events={}
function get_param_handle(n)
 if not parameters[n] then parameters[n]={value=0,get=function(s)return s.value end,set=function(s,v)s.value=v end} end
 return parameters[n]
end
function make_default_activity()end
function GetSelf()return {listen_command=function(_,c)listened[c]=true end}end
function get_base_data()return {}end
function dispatch_action(_,id,value)events[#events+1]={id,value}end
''')
def load(path):
    path = Path(str(path))
    local = root / path.relative_to(mod)
    return vm.execute((local if local.exists() else path).read_text(encoding='utf-8-sig'))
g.dofile = load
load(mod/'Cockpit/Scripts/Systems/Displays.lua')
n = g.native_commands
for key in ('TDC_DEPRESS_ON','TDC_DEPRESS_OFF','DSS_OFF','DSS_UP','DSS_LEFT','DSS_DOWN','DSS_RIGHT'):
    assert g.listened[n[key]], key
# Model delivery only for stock commands the Lua device actually subscribed to.
def deliver(command, value):
    assert g.listened[command], command
    g.SetCommand(command, value)
def events():
    result = [(e[1],e[2]) for e in g.events.values()]
    vm.execute('events={}')
    return result
for _ in range(2):
    deliver(n.TDC_DEPRESS_ON,1)
    deliver(n.TDC_DEPRESS_OFF,0)
    assert events() == [(10114,1),(10114,0)]
deliver(n.DSS_UP,1)
events()
deliver(n.TDC_DEPRESS_ON,1)
deliver(n.TDC_DEPRESS_OFF,0)
assert not any(e[0] == 10114 for e in events())
deliver(n.DSS_OFF,1)
events()
deliver(n.TDC_DEPRESS_ON,1)
deliver(n.TDC_DEPRESS_OFF,0)
assert events() == [(10114,1),(10114,0)]
print('PASS real Displays.lua: stock HOTAS subscription, one designation per press, release, HUD isolation and IRADS reselection')
