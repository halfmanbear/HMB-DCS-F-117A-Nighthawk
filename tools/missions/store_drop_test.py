"""Drop each F-117 store in DCS and report whether it released and where it landed.

    python tools/missions/store_drop_test.py              # every store
    python tools/missions/store_drop_test.py MK-82 GBU-10 # some stores
    python tools/missions/store_drop_test.py --report     # rewrite the report from the last runs

For each store the script builds a mission from the Caucasus free flight quick start: one
F-117 in the air over the flat ground east of Mozdok, carrying the store on both stations,
with no wind. A temporary hook in Saved Games/DCS/Scripts/Hooks then flies the aircraft
the way a pilot would:
 1. Unpauses and holds height, speed and heading.
 2. Turns on IRADS and Master Arm.
 3. Slews the IRADS and designates until the lock point is the store's test distance ahead.
 4. Puts a target truck on the lock point and steers at it.
 5. Arms the laser for laser-guided stores.
 6. Holds the pickle until the cockpit reports a release.
A mission script logs where the weapon hits. Each store's run is written to
tools/missions/results/<store>.csv and the summary to tools/missions/results/store_drop.md.
Close DCS first. Each store takes about three minutes.
"""
import argparse
import csv
import math
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from missions.miz import Miz  # noqa: E402

MOD = HERE.parents[1]
TEMPLATE = MOD / 'Missions/QuickStart/F-117A-NightHawk - Caucasus - Free Flight.miz'
RESULTS = HERE / 'results'
DCS_EXE = Path(r'E:\Eagle Dynamics\DCS World\bin-mt\DCS.exe')
SAVED_GAMES = MOD.parents[2]
# DCS writes dcs.log under the Windows user's Saved Games, which is not where this install lives.
LOG_DIRS = [SAVED_GAMES / 'Logs', Path.home() / 'Saved Games/DCS/Logs']

# Flat steppe east of Mozdok, flying east. DCS x is north and z is east.
START_X, START_Z, HEADING = -83000.0, 805000.0, math.pi / 2

# name, CLSID, start height (m above sea level), speed (m/s true), designation distance (m), laser
STORES = [
    ('GBU-31V1', '{GBU-31}', 4500, 230, 9000, False),
    ('GBU-31V3', '{GBU-31V3B}', 4500, 230, 9000, False),
    ('GBU-32', '{GBU_32_V_2B}', 4500, 230, 9000, False),
    ('GBU-12', '{DB769D48-67D7-42ED-A2BE-108D566C8B1E}', 4500, 230, 9000, True),
    ('GBU-27', '{EF0A9419-01D6-473B-99A3-BEBDB923B14D}', 4500, 230, 9000, True),
    ('GBU-10', '{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}', 4500, 230, 9000, True),
    ('MK-82', '{BCE4E030-38E9-423E-98ED-24BE3DA87C32}', 4500, 230, 9000, False),
    ('MK-84', '{AB8B8299-F1CC-4359-89B5-2172E0CF4A5A}', 4500, 230, 9000, False),
    ('CBU-105', '{CBU_105}', 4500, 230, 9000, False),
    ('AGM-154A', '{AGM-154A}', 6000, 240, 22000, False),
    ('AGM-154B', '{AGM-154B}', 6000, 240, 22000, False),
    ('AGM-154C', '{9BCC2A2B-5708-4860-B1F1-053A18442067}', 6000, 240, 22000, False),
    ('AGM-65D', '{444BA8AE-82A7-4345-842E-76154EFCCA47}', 2500, 220, 8000, False),
    ('AGM-65E', '{F16A4DE0-116C-4A71-97F0-2CF85B0313EF}', 2500, 220, 8000, True),
]

# Runs inside the mission. Logs each shot and its impact point to dcs.log.
MISSION_SCRIPT = r"""
local tracked = {}
local handler = {}
function handler:onEvent(e)
    if e.id == world.event.S_EVENT_SHOT and e.weapon then
        tracked[#tracked + 1] = {w = e.weapon, name = e.weapon:getTypeName(), p = e.weapon:getPoint(), v = e.weapon:getVelocity()}
        env.info('F117TEST SHOT ' .. e.weapon:getTypeName())
    elseif e.id == world.event.S_EVENT_DEAD and e.initiator and e.initiator.getName then
        local ok, name = pcall(function() return e.initiator:getName() end)
        if ok then env.info('F117TEST DEAD ' .. tostring(name)) end
    end
end
world.addEventHandler(handler)
local function poll()
    for i = #tracked, 1, -1 do
        local t = tracked[i]
        if t.w:isExist() then
            t.p, t.v = t.w:getPoint(), t.w:getVelocity()
        else
            -- Carry the last sample down to the ground along its velocity.
            local ground = land.getHeight({x = t.p.x, y = t.p.z})
            local dt = (t.v.y < -1) and math.min(1, (t.p.y - ground) / -t.v.y) or 0
            env.info(string.format('F117TEST IMPACT %s %.1f %.1f %.1f', t.name, t.p.x + t.v.x * dt, ground, t.p.z + t.v.z * dt))
            table.remove(tracked, i)
        end
    end
    return timer.getTime() + 0.02
end
timer.scheduleFunction(poll, nil, timer.getTime() + 1)
env.info('F117TEST READY')
"""

HOOK = r"""-- Temporary hook written by tools/missions/store_drop_test.py. Safe to delete.
local DESIRED, ALT, SPEED, LASER, WAIT = {DESIRED}, {ALT}, {SPEED}, {LASER}, {WAIT}
local path = lfs.writedir() .. 'Logs\\F117_store_drop.csv'
local hook = {{}}
local handle, startTime, finished, phase, phaseTime, lock, heading, released, releaseTime
local slewUntil, lastStatus, designated = 0, -1, false
local tries = 0

local function finish(why)
    if handle then handle:write('# ' .. why .. '\n'); handle:close() end
    finished = true
    local done = io.open(path .. '.done', 'w'); done:write(why); done:close()
    DCS.exitProcess() -- a clean exit flushes dcs.log
end

local function params()
    local ok, text = pcall(net.dostring_in, 'export', 'return list_cockpit_params()')
    local result = {{}}
    if ok and text then
        for name, value in string.gmatch(text, '([%w_]+):([^\n]*)') do result[name] = tonumber(value) or value end
    end
    return result
end

local function command(id, value)
    if value then Export.LoSetCommand(id, value) else Export.LoSetCommand(id) end
end

local function in_mission(code)
    pcall(net.dostring_in, 'mission', 'a_do_script(' .. string.format('%q', code) .. ')')
end

local function fly(me, t)
    -- Hold height with pitch, heading with bank, speed with throttle.
    local vz = (Export.LoGetVectorVelocity() or {{y = 0}}).y
    local climb = math.max(-15, math.min(15, (ALT - me.LatLongAlt.Alt) * 0.08))
    Export.LoSetCommand(2001, math.max(-0.4, math.min(0.4, 0.02 * (climb - vz) - 0.6 * me.Pitch)))
    local err = heading - me.Heading
    while err > math.pi do err = err - 2 * math.pi end
    while err < -math.pi do err = err + 2 * math.pi end
    local bankWanted = math.max(-0.5, math.min(0.5, 2.5 * err))
    Export.LoSetCommand(2002, math.max(-0.5, math.min(0.5, 1.5 * (bankWanted - me.Bank))))
    Export.LoSetCommand(2003, 0)
    local tas = Export.LoGetTrueAirSpeed() or SPEED
    Export.LoSetCommand(2004, math.max(-1, math.min(1, 0.08 * (tas - SPEED))))
end

function hook.onSimulationFrame()
    if finished then return end
    if DCS.getPause() then DCS.setPause(false) end
    local now = DCS.getModelTime()
    local me = Export.LoGetSelfData()
    if not startTime then
        if now < 3 or not me then return end
        startTime, heading = now, me.Heading
        handle = io.open(path, 'w')
        handle:write('t,phase,x,alt,z,tas,status,profile,lock_valid,lock_x,lock_y,lock_z,zone,min,max,error,sequence\n')
        command(10122)     -- Master Arm (IRADS is already on at start)
        phase, phaseTime = 'warm', now
    end
    if not me then return finish('aircraft lost') end
    local t = now - startTime
    if t > 360 and phase ~= 'attack' then return finish('timed out in phase ' .. phase .. ', last status ' .. lastStatus) end
    fly(me, t)
    local p = params()
    local status = p.F117_RELEASE_STATUS or -1
    local valid = (p.F117_IRADS_LOCK_VALID or 0) > 0.5
    if phase == 'warm' and now - phaseTime > 5 then
        phase, phaseTime = 'aim', now
    elseif phase == 'aim' and now >= slewUntil then
        Export.LoSetCommand(10120, 0)
        if not valid then
            -- The sight starts above the horizon. Designate; if no ground point comes
            -- back, look further down and try again.
            if not designated then
                command(10114, 1); command(10114, 0); designated, phaseTime = true, now
            elseif now - phaseTime > 2 then
                Export.LoSetCommand(10120, -1)
                slewUntil, designated = now + 0.5, false
            end
        else
            designated = false
            local dx, dz = p.F117_IRADS_LOCK_X - me.Position.x, p.F117_IRADS_LOCK_Z - me.Position.z
            local along = dx * math.cos(me.Heading) + dz * math.sin(me.Heading)
            tries = tries + 1
            if math.abs(along - DESIRED) < 0.12 * DESIRED or tries > 40 then
                lock = {{x = p.F117_IRADS_LOCK_X, y = p.F117_IRADS_LOCK_Y, z = p.F117_IRADS_LOCK_Z}}
                in_mission(string.format([[coalition.addGroup(country.id.RUSSIA, Group.Category.GROUND, {{name = 'F117TGT',
                    task = 'Ground Nothing', units = {{{{type = 'Ural-375', name = 'F117TGT1', x = %.1f, y = %.1f, heading = 0, skill = 'Average'}}}}}})
                    env.info('F117TEST LOCK %.1f %.1f %.1f')]], lock.x, lock.z, lock.x, lock.y, lock.z))
                if LASER then command(10118) end
                phase, phaseTime = 'attack', now
            else
                -- Too short: look farther (up). Too long: look nearer (down).
                command(10117)
                designated = false
                local up = along < DESIRED
                Export.LoSetCommand(10120, up and 1 or -1)
                slewUntil = now + math.min(0.6, 0.05 + 0.4 * math.abs(along - DESIRED) / DESIRED)
                phaseTime = now
            end
        end
    elseif phase == 'attack' then
        local dx, dz = lock.x - me.Position.x, lock.z - me.Position.z
        heading = math.atan2(dz, dx)
        if not released then command(350) end -- pickle held
        if (p.F117_RELEASE_SEQUENCE or 0) > 0 and not released then
            released, releaseTime = true, now
            command(351)
        end
        if released and now - releaseTime > WAIT then return finish('released') end
        if not released and now - phaseTime > 240 then command(351); return finish('no release, last status ' .. status) end
    end
    if status ~= lastStatus or math.floor(t * 2) ~= math.floor((t - 0.02) * 2) then
        lastStatus = status
        handle:write(string.format('%.2f,%s,%.1f,%.1f,%.1f,%.1f,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n', t, phase,
            me.Position.x, me.LatLongAlt.Alt, me.Position.z, Export.LoGetTrueAirSpeed() or 0, status,
            tostring(p.F117_CCRP_PROFILE), tostring(p.F117_IRADS_LOCK_VALID), tostring(p.F117_IRADS_LOCK_X),
            tostring(p.F117_IRADS_LOCK_Y), tostring(p.F117_IRADS_LOCK_Z), tostring(p.F117_RELEASE_CUE_IN_ZONE),
            tostring(p.F117_RELEASE_MIN_RANGE), tostring(p.F117_RELEASE_MAX_RANGE), tostring(p.F117_RELEASE_CUE_ERROR),
            tostring(p.F117_RELEASE_SEQUENCE)))
    end
end
DCS.setUserCallbacks(hook)
"""


def build_mission(store, target):
    name, clsid, alt, speed, _, _ = store
    miz = Miz.load(TEMPLATE)
    found = False

    def keep(group):
        nonlocal found
        unit = group['units'][1]
        if unit['skill'] != 'Player' or found:
            return False
        found = True
        unit['payload']['pylons'] = miz.table({1: {'CLSID': clsid}, 2: {'CLSID': clsid}})
        unit['payload']['fuel'] = 4000
        unit['x'], unit['y'], unit['alt'], unit['alt_type'] = START_X, START_Z, alt, 'BARO'
        unit['heading'], unit['psi'], unit['speed'] = HEADING, -HEADING, speed
        points = miz.table()
        for i, distance in enumerate((0, 150000)):
            points[i + 1] = miz.table({
                'x': START_X + distance * math.cos(HEADING), 'y': START_Z + distance * math.sin(HEADING),
                'alt': alt, 'alt_type': 'BARO', 'speed': speed, 'type': 'Turning Point', 'action': 'Turning Point',
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
    trig = miz.mission['trig']
    trig['conditions'] = miz.table({1: 'return(true)'})
    trig['actions'] = miz.table({1: 'a_do_script(' + lua_string(MISSION_SCRIPT) + ');'})
    trig['funcStartup'] = miz.table({1: 'if mission.trig.conditions[1]() then mission.trig.actions[1]() end'})
    trig['flag'] = miz.table({1: True})  # DCS only runs a start trigger whose flag is set
    miz.mission['trigrules'] = miz.table({1: {
        'rules': {}, 'eventlist': '', 'predicate': 'triggerStart', 'comment': 'F117 store drop test',
        'actions': {1: {'predicate': 'a_do_script', 'text': MISSION_SCRIPT, 'KeyDict_text': ''}}}})
    miz.save(target)


def lua_string(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def run_dcs(store, mission):
    if 'DCS.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout:
        raise SystemExit('Close DCS first.')
    output = SAVED_GAMES / 'Logs/F117_store_drop.csv'
    done = Path(str(output) + '.done')
    hook_path = SAVED_GAMES / 'Scripts/Hooks/zz_f117_store_drop.lua'
    for old in (output, done):
        old.unlink(missing_ok=True)
    _, _, alt, speed, desired, laser = store
    hook_path.write_text(HOOK.format(DESIRED=desired, ALT=alt, SPEED=speed, LASER='true' if laser else 'false',
                                     WAIT=160 if store[0].startswith('AGM-154') else 70),
                         encoding='utf-8')
    process = subprocess.Popen([str(DCS_EXE), '--mission', str(mission)])
    try:
        deadline = time.time() + 600
        while not done.exists():
            if time.time() > deadline:
                return 'DCS did not finish in 10 minutes'
            if process.poll() is not None:
                log = SAVED_GAMES / 'Logs/dcs.log'
                if log.exists():  # keep the tail to see why
                    tail = log.read_text(encoding='utf-8', errors='replace').splitlines()[-80:]
                    (RESULTS / f'{store[0]}.closed.log').write_text('\n'.join(tail) + '\n', encoding='utf-8')
                return 'DCS closed early'
            time.sleep(2)
    finally:
        try:
            process.wait(120)  # the hook asks DCS to exit, which flushes dcs.log
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(60)
        hook_path.unlink(missing_ok=True)
    name = store[0]
    (RESULTS / f'{name}.csv').write_bytes(output.read_bytes())
    for folder in LOG_DIRS:
        log = folder / 'dcs.log'
        if log.exists() and log.stat().st_mtime > time.time() - 900:
            lines = [line for line in log.read_text(encoding='utf-8', errors='replace').splitlines()
                     if any(w in line for w in ('F117TEST', 'DELIVERY', 'F117_WEAPONS', 'ERROR   Scripting', 'SCRIPTING'))
                     and 'BHD' not in line and 'Black Hawk' not in line]
            (RESULTS / f'{name}.log').write_text('\n'.join(lines) + '\n', encoding='utf-8')
            break
    return done.read_text()


def summarise(name):
    """One report row from a store's saved CSV and log lines."""
    csv_path, log_path = RESULTS / f'{name}.csv', RESULTS / f'{name}.log'
    if not csv_path.exists():
        return f'| {name} | not run | | | |'
    rows = [r for r in csv.reader(line for line in csv_path.read_text().splitlines() if not line.startswith('#'))][1:]
    outcome = [line[2:] for line in csv_path.read_text().splitlines() if line.startswith('#')]
    log = log_path.read_text(encoding='utf-8') if log_path.exists() else ''
    lock = re.search(r'F117TEST LOCK (\S+) (\S+) (\S+)', log)
    impacts = re.findall(r'F117TEST IMPACT (\S+) (\S+) (\S+) (\S+)', log)
    killed = 'F117TGT1' in log and 'F117TEST DEAD F117TGT1' in log
    statuses = sorted({r[6] for r in rows if len(r) > 6})
    miss = ''
    if lock and impacts:
        lx, lz = float(lock.group(1)), float(lock.group(3))
        _, ix, _, iz = impacts[0]
        miss = f'{math.hypot(float(ix) - lx, float(iz) - lz):.0f}'
    return (f"| {name} | {outcome[0] if outcome else 'unfinished'} | {impacts[0][0] if impacts else 'none'} | {miss} | "
            f"{'yes' if killed else 'no'} | {' '.join(statuses)} |")


def report():
    lines = ['| Store | Outcome | Weapon seen | Miss from lock point, m | Target killed | Release statuses seen |',
             '|---|---|---|---:|---|---|'] + [summarise(store[0]) for store in STORES]
    (RESULTS / 'store_drop.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('stores', nargs='*', help='store names (default: all)')
    parser.add_argument('--report', action='store_true', help='only rewrite the report from saved results')
    parser.add_argument('--build-only', action='store_true', help='write the missions without starting DCS')
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)
    if not args.report:
        chosen = [s for s in STORES if not args.stores or s[0] in args.stores]
        unknown = set(args.stores) - {s[0] for s in STORES}
        if unknown:
            raise SystemExit(f'Unknown stores: {sorted(unknown)}')
        for store in chosen:
            mission = RESULTS / f'{store[0]}.miz'
            build_mission(store, mission)
            if not args.build_only:
                print(store[0], run_dcs(store, mission), flush=True)
    report()


if __name__ == '__main__':
    main()
