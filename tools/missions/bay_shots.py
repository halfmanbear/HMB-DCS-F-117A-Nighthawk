"""Fly the F-117 level with a store on each pylon and photograph the weapon bays as they open and close.

    python tools/missions/bay_shots.py              # fly and capture
    python tools/missions/bay_shots.py --store gbu-10
    python tools/missions/bay_shots.py --store mk-84 --right gbu-31   # a different store on each pylon
    python tools/missions/bay_shots.py --build-only

Builds a mission from the Caucasus free flight quick start (a GBU-27 on each pylon, or the --store, noon, no wind,
600 m over the Black Sea). A temporary hook in Saved Games/DCS/Scripts/Hooks unpauses, holds level
flight, switches to the free camera and steps through the bay states with the bay commands:
both open, left closed, both open, right closed, both closed. Each state is photographed from
below-left, below-right, below and in front. Shots, the draw argument values at each shot and the
DCS log lines go to tools/missions/results/bays/ (bays_<store>/ for another store). Close DCS first. About
two minutes.
"""
import argparse
import csv
import math
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from missions import vortex_shots as base  # noqa: E402
from missions.miz import Miz  # noqa: E402
from missions.store_drop_test import lua_string  # noqa: E402

RESULTS = HERE / 'results/bays'
HOOK_PATH = base.SAVED_GAMES / 'Scripts/Hooks/zz_f117_bay_shots.lua'
LOGS = base.LOGS
GBU_27 = '{EF0A9419-01D6-473B-99A3-BEBDB923B14D}'
STORES = {'gbu-27': GBU_27, 'gbu-10': '{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}',
          'gbu-12': '{DB769D48-67D7-42ED-A2BE-108D566C8B1E}', 'gbu-31': '{GBU-31}', 'gbu-31v3': '{GBU-31V3B}',
          'gbu-32': '{GBU_32_V_2B}', 'agm-65d': '{444BA8AE-82A7-4345-842E-76154EFCCA47}',
          'agm-65e': '{F16A4DE0-116C-4A71-97F0-2CF85B0313EF}', 'agm-154a': '{AGM-154A}', 'agm-154b': '{AGM-154B}',
          'agm-154c': '{9BCC2A2B-5708-4860-B1F1-053A18442067}', 'cbu-105': '{CBU_105}',
          'mk-82': '{BCE4E030-38E9-423E-98ED-24BE3DA87C32}', 'mk-84': '{AB8B8299-F1CC-4359-89B5-2172E0CF4A5A}'}

# State name and the bay commands issued on entering it: 10101 open both, 10102 close both,
# 10131 toggle left, 10132 toggle right.
STATES = "{{'closed', {}}, {'both_open', {10101}}, {'left_closed', {10131}}, {'both_open_again', {10131}}, " \
         "{'right_closed', {10132}}, {'both_closed', {10102}}}"
# Camera and aim points in the body frame (forward, up, right), metres.
SHOTS = """{
    {'below_left',  {-3, -7, -7}, {1.3, -0.6, 0}},
    {'below_right', {-3, -7,  7}, {1.3, -0.6, 0}},
    {'below',       {-1, -10, 0}, {1.3, -0.6, 0}},
    {'front',       { 9, -3,  0}, {1.3, -0.8, 0}},
}"""

HOOK = r"""-- Temporary hook written by tools/missions/bay_shots.py. Safe to delete.
local logs = lfs.writedir() .. 'Logs\\'
local SPEED, ALT = __SPEED__, __ALT__
local REPLAY = __REPLAY__
local STATES = __STATES__
local SHOTS = __SHOTS__
local SETTLE = 4.0 -- the bays need 2 s to move
local hook = {}
local startTime, finished, handle
local state, shot, stateTime, shotTime, waitingFile = 0, 1, 0, 0, nil
local Actions

local function finish(why)
    log.write('F117BAYS', log.INFO, 'finish ' .. why)
    if handle then handle:write('# ' .. why .. '\n'); handle:close() end
    finished = true
    local done = io.open(logs .. 'F117_vortex_shots.done', 'w'); done:write(why); done:close()
    DCS.exitProcess()
end

local function clamp(v, lo, hi) return math.max(lo, math.min(hi, v)) end

local function axes(me)
    local h, p, b = me.Heading, me.Pitch, me.Bank
    local f = {x = math.cos(p) * math.cos(h), y = math.sin(p), z = math.cos(p) * math.sin(h)}
    local r0 = {x = -math.sin(h), y = 0, z = math.cos(h)}
    local u0 = {x = -math.sin(p) * math.cos(h), y = math.cos(p), z = -math.sin(p) * math.sin(h)}
    local cb, sb = math.cos(b), math.sin(b)
    local r = {x = r0.x * cb - u0.x * sb, y = r0.y * cb - u0.y * sb, z = r0.z * cb - u0.z * sb}
    local u = {x = u0.x * cb + r0.x * sb, y = u0.y * cb + r0.y * sb, z = u0.z * cb + r0.z * sb}
    return f, u, r
end

local function body_to_world(me, f, u, r, v)
    local p = me.Position
    return {x = p.x + f.x * v[1] + u.x * v[2] + r.x * v[3],
            y = p.y + f.y * v[1] + u.y * v[2] + r.y * v[3],
            z = p.z + f.z * v[1] + u.z * v[2] + r.z * v[3]}
end

local function norm(v)
    local m = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    return {x = v.x / m, y = v.y / m, z = v.z / m}
end
local function cross(a, b)
    return {x = a.y * b.z - a.z * b.y, y = a.z * b.x - a.x * b.z, z = a.x * b.y - a.y * b.x}
end

local function place_camera(me, spec)
    local f, u, r = axes(me)
    local cam = body_to_world(me, f, u, r, spec[2])
    local aim = body_to_world(me, f, u, r, spec[3])
    local look = norm({x = aim.x - cam.x, y = aim.y - cam.y, z = aim.z - cam.z})
    local right = norm(cross(look, u))
    local up = cross(right, look)
    Export.LoSetCameraPosition({x = look, y = up, z = right, p = cam})
end

local function request_shot(name)
    waitingFile = logs .. 'F117_vortex_shot.req'
    local f = io.open(waitingFile, 'w'); f:write(name); f:close()
    if Actions and Actions.iCommandScreenShot then DCS.dispatchDigitalAction(Actions.iCommandScreenShot) end
end

local function shot_taken()
    local f = io.open(waitingFile, 'r')
    if f then f:close(); return false end
    return true
end

local function args()
    return Export.LoGetAircraftDrawArgumentValue(26) or -1, Export.LoGetAircraftDrawArgumentValue(904) or -1,
           Export.LoGetAircraftDrawArgumentValue(905) or -1
end

function hook.onSimulationFrame()
    if finished then return end
    if DCS.getPause() then DCS.setPause(false) end
    local now = DCS.getModelTime()
    local me = Export.LoGetSelfData()
    if not startTime then
        if now < 3 or not me then return end
        startTime = now
        handle = io.open(logs .. 'F117_vortex_shots.csv', 'w')
        handle:write('t,state,arg26_any,arg904_left,arg905_right,alt,tas\n')
        local ok, Input = pcall(require, 'Input')
        if ok and Input and Input.getEnvTable then Actions = Input.getEnvTable().Actions end
        if Actions and Actions.iCommandViewFree then Export.LoSetCommand(Actions.iCommandViewFree) end
        stateTime = now
        state = 0
    end
    if not me then return finish('aircraft lost') end
    local t = now - startTime
    if t > 400 then return finish('timed out') end

    -- Level flight: hold height, wings level and speed.
    local tas = Export.LoGetTrueAirSpeed() or 0
    local vy = (Export.LoGetVectorVelocity() or {y = 0}).y
    local climb = clamp((ALT - me.LatLongAlt.Alt) * 0.08, -15, 15)
    if not REPLAY then
        Export.LoSetCommand(2001, clamp(0.02 * (climb - vy) - 0.6 * me.Pitch, -0.4, 0.4))
        Export.LoSetCommand(2002, clamp(1.5 * (0 - me.Bank), -0.5, 0.5))
        Export.LoSetCommand(2003, 0)
        Export.LoSetCommand(2004, clamp(0.08 * (tas - SPEED), -1, 1))
    end

    if state == 0 then
        -- Settle the flight before the first state; the bays are closed.
        if now - stateTime > 8 then
            state, shot, stateTime = 1, 1, now
            if not REPLAY then for _, id in ipairs(STATES[1][2]) do Export.LoSetCommand(id) end end
        end
        return
    end
    local current = STATES[state]
    place_camera(me, SHOTS[shot])
    if not waitingFile then
        if now - stateTime > SETTLE and now - shotTime > 0.6 then
            local a26, a904, a905 = args()
            request_shot(current[1] .. '_' .. SHOTS[shot][1])
            handle:write(string.format('%.2f,%s,%.3f,%.3f,%.3f,%.0f,%.1f\n', t, current[1], a26, a904, a905, me.LatLongAlt.Alt, tas))
            log.write('F117BAYS', log.INFO, string.format('shot %s_%s any %.3f left %.3f right %.3f', current[1], SHOTS[shot][1], a26, a904, a905))
        end
    elseif shot_taken() then
        waitingFile = nil
        shotTime = now
        shot = shot + 1
        if shot > #SHOTS then
            state, shot, stateTime = state + 1, 1, now
            if state > #STATES then return finish('done') end
            if not REPLAY then for _, id in ipairs(STATES[state][2]) do Export.LoSetCommand(id) end end
        end
    end
end
DCS.setUserCallbacks(hook)
"""


def build_mission(target, clsid=GBU_27, right=None):
    miz = Miz.load(base.TEMPLATE)
    found = False

    def keep(group):
        nonlocal found
        unit = group['units'][1]
        if unit['skill'] != 'Player' or found:
            return False
        found = True
        unit['payload']['pylons'] = miz.table({1: {'CLSID': clsid}, 2: {'CLSID': right or clsid}})
        unit['payload']['fuel'] = 3000
        unit['x'], unit['y'], unit['alt'], unit['alt_type'] = base.START_X, base.START_Z, base.ALT, 'BARO'
        unit['heading'], unit['psi'], unit['speed'] = base.HEADING, -base.HEADING, base.SPEED
        points = miz.table()
        for i, distance in enumerate((0, 150000)):
            points[i + 1] = miz.table({
                'x': base.START_X + distance * math.cos(base.HEADING), 'y': base.START_Z + distance * math.sin(base.HEADING),
                'alt': base.ALT, 'alt_type': 'BARO', 'speed': base.SPEED, 'type': 'Turning Point',
                'action': 'Turning Point', 'ETA': 0, 'ETA_locked': i == 0, 'speed_locked': True,
                'formation_template': '', 'task': {'id': 'ComboTask', 'params': {'tasks': {}}}})
        group['route']['points'] = points
        group['x'], group['y'] = base.START_X, base.START_Z
        return True

    miz.remove_groups(keep)
    weather = miz.mission['weather']
    for level in ('atGround', 'at2000', 'at8000'):
        weather['wind'][level]['speed'] = 0
    weather['groundTurbulence'] = 0
    miz.mission['start_time'] = 12 * 3600
    trig = miz.mission['trig']
    trig['conditions'] = miz.table({1: 'return(true)'})
    trig['actions'] = miz.table({1: 'a_do_script(' + lua_string("env.info('F117BAYS mission ready')") + ');'})
    trig['funcStartup'] = miz.table({1: 'if mission.trig.conditions[1]() then mission.trig.actions[1]() end'})
    trig['flag'] = miz.table({1: True})
    miz.save(target)


def acknowledge_shot(path):
    # The hook briefly opens this file each frame while checking acknowledgement.
    for attempt in range(100):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == 99:
                raise
            time.sleep(0.01)


def run(mission, replay=False):
    if 'DCS.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout:
        raise SystemExit('Close DCS first.')
    request, done, flight = LOGS / 'F117_vortex_shot.req', LOGS / 'F117_vortex_shots.done', LOGS / 'F117_vortex_shots.csv'
    for old in (request, done, flight):
        old.unlink(missing_ok=True)
    hook = HOOK.replace('__SPEED__', str(base.SPEED)).replace('__ALT__', str(base.ALT)) \
               .replace('__STATES__', STATES).replace('__SHOTS__', SHOTS).replace('__REPLAY__', 'true' if replay else 'false')
    HOOK_PATH.write_text(hook, encoding='utf-8')
    process = subprocess.Popen([str(base.DCS_EXE), '--track' if replay else '--mission', str(mission)])
    base.RESULTS = RESULTS
    before = base.screenshots()
    try:
        deadline = time.time() + 600
        while not done.exists():
            if time.time() > deadline:
                print('DCS did not finish in 10 minutes')
                break
            if process.poll() is not None:
                print('DCS closed early')
                break
            if request.exists():
                time.sleep(0.05)
                name = request.read_text().strip()
                path = base.capture(name, before)
                before = base.screenshots()
                print('captured', path.name if path else f'nothing for {name}', flush=True)
                acknowledge_shot(request)
            time.sleep(0.05)
    finally:
        try:
            process.wait(120)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(60)
        HOOK_PATH.unlink(missing_ok=True)
        acknowledge_shot(request)
    if flight.exists():
        (RESULTS / 'bays.csv').write_bytes(flight.read_bytes())
        expected = {'closed': (0, 0, 0), 'both_open': (1, 1, 1), 'left_closed': (1, 0, 1),
                    'both_open_again': (1, 1, 1), 'right_closed': (1, 1, 0), 'both_closed': (0, 0, 0)}
        rows = list(csv.reader(line for line in flight.read_text().splitlines() if not line.startswith('#')))
        latest = {row[1]: tuple(float(value) for value in row[2:5]) for row in rows[1:]}
        assert latest == expected, f'bay state mismatch: {latest}'
    log = LOGS / 'dcs.log'
    if log.exists():
        lines = [line for line in log.read_text(encoding='utf-8', errors='replace').splitlines()
                 if 'F117BAYS' in line or 'ERROR   Lua' in line]
        (RESULTS / 'run.log').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('\n'.join(lines))
    print(done.read_text() if done.exists() else 'unfinished')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--build-only', action='store_true', help='write the mission without starting DCS')
    parser.add_argument('--store', choices=sorted(STORES), default='gbu-27', help='store on both pylons')
    parser.add_argument('--right', choices=sorted(STORES), help='a different store on the right pylon')
    parser.add_argument('--replay', type=Path, help='observe a recorded bay test without sending flight or bay commands')
    args = parser.parse_args()
    global RESULTS
    if args.replay:
        RESULTS = HERE / 'results/bays_replay'
        RESULTS.mkdir(parents=True, exist_ok=True)
        run(args.replay.resolve(), replay=True)
        return
    if args.store != 'gbu-27' or args.right:
        RESULTS = HERE / ('results/bays_' + args.store + (f'_{args.right}' if args.right else ''))
    RESULTS.mkdir(parents=True, exist_ok=True)
    mission = RESULTS / 'bay_shots.miz'
    build_mission(mission, STORES[args.store], STORES[args.right] if args.right else None)
    if not args.build_only:
        run(mission)


if __name__ == '__main__':
    main()
