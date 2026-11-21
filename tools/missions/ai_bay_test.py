"""Run an AI Mk-82 attack and log standard bay argument 26 around release.

The mission's AI has no EFM or cockpit device. A temporary hook unpauses and
ends the run after 120 seconds. Close DCS before running this script.
"""
from pathlib import Path
import sys
import subprocess
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from missions import bay_shots
from missions.miz import Miz
from missions.store_drop_test import lua_string

SCRIPT = r'''
local bomb = '{BCE4E030-38E9-423E-98ED-24BE3DA87C32}'
local attack = {id='Bombing', params={x=-83000, y=818000, directionEnabled=false,
    attackQty=1, attackQtyLimit=true, expend='One', groupAttack=false,
    weaponType=2032, altitude=4500, altitudeEnabled=true}}
local group = coalition.addGroup(country.id.USA, Group.Category.AIRPLANE, {
    name='F117_AI_BAY_TEST', groupId=9100, task='Ground Attack',
    units={{name='F117_AI_BAY_TEST_1', unitId=9101, type='F-117-NightHawk', skill='Excellent',
        x=-83000, y=805000, alt=4500, alt_type='BARO', speed=230, heading=math.pi/2,
        payload={fuel=3000, flare=0, chaff=0, gun=0, pylons={[1]={CLSID=bomb}, [2]={CLSID=bomb}}}}},
    route={points={{x=-83000, y=805000, alt=4500, alt_type='BARO', speed=230,
        type='Turning Point', action='Turning Point', task={id='ComboTask', params={tasks={}}}},
        {x=-83000, y=830000, alt=4500, alt_type='BARO', speed=230,
        type='Turning Point', action='Turning Point', task={id='ComboTask', params={tasks={}}}}}}
})
-- Let the spawned group's initial route initialize before replacing its task.
timer.scheduleFunction(function()
    group:getController():setTask(attack)
    env.info('F117_AI_BAYS bombing task assigned')
end, nil, timer.getTime()+1)
local last = -1
local last_report = -10
local function sample(_, now)
    local u = Unit.getByName('F117_AI_BAY_TEST_1')
    if not u or not u:isExist() then return end
    local value = u:getDrawArgumentValue(26)
    if now-last_report >= 5 then
        local p = u:getPoint()
        env.info(string.format('F117_AI_BAYS position t=%.1f x=%.1f z=%.1f alt=%.1f ammo=%d',
            now, p.x, p.z, p.y, #(u:getAmmo() or {})))
        last_report = now
    end
    if math.abs(value-last) > 0.01 then
        env.info(string.format('F117_AI_BAYS t=%.2f arg26=%.3f arg904=%.3f arg905=%.3f arg906=%.3f',
            now, value, u:getDrawArgumentValue(904), u:getDrawArgumentValue(905), u:getDrawArgumentValue(906)))
        last = value
    end
    return now + 0.1
end
timer.scheduleFunction(sample, nil, timer.getTime()+0.1)
world.addEventHandler({onEvent=function(self,e)
    if e.id == world.event.S_EVENT_SHOT and e.initiator and e.initiator:getName()=='F117_AI_BAY_TEST_1' then
        env.info('F117_AI_BAYS SHOT '..e.weapon:getTypeName()..' arg26='..e.initiator:getDrawArgumentValue(26))
    end
end})
'''


def main():
    results = HERE / 'results/bays_ai'
    results.mkdir(parents=True, exist_ok=True)
    mission = results / 'ai_bays.miz'
    bay_shots.build_mission(mission, bay_shots.STORES['mk-82'])
    miz = Miz.load(mission)
    miz.mission['trig']['actions'][1] = 'a_do_script(' + lua_string(SCRIPT) + ');'
    miz.save(mission)
    if 'DCS.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout:
        raise SystemExit('Close DCS first.')
    hook_path = bay_shots.HOOK_PATH.with_name('zz_f117_ai_bays.lua')
    done = bay_shots.LOGS / 'F117_ai_bays.done'
    done.unlink(missing_ok=True)
    hook_path.write_text(r'''
local hook = {}
function hook.onSimulationFrame()
    if DCS.getPause() then DCS.setPause(false) end
    if DCS.getModelTime() > 120 then
        local f = io.open(lfs.writedir()..'Logs/F117_ai_bays.done','w')
        if f then f:write('done'); f:close() end
        DCS.exitProcess()
    end
end
DCS.setUserCallbacks(hook)
''', encoding='utf-8')
    process = subprocess.Popen([str(bay_shots.base.DCS_EXE), '--mission', str(mission)])
    try:
        deadline = time.monotonic() + 360
        while process.poll() is None and not done.exists() and time.monotonic() < deadline:
            time.sleep(0.5)
        try:
            process.wait(30)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(30)
    finally:
        hook_path.unlink(missing_ok=True)
    log = bay_shots.LOGS / 'dcs.log'
    lines = [line for line in log.read_text(encoding='utf-8', errors='replace').splitlines()
             if 'F117_AI_BAYS' in line or 'ERROR   SCRIPTING' in line]
    (results / 'ai.log').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
    assert any('SHOT' in line for line in lines), 'AI did not release in the test interval'
    assert any('arg26=1.000' in line for line in lines), 'AI never opened standard bay argument'


if __name__ == '__main__':
    main()
