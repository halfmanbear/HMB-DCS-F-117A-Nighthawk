"""Fly the F-117 through steady AoA steps in DCS and screenshot the leading-edge vortex.

    python tools/missions/vortex_shots.py            # fly and capture
    python tools/missions/vortex_shots.py --build-only
    python tools/missions/vortex_shots.py --power-map  # AoA sweep at three speeds, top view only

Builds a mission from the Caucasus free flight quick start: a clean F-117 at 600 m over
the Black Sea at noon with no wind. A temporary hook in Saved Games/DCS/Scripts/Hooks:
 1. Unpauses, goes to full throttle and switches to the free camera.
 2. For each step (1 g cruise, 6 deg, 9 deg, full aft stick) accelerates to the entry
    speed, rolls into a level turn and holds the AoA with the stick.
 3. Once the AoA is steady, places the camera at fixed points around the aircraft and
    asks this script to capture the screen at each.
Shots and a flight log go to tools/missions/results/vortex/. Close DCS first. About
three minutes.
"""
import argparse
import math
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from missions.miz import Miz  # noqa: E402
from missions.store_drop_test import lua_string  # noqa: E402

MOD = HERE.parents[1]
TEMPLATE = MOD / 'Missions/QuickStart/F-117A-NightHawk - Caucasus - Free Flight.miz'
RESULTS = HERE / 'results/vortex'
STEPS = "{{'cruise', nil}, {'aoa06', 6}, {'aoa09', 9}, {'aoamax', 99}, {'fastmax', 99, 260}}"
SHOTS = """{
    {'top',   {-4, 22, -3},  {-1, 0, 0}},   -- plan view from above, like the in-game reference
    {'side',  {3, 9, -17},   {-1.5, 0, 0}}, -- above the left wing, like the airshow photo
    {'rear',  {-20, 7, 6},   {0, 0, 0}},    -- behind and above the right wing
}"""
# Power map: one top shot per AoA step at each entry speed.
MAP_STEPS = '{' + ', '.join(
    f"{{'v{v}_a{aoa:02d}', {aoa}, {v}}}" for v in (150, 200, 250) for aoa in (4, 5, 6, 7, 8, 9, 10, 99)) + '}'
MAP_SHOTS = "{{'top', {-4, 22, -3}, {-1, 0, 0}}}"
DCS_EXE = Path(r'E:\Eagle Dynamics\DCS World\bin-mt\DCS.exe')
SAVED_GAMES = MOD.parents[2]
LOGS = SAVED_GAMES / 'Logs'
HOOK_PATH = SAVED_GAMES / 'Scripts/Hooks/zz_f117_vortex_shots.lua'

# Open sea south-west of Sochi, flying west. DCS x is north and z is east.
START_X, START_Z, HEADING, ALT, SPEED = -60000.0, 200000.0, 3 * math.pi / 2, 600, 190

HOOK = r"""-- Temporary hook written by tools/missions/vortex_shots.py. Safe to delete.
local logs = lfs.writedir() .. 'Logs\\'
local SPEED, ALT = {SPEED}, {ALT}
-- name, target AoA (deg; nil = 1 g cruise, 99 = full aft stick), entry speed (m/s; nil = SPEED)
local STEPS = {STEPS}
-- Camera points in the body frame (forward, up, right), metres, looking at the target point.
local SHOTS = {SHOTS}
local hook = {{}}
local handle, startTime, finished
local step, phase, phaseTime, steadySince = 1, 'accelerate', 0, nil
local shot, shotTime, waitingFile
local integ, Actions = 0, nil

local function finish(why)
    log.write('F117VORTEX', log.INFO, 'finish ' .. why)
    if handle then handle:write('# ' .. why .. '\n'); handle:close() end
    finished = true
    local done = io.open(logs .. 'F117_vortex_shots.done', 'w'); done:write(why); done:close()
    DCS.exitProcess()
end

local function clamp(v, lo, hi) return math.max(lo, math.min(hi, v)) end

-- Body axes in world coordinates from heading, pitch and bank.
local function axes(me)
    local h, p, b = me.Heading, me.Pitch, me.Bank
    local f = {{x = math.cos(p) * math.cos(h), y = math.sin(p), z = math.cos(p) * math.sin(h)}}
    local r0 = {{x = -math.sin(h), y = 0, z = math.cos(h)}}
    local u0 = {{x = -math.sin(p) * math.cos(h), y = math.cos(p), z = -math.sin(p) * math.sin(h)}}
    local cb, sb = math.cos(b), math.sin(b)
    local r = {{x = r0.x * cb - u0.x * sb, y = r0.y * cb - u0.y * sb, z = r0.z * cb - u0.z * sb}}
    local u = {{x = u0.x * cb + r0.x * sb, y = u0.y * cb + r0.y * sb, z = u0.z * cb + r0.z * sb}}
    return f, u, r
end

local function body_to_world(me, f, u, r, v)
    local p = me.Position
    return {{x = p.x + f.x * v[1] + u.x * v[2] + r.x * v[3],
             y = p.y + f.y * v[1] + u.y * v[2] + r.y * v[3],
             z = p.z + f.z * v[1] + u.z * v[2] + r.z * v[3]}}
end

local function norm(v)
    local m = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    return {{x = v.x / m, y = v.y / m, z = v.z / m}}
end
local function cross(a, b)
    return {{x = a.y * b.z - a.z * b.y, y = a.z * b.x - a.x * b.z, z = a.x * b.y - a.y * b.x}}
end

local function place_camera(me, spec)
    local f, u, r = axes(me)
    local cam = body_to_world(me, f, u, r, spec[2])
    local aim = body_to_world(me, f, u, r, spec[3])
    local look = norm({{x = aim.x - cam.x, y = aim.y - cam.y, z = aim.z - cam.z}})
    local right = norm(cross(look, u))
    local up = cross(right, look)
    Export.LoSetCameraPosition({{x = look, y = up, z = right, p = cam}})
end

local function request_shot(name)
    waitingFile = logs .. 'F117_vortex_shot.req'
    local f = io.open(waitingFile, 'w'); f:write(name); f:close()
    -- Screenshot is a UI-layer action: LoSetCommand ignores it, dispatchDigitalAction runs it.
    if Actions and Actions.iCommandScreenShot then DCS.dispatchDigitalAction(Actions.iCommandScreenShot) end
end

local function shot_taken()
    local f = io.open(waitingFile, 'r')
    if f then f:close(); return false end
    return true
end

function hook.onSimulationFrame()
    if finished then return end
    if DCS.getPause() then DCS.setPause(false) end
    local now = DCS.getModelTime()
    local me = Export.LoGetSelfData()
    if not startTime then
        if now < 3 or not me then return end
        startTime, phaseTime = now, now
        handle = io.open(logs .. 'F117_vortex_shots.csv', 'w')
        handle:write('t,step,phase,alt,tas,aoa,nz,bank,pitch_cmd,roll_cmd\n')
        local ok, Input = pcall(require, 'Input')
        if ok and Input and Input.getEnvTable then Actions = Input.getEnvTable().Actions end
        log.write('F117VORTEX', log.INFO, 'actions ' .. tostring(Actions ~= nil) .. ' free ' ..
            tostring(Actions and Actions.iCommandViewFree) .. ' shot ' .. tostring(Actions and Actions.iCommandScreenShot))
    end
    if not me then return finish('aircraft lost') end
    local t = now - startTime
    if t > 1300 then return finish('timed out at step ' .. step .. ' ' .. phase) end

    local tas = Export.LoGetTrueAirSpeed() or 0
    local aoa = Export.LoGetAngleOfAttack() or 0 -- degrees, despite Export.lua
    local nz = (Export.LoGetAccelerationUnits() or {{y = 1}}).y
    local vy = (Export.LoGetVectorVelocity() or {{y = 0}}).y
    local name, target = STEPS[step][1], STEPS[step][2]
    local entry = STEPS[step][3] or SPEED
    local pitchCmd, bankWanted

    if phase == 'accelerate' then
        -- Wings level, hold height, full throttle until at entry speed.
        bankWanted = 0
        -- Dive back down to the start height; the descent also buys the speed back.
        local climb = clamp((ALT - me.LatLongAlt.Alt) * 0.08, -30, 15)
        pitchCmd = clamp(0.02 * (climb - vy) - 0.6 * me.Pitch, -0.4, 0.4)
        integ = 0
        if math.abs(tas - entry) < 6 and math.abs(ALT - me.LatLongAlt.Alt) < 400 and now - phaseTime > 4 then
            phase, phaseTime, steadySince = (target == nil) and 'hold' or 'roll', now, nil
        end
    elseif phase == 'roll' then
        -- Bank first so the pull turns the aircraft instead of climbing.
        bankWanted = -1.2
        pitchCmd = clamp(0.02 * (0 - vy), -0.3, 0.3)
        if math.abs(me.Bank - bankWanted) < 0.12 then phase, phaseTime = 'hold', now end
    else
        if target == nil then
            bankWanted = 0
            local climb = clamp((ALT - me.LatLongAlt.Alt) * 0.08, -15, 15)
            pitchCmd = clamp(0.02 * (climb - vy) - 0.6 * me.Pitch, -0.4, 0.4)
        elseif target >= 90 then
            pitchCmd = 1
        else
            local err = target - aoa
            integ = clamp(integ + err * 0.04 * (1 / 60), -0.6, 0.6)
            pitchCmd = clamp(0.06 * err + integ, -1, 1)
        end
        if target ~= nil then
            -- Level turn to the left: bank for the load factor, plus more bank if climbing.
            bankWanted = -clamp(math.acos(clamp(1 / math.max(nz, 1.01), 0, 1)) + 0.02 * vy, 0.9, 1.45)
        end
        local steady = (target == nil) or (target >= 90 and now - phaseTime > 2.5) or
                       (target < 90 and math.abs(target - aoa) < 0.6)
        if phase == 'hold' then
            if steady then steadySince = steadySince or now else steadySince = nil end
            if steadySince and now - steadySince > 1.0 then
                phase, shot, shotTime = 'shoot', 1, now
                if Actions and Actions.iCommandViewFree then Export.LoSetCommand(Actions.iCommandViewFree) end
            elseif now - phaseTime > 25 then
                log.write('F117VORTEX', log.INFO, name .. ' never steady, aoa ' .. aoa)
                phase, shot, shotTime = 'shoot', 1, now
            end
        elseif phase == 'shoot' then
            place_camera(me, SHOTS[shot])
            if not waitingFile and now - shotTime > 0.6 then
                request_shot(name .. '_' .. SHOTS[shot][1])
                log.write('F117VORTEX', log.INFO, string.format('shot %s_%s aoa %.1f tas %.0f nz %.2f alt %.0f',
                    name, SHOTS[shot][1], aoa, tas, nz, me.LatLongAlt.Alt))
            elseif waitingFile and shot_taken() then
                waitingFile = nil
                shot, shotTime = shot + 1, now
                if shot > #SHOTS then
                    step = step + 1
                    if step > #STEPS then return finish('done') end
                    phase, phaseTime = 'accelerate', now
                    if Actions and Actions.iCommandViewAir then Export.LoSetCommand(Actions.iCommandViewAir) end
                end
            end
        end
    end
    Export.LoSetCommand(2001, pitchCmd)
    local rollCmd = clamp(1.5 * (bankWanted - me.Bank), -0.6, 0.6)
    Export.LoSetCommand(2002, rollCmd)
    Export.LoSetCommand(2003, 0)
    -- Settle on the entry speed (or hold it in the 1 g step); full power in the turns.
    local throttle = -1
    if phase == 'accelerate' then throttle = clamp(0.08 * (tas - entry), -1, 1)
    elseif target == nil then throttle = clamp(0.08 * (tas - SPEED), -1, 1) end
    Export.LoSetCommand(2004, throttle)
    if math.floor(t * 4) ~= math.floor((t - 0.02) * 4) then
        handle:write(string.format('%.2f,%s,%s,%.0f,%.1f,%.2f,%.2f,%.2f,%.3f,%.3f\n',
            t, name, phase, me.LatLongAlt.Alt, tas, aoa, nz, math.deg(me.Bank), pitchCmd, rollCmd))
    end
end
DCS.setUserCallbacks(hook)
"""


def build_mission(target):
    miz = Miz.load(TEMPLATE)
    found = False

    def keep(group):
        nonlocal found
        unit = group['units'][1]
        if unit['skill'] != 'Player' or found:
            return False
        found = True
        unit['payload']['pylons'] = miz.table()
        unit['payload']['fuel'] = 3000
        unit['x'], unit['y'], unit['alt'], unit['alt_type'] = START_X, START_Z, ALT, 'BARO'
        unit['heading'], unit['psi'], unit['speed'] = HEADING, -HEADING, SPEED
        points = miz.table()
        for i, distance in enumerate((0, 150000)):
            points[i + 1] = miz.table({
                'x': START_X + distance * math.cos(HEADING), 'y': START_Z + distance * math.sin(HEADING),
                'alt': ALT, 'alt_type': 'BARO', 'speed': SPEED, 'type': 'Turning Point', 'action': 'Turning Point',
                'ETA': 0, 'ETA_locked': i == 0, 'speed_locked': True, 'formation_template': '',
                'task': {'id': 'ComboTask', 'params': {'tasks': {}}}})
        group['route']['points'] = points
        group['x'], group['y'] = START_X, START_Z
        return True

    miz.remove_groups(keep)
    weather = miz.mission['weather']
    for level in ('atGround', 'at2000', 'at8000'):
        weather['wind'][level]['speed'] = 0
    weather['groundTurbulence'] = 0
    miz.mission['start_time'] = 12 * 3600
    script = "env.info('F117VORTEX mission ready')"
    trig = miz.mission['trig']
    trig['conditions'] = miz.table({1: 'return(true)'})
    trig['actions'] = miz.table({1: 'a_do_script(' + lua_string(script) + ');'})
    trig['funcStartup'] = miz.table({1: 'if mission.trig.conditions[1]() then mission.trig.actions[1]() end'})
    trig['flag'] = miz.table({1: True})
    miz.save(target)


SCREEN_DIRS = [SAVED_GAMES / 'ScreenShots', Path.home() / 'Saved Games/DCS/ScreenShots']


def screenshots():
    return {p for folder in SCREEN_DIRS if folder.exists() for p in folder.iterdir()}


def capture(name, before):
    """Collect the screenshot DCS was asked for; fall back to grabbing the screen."""
    deadline = time.time() + 4
    while time.time() < deadline:
        new = [p for p in screenshots() - before if p.suffix.lower() in ('.png', '.jpg')]
        if new:
            time.sleep(0.5)  # let DCS finish writing
            source = max(new, key=lambda p: p.stat().st_mtime)
            path = RESULTS / f'{name}{source.suffix.lower()}'
            path.write_bytes(source.read_bytes())
            source.unlink()
            return path
        time.sleep(0.1)
    try:
        path = RESULTS / f'{name}.png'
        ImageGrab.grab().save(path)
        return path
    except OSError:
        return None


def run(mission, steps=STEPS, shots=SHOTS):
    if 'DCS.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout:
        raise SystemExit('Close DCS first.')
    request, done, flight = LOGS / 'F117_vortex_shot.req', LOGS / 'F117_vortex_shots.done', LOGS / 'F117_vortex_shots.csv'
    for old in (request, done, flight, RESULTS / 'shots.csv'):
        old.unlink(missing_ok=True)
    HOOK_PATH.write_text(HOOK.format(SPEED=SPEED, ALT=ALT, STEPS=steps, SHOTS=shots), encoding='utf-8')
    process = subprocess.Popen([str(DCS_EXE), '--mission', str(mission)])
    taken = []
    before = screenshots()
    try:
        deadline = time.time() + 1500
        while not done.exists():
            if time.time() > deadline:
                print('DCS did not finish in 25 minutes')
                break
            if process.poll() is not None:
                print('DCS closed early')
                break
            if request.exists():
                time.sleep(0.05)
                name = request.read_text().strip()
                with (RESULTS / 'shots.csv').open('a') as times:
                    times.write(f'{name},{time.time():.3f}\n')
                path = capture(name, before)
                before = screenshots()
                if path:
                    taken.append(path)
                print('captured', path.name if path else f'nothing for {name}', flush=True)
                request.unlink()
            time.sleep(0.05)
    finally:
        try:
            process.wait(120)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(60)
        HOOK_PATH.unlink(missing_ok=True)
        request.unlink(missing_ok=True)
    if flight.exists():
        (RESULTS / 'flight.csv').write_bytes(flight.read_bytes())
    log = LOGS / 'dcs.log'
    if log.exists():
        lines = [line for line in log.read_text(encoding='utf-8', errors='replace').splitlines()
                 if 'F117VORTEX' in line or 'ERROR   Lua' in line]
        (RESULTS / 'run.log').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('\n'.join(lines))
    print(done.read_text() if done.exists() else 'unfinished')
    return taken


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--build-only', action='store_true', help='write the mission without starting DCS')
    parser.add_argument('--power-map', action='store_true',
                        help='sweep AoA at 150, 200 and 250 m/s with top shots only, into results/vortex/power_map')
    args = parser.parse_args()
    global RESULTS
    if args.power_map:
        RESULTS = RESULTS / 'power_map'
    RESULTS.mkdir(parents=True, exist_ok=True)
    mission = RESULTS / 'vortex_shots.miz'
    build_mission(mission)
    if not args.build_only:
        run(mission, MAP_STEPS, MAP_SHOTS) if args.power_map else run(mission)


if __name__ == '__main__':
    main()
