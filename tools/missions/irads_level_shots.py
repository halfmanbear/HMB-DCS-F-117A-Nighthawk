"""Build paired IRADS level calibration missions; optionally fly and capture them.

    python tools/missions/irads_level_shots.py
    python tools/missions/irads_level_shots.py --run --variant day
    python tools/missions/irads_level_shots.py --run --variant night
    python tools/missions/irads_level_shots.py --run --variant both --transitions

Gain is left at its startup default. Uses the store-drop flight setup and
the bay/vortex screenshot handshake. Requires DCS closed before --run.
"""
import argparse
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from missions import store_drop_test as drop
from missions import vortex_shots as shots
from missions.bay_shots import acknowledge_shot
from missions.miz import Miz

RESULTS = HERE / 'results/irads_level'
OVERRIDE = HERE.parents[1] / 'Cockpit/Scripts/Systems/IRADS_LevelCalibration.local.lua'
# Sample every fourth control detent across 0..1; keep startup gain.
STEPS = {variant: list(range(0, 161, 4)) for variant in ('day', 'night')}

HOOK = r'''
local OUT=__OUT__
local LEVELS=__LEVELS__
local LOW,HIGH=__LOW__,__HIGH__
local hook={}
local start,phaseAt,heading,index,scene,stage,requestAt,actions,file,stepAt,lastStatus
local finished=false
local holding=false
local targetNames=__NAMES__
local targets=__TARGETS__
local settles=__SETTLES__
local function params()
    local text=net.dostring_in('export','return list_cockpit_params()') or ''
    local p={}
    for k,v in text:gmatch('([%w_]+):([^\n]*)') do p[k]=tonumber(v) end
    return p
end
local function clamp(v,a,b) return math.max(a,math.min(b,v)) end
local function finish(reason)
    Export.LoSetCommand(10120,0)
    if file then file:write('# '..reason..'\n');file:close();file=nil end
    local f=assert(io.open(OUT..'/done.txt','w'));f:write(reason);f:close()
    finished=true
    DCS.exitProcess()
end
local function aim(now,p)
    local y=p.F117_IRADS_LOS_Y
    local x,z=p.F117_IRADS_LOS_X,p.F117_IRADS_LOS_Z
    if not y or not x or not z or (p.F117_IRADS_LOS_VALID or 0)<.5 then
        return false
    end
    y=y/math.max(.00001,math.sqrt(x*x+y*y+z*z))
    local error=targets[scene]-y
    -- The EFM ignores axis magnitudes <= .05. A plain proportional
    -- controller stalls outside our .012 LOS tolerance without this floor.
    local speed=clamp(math.abs(error)*3,.08,.35)
    -- Acquire near the centre, then allow small flight-induced drift. The
    -- previous single boundary repeatedly restarted the settling timer.
    local tolerance=holding and .025 or .006
    holding=math.abs(error)<tolerance
    Export.LoSetCommand(10120,holding and 0 or (error<0 and -speed or speed))
    return holding
end
local function set_level()
    if index==1 then return end -- capture untouched mission default first
    local travel=math.sqrt(clamp((LEVELS[index-1]-LOW)/(HIGH-LOW),0,1))
    net.dostring_in('export',string.format(
        'local d=GetDevice(7); if d then d:performClickableAction(3009,%.9f) end',travel*2-1))
end
function hook.onSimulationFrame()
    if finished then return end
    if DCS.getPause() then DCS.setPause(false) end
    local now=DCS.getModelTime()
    local me=Export.LoGetSelfData()
    if not start then
        if now<3 or not me then return end
        start,heading,phaseAt=now,me.Heading,now
        index,scene,stage=1,1,'warm'
        file=assert(io.open(OUT..'/measurements.csv','w'))
        file:write('shot,time,level,gain,los_x,los_y,los_z,native,power\n')
        local ok,Input=pcall(require,'Input')
        if ok and Input and Input.getEnvTable then actions=Input.getEnvTable().Actions end
        if actions and actions.iCommandViewCockpit then DCS.dispatchDigitalAction(actions.iCommandViewCockpit) end
        return
    end
    if not me then return finish('FAIL aircraft lost') end
    if now-start>3600 then return finish('FAIL overall timeout') end
    local vy=(Export.LoGetVectorVelocity() or {y=0}).y
    local climb=clamp((4500-me.LatLongAlt.Alt)*.08,-15,15)
    Export.LoSetCommand(2001,clamp(.02*(climb-vy)-.6*me.Pitch,-.4,.4))
    local err=heading-me.Heading
    while err>math.pi do err=err-2*math.pi end
    while err< -math.pi do err=err+2*math.pi end
    Export.LoSetCommand(2002,clamp(1.5*(clamp(2.5*err,-.5,.5)-me.Bank),-.5,.5))
    Export.LoSetCommand(2003,0)
    Export.LoSetCommand(2004,clamp(.08*((Export.LoGetTrueAirSpeed() or 230)-230),-1,1))
    local p=params()
    if not lastStatus or now-lastStatus>1 then
        local f=assert(io.open(OUT..'/status.txt','w'))
        f:write(string.format('%d/%d %s %s level=%.5f LOS_Y=%.5f',index,#LEVELS+1,targetNames[scene],stage,
            p.F117_IRADS_BRIGHTNESS or -1,p.F117_IRADS_LOS_Y or 0));f:close()
        lastStatus=now
    end
    if stepAt and stage~='capture' and now-stepAt>30 then
        return finish('FAIL step timeout; see status.txt for last level and LOS')
    end
    if stage=='warm' then
        if now-phaseAt<20 then return end
        if (p.F117_IRADS_POWER or 0)<.5 then return finish('FAIL IRADS not powered') end
        stage,phaseAt,stepAt='aim',now,now
    end
    if stage=='aim' then
        if aim(now,p) then stage,phaseAt='settle',now end
        if now-phaseAt>25 then
            return finish(string.format('FAIL LOS aiming timeout: valid=%s x=%s y=%s z=%s',
                tostring(p.F117_IRADS_LOS_VALID),tostring(p.F117_IRADS_LOS_X),
                tostring(p.F117_IRADS_LOS_Y),tostring(p.F117_IRADS_LOS_Z)))
        end
    elseif stage=='settle' then
        if not aim(now,p) then stage,phaseAt='aim',now;return end
        if now-phaseAt<settles[scene] then return end
        if index>1 and math.abs((p.F117_IRADS_BRIGHTNESS or -1)-LEVELS[index-1])>.0001 then
            return finish('FAIL IR Level did not reach requested detent')
        end
        local name=(index==1 and 'default' or string.format('level_%05.2f',LEVELS[index-1]*100))..'_'..targetNames[scene]
        local f=assert(io.open(OUT..'/shot.req','w'));f:write(name);f:close()
        file:write(string.format('%s,%.2f,%.6f,%.6f,%.5f,%.5f,%.5f,%d,%d\n',
            name,now,p.F117_IRADS_BRIGHTNESS or -1,p.F117_IRADS_CONTRAST or -1,
            p.F117_IRADS_LOS_X or 0,p.F117_IRADS_LOS_Y or 0,p.F117_IRADS_LOS_Z or 0,
            p.F117_NATIVE_BRIGHTNESS_ACTIVE or 0,p.F117_IRADS_POWER or 0));file:flush()
        if actions and actions.iCommandScreenShot then DCS.dispatchDigitalAction(actions.iCommandScreenShot) end
        stage,requestAt='capture',now
    elseif stage=='capture' then
        local f=io.open(OUT..'/shot.req','r')
        if f then f:close();if now-requestAt>15 then return finish('FAIL screenshot acknowledgement timeout') end;return end
        scene=scene+1
        if scene>#targets then
            scene,index=1,index+1
            if index>#LEVELS+1 then return finish('done') end
            set_level()
        end
        stage,phaseAt,stepAt='aim',now,now
    end
end
DCS.setUserCallbacks(hook)
'''


SCENE_SCRIPT = r'''
-- A repeatable corridor under the flight path, with structures and moving
-- unarmed trucks. DCS supplies the thermal signatures; no artificial heat map.
for i=0,36 do
    local x,z=-83000,823000+i*1500
    for j=-1,1 do
        coalition.addStaticObject(country.id.RUSSIA,{
            name=string.format('IRADS building %d %d',i,j),type='Tech combine',
            category='Fortifications',x=x+j*250,y=z+j*100,heading=0,dead=false})
    end
    local rx,rz=land.getClosestPointOnRoads('roads',x,z)
    rx,rz=rx or x,rz or z
    coalition.addGroup(country.id.RUSSIA,Group.Category.GROUND,{
        name='IRADS warm trucks '..i,visible=false,hidden=false,
        units={{type='Ural-375',name='IRADS truck '..i,x=rx,y=rz,heading=0,skill='Average'}},
        route={points={
            {x=rx,y=rz,type='Turning Point',action='Off Road',speed=5,
             task={id='ComboTask',params={tasks={}}}},
            {x=rx+500,y=rz+500,type='Turning Point',action='Off Road',speed=5,
             task={id='ComboTask',params={tasks={}}}}}}})
end
env.info('IRADS calibration scene ready: structures, roads and moving trucks')
'''


def build(variant, folder, transitions=False, sample_levels=None):
    folder.mkdir(parents=True, exist_ok=True)
    mission = folder / f'irads_level_{variant}.miz'
    drop.build_mission(drop.STORES[0], mission)
    miz = Miz.load(mission)
    miz.mission['start_time'] = (12 if variant == 'day' else 23) * 3600
    # Remove the store-drop event handler and every weapon. No attack commands.
    miz.mission['trig'] = miz.table()
    miz.mission['trigrules'] = miz.table()
    trig = miz.mission['trig']
    trig['conditions'] = miz.table({1: 'return(true)'})
    trig['actions'] = miz.table({1: 'a_do_script(' + drop.lua_string(SCENE_SCRIPT) + ');'})
    trig['funcStartup'] = miz.table({1: 'if mission.trig.conditions[1]() then mission.trig.actions[1]() end'})
    trig['flag'] = miz.table({1: True})
    miz.mission['trigrules'] = miz.table({1: {
        'rules': {}, 'eventlist': '', 'predicate': 'triggerStart', 'comment': 'IRADS calibration scene',
        'actions': {1: {'predicate': 'a_do_script', 'text': SCENE_SCRIPT, 'KeyDict_text': ''}}}})
    for _, unit in miz.player_units():
        unit['payload']['pylons'] = miz.table()
    sequence = ('Ground / sky / reacquired ground / settled ground at the startup default and six reference levels. '
                'Uses the production nonlinear control mapping and limits.' if transitions else
                'Ground-only sweep from 0 to 1 at increments of 0.025. '
                'The Python runner temporarily enables the extended range.')
    miz.set_text('descriptionText',
                 f'IRADS Level calibration ({variant}). Same location, altitude and weather in both variants. '
                 'IRADS is powered on at hot air start; leave gain at its startup preset. '
                 'The Python --run option automates pointing, level changes and screenshots. '
                 'The terrain corridor includes industrial structures and moving trucks near roads. ' + sequence)
    miz.save(mission)
    levels = [.05, .065, .10, .40, .60, .80] if transitions else [n*.00625 for n in STEPS[variant]]
    if sample_levels is not None:
        levels = sample_levels
    names = ['ground_before', 'sky', 'ground_return', 'ground_settled'] if transitions else ['ground']
    targets = [-.31, .035, -.31, -.31] if transitions else [-.31]
    settles = [1, 1, .25, 1] if transitions else [1]
    low, high = (.025, .80) if transitions else (0, 1)
    if any(not low <= value <= high for value in levels):
        raise ValueError(f'Capture levels must be within {low}..{high}')
    hook = HOOK.replace('__OUT__', drop.lua_string(folder.resolve().as_posix()))
    for key, values in [('LEVELS', levels), ('TARGETS', targets), ('SETTLES', settles)]:
        hook = hook.replace('__'+key+'__', '{' + ','.join(map(str, values)) + '}')
    hook = hook.replace('__NAMES__', '{' + ','.join(drop.lua_string(n) for n in names) + '}')
    hook = hook.replace('__LOW__', str(low)).replace('__HIGH__', str(high))
    (folder / 'capture_hook.lua').write_text(hook, encoding='utf-8')
    (folder / 'plan.json').write_text(json.dumps({
        'variant': variant, 'gain': .8 if variant == 'day' else .96,
        'levels': ['mission default'] + levels,
        'scenes': names, 'settle_seconds': settles, 'extended_range': not transitions,
        'note': 'Verify LOS/settings in measurements.csv. Transition tests use the production range; full sweeps temporarily extend it.'
    }, indent=2) + '\n', encoding='utf-8')
    return mission


def run(mission, folder):
    if 'DCS.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout:
        raise SystemExit('Close DCS first; the calibration harness starts and exits its own DCS session.')
    hook_path = drop.SAVED_GAMES / 'Scripts/Hooks/zz_f117_irads_level_shots.lua'
    if hook_path.exists():
        raise SystemExit(f'Refusing to overwrite existing hook: {hook_path}')
    if OVERRIDE.exists():
        raise SystemExit(f'Remove the stale calibration override before running: {OVERRIDE}')
    request, done = folder / 'shot.req', folder / 'done.txt'
    request.unlink(missing_ok=True)
    done.unlink(missing_ok=True)
    (folder / 'status.txt').unlink(missing_ok=True)
    shots.RESULTS = folder
    before = shots.screenshots()
    hook_path.write_bytes((folder / 'capture_hook.lua').read_bytes())
    process = None
    try:
        if json.loads((folder / 'plan.json').read_text())['extended_range']:
            with OVERRIDE.open('x', encoding='utf-8') as override:
                override.write('-- Temporary IRADS screenshot calibration range: 0..1\nreturn true\n')
        process = subprocess.Popen([str(drop.DCS_EXE), '--mission', str(mission.resolve())])
        deadline = time.monotonic() + 5400
        next_status = time.monotonic() + 5
        while not done.exists():
            if process.poll() is not None:
                raise RuntimeError('DCS closed before calibration completed')
            if time.monotonic() > deadline:
                raise TimeoutError('DCS calibration exceeded 90 minutes')
            if request.exists():
                name = request.read_text().strip()
                path = shots.capture(name, before)
                if path is None:
                    raise RuntimeError(f'No screenshot captured for {name}')
                print('captured', path, flush=True)
                before = shots.screenshots()
                acknowledge_shot(request)
            if time.monotonic() >= next_status:
                status = folder / 'status.txt'
                if status.exists():
                    print('progress', status.read_text(), flush=True)
                next_status = time.monotonic() + 5
            time.sleep(.1)
        reason = done.read_text()
        if reason != 'done':
            raise RuntimeError(reason)
        print('Completed', mission.name, flush=True)
    except KeyboardInterrupt:
        print('Cancelled; closing the test session and removing temporary files.', flush=True)
        return False
    finally:
        previous_signal = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            try:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
            finally:
                hook_path.unlink(missing_ok=True)
                OVERRIDE.unlink(missing_ok=True)
                acknowledge_shot(request)
        finally:
            signal.signal(signal.SIGINT, previous_signal)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--variant', choices=['day', 'night', 'both'], default='both')
    parser.add_argument('--transitions', action='store_true', help='Test proposed defaults against ground/sky/ground exposure with production limits')
    parser.add_argument('--levels', nargs='+', type=float, help='Capture selected internal video levels instead of the standard list')
    args = parser.parse_args()
    variants = ['day', 'night'] if args.variant == 'both' else [args.variant]
    for variant in variants:
        folder = RESULTS / variant
        if args.transitions:
            folder = folder / 'transitions'
        mission = build(variant, folder, transitions=args.transitions, sample_levels=args.levels)
        print('Built', mission, flush=True)
        if args.run:
            if run(mission, folder) is False:
                return


if __name__ == '__main__':
    main()
