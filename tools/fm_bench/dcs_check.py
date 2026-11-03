#!/usr/bin/env python3
"""Fly one scripted input sequence in DCS and on the bench, then compare the two.

The bench does its own integration, so this is what shows how far its results can be trusted in DCS.
DCS must be closed. It starts by itself, runs for about 2.5 minutes and is closed again.

    python tools/fm_bench/dcs_check.py --mission "E:/Saved Games/DCS/Missions/f117_test.miz"

The mission only supplies a map and a player F-117: this tool makes an air start copy with standard
weather and no other aircraft. Each DCS launch overwrites dcs.log and the EFM's debug logs.
"""
import argparse
import csv
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import efm as efm_module  # noqa: E402
sys.path.insert(0, str(HERE.parent))
from missions.miz import serialize as _lua  # noqa: E402
from scorecard import RESULTS, read_inertia  # noqa: E402
from sim import (CMD_PITCH_AXIS, CMD_ROLL_AXIS, CMD_THROTTLE_AXIS, CMD_YAW_AXIS, DT, FT_TO_M, KT_TO_MPS, LB_TO_KG,  # noqa: E402
                 RAD, Sim, isa, mach_from_cas)

START_ALT_FT = 15000.0  # High enough that the hands-off sequence doesn't reach the ground.
START_KCAS = 250.0
WEIGHT_LB = 40000.0
EMPTY_KG = 13381.0  # M_empty in F-117-NightHawk.lua.
SETTLE_S = 3.0  # DCS runs this long after the start before the sequence begins.

# Seconds, pitch axis (+ is aft), roll axis (+ is right), yaw axis, throttle axis (-1 is full).
SCHEDULE = [
    (0.0, 0.0, 0.0, 0.0, -1.0),   # Full power, hands off: acceleration.
    (45.0, 0.0, 1.0, 0.0, -1.0),  # Full stick roll.
    (46.9, 0.0, 0.0, 0.0, -1.0),
    (52.0, 0.3, 0.0, 0.0, -1.0),  # Steady pull.
    (58.0, 0.0, 0.0, 0.0, -1.0),
    (64.0, 0.0, 0.0, 1.0, -1.0),  # Full pedal.
    (70.0, 0.0, 0.0, 0.0, -1.0),
    (76.0, 0.0, 0.0, 0.0, 1.0),   # Idle: deceleration.
]
END_S = 106.0

HOOK = r"""-- Temporary hook written by tools/fm_bench/dcs_check.py. Safe to delete.
local schedule = {SCHEDULE}
local endTime = {END}
local settle = {SETTLE}
local path = lfs.writedir() .. 'Logs\\F117_bench_check.csv'
local handle, startTime, finished
local hook = {{}}
function hook.onSimulationFrame()
    if finished then return end
    if DCS.getPause() then DCS.setPause(false) end
    local now = DCS.getModelTime()
    if not startTime then
        if now < settle or not Export.LoGetSelfData() then return end
        startTime = now
        handle = io.open(path, 'w')
        handle:write('t,alt_m,tas_mps,mach,aoa_deg,nz,pitch_rad,bank_rad,roll_rate,fuel_fraction\n')
    end
    local t = now - startTime
    local step = schedule[1]
    for _, row in ipairs(schedule) do if t >= row[1] then step = row end end
    Export.LoSetCommand(2001, step[2])
    Export.LoSetCommand(2002, step[3])
    Export.LoSetCommand(2003, step[4])
    Export.LoSetCommand(2004, step[5])
    if not Export.LoGetSelfData() then -- Aircraft lost: stop rather than fail on every frame.
        handle:close()
        finished = true
        local done = io.open(path .. '.done', 'w')
        done:write('lost')
        done:close()
        return
    end
    local accel = Export.LoGetAccelerationUnits() or {{y = 0}}
    local pitch, bank = Export.LoGetADIPitchBankYaw()
    local rates = Export.LoGetAngularVelocity() or {{x = 0}}
    local engine = Export.LoGetEngineInfo() or {{}}
    local fuel = engine.fuel_internal or 0
    handle:write(string.format('%.3f,%.2f,%.3f,%.4f,%.3f,%.3f,%.4f,%.4f,%.4f,%.4f\n', t,
        Export.LoGetAltitudeAboveSeaLevel(), Export.LoGetTrueAirSpeed(), Export.LoGetMachNumber(),
        Export.LoGetAngleOfAttack(), accel.y, pitch or 0, bank or 0, rates.x or 0, fuel))
    if t >= endTime then
        handle:close()
        finished = true
        local done = io.open(path .. '.done', 'w')
        done:write('done')
        done:close()
    end
end
DCS.setUserCallbacks(hook)
"""


# Takeoff from the worked example on TO 1F-117A-1 page A3-4: 46,000 lb, sea level conditions, normal performance.
TAKEOFF_WEIGHT_LB = 46000.0
TAKEOFF_ROTATE_KCAS = 178.0
TAKEOFF_GROUND_RUN_FT = 4700.0
TAKEOFF_CLEAR_50_FT = 6950.0
TAKEOFF_LIFTOFF_KCAS = 194.0

TAKEOFF_HOOK = r"""-- Temporary hook written by tools/fm_bench/dcs_check.py. Safe to delete.
local rotate = {ROTATE}
local path = lfs.writedir() .. 'Logs\\F117_bench_check.csv'
local brakeRelease = 8 -- Full power against the brakes first, since the manual's run starts from brake release at full power.
local handle, startTime, finished, startX, startZ, startAgl, gearUp
local hook = {{}}
function hook.onSimulationFrame()
    if finished then return end
    if DCS.getPause() then DCS.setPause(false) end
    local now = DCS.getModelTime()
    local me = Export.LoGetSelfData()
    if not startTime then
        if now < 3 or not me then return end
        Export.LoSetCommand(74)
        Export.LoSetCommand(2004, -1)
        if now < 3 + brakeRelease then return end
        Export.LoSetCommand(75)
        startTime = now
        startX, startZ = me.Position.x, me.Position.z
        startAgl = Export.LoGetAltitudeAboveGroundLevel()
        handle = io.open(path, 'w')
        handle:write('t,distance_m,agl_m,ias_mps,pitch_rad,aoa_deg,nz,msl_m\n')
    end
    local stop = not me
    if me then
        local t = now - startTime
        local ias = Export.LoGetIndicatedAirSpeed()
        Export.LoSetCommand(2004, -1)
        Export.LoSetCommand(2002, 0)
        Export.LoSetCommand(2003, 0)
        -- Rotate towards the 8 to 9 degrees of pitch on TO 1F-117A-1 page 2-13.
        local pull = 0
        if ias >= rotate then pull = math.max(0, math.min(0.35, 0.05 * (9 - me.Pitch * 57.3))) end
        Export.LoSetCommand(2001, pull)
        local dx, dz = me.Position.x - startX, me.Position.z - startZ
        local agl = Export.LoGetAltitudeAboveGroundLevel() - startAgl
        local accel = Export.LoGetAccelerationUnits() or {{y = 0}}
        handle:write(string.format('%.3f,%.2f,%.3f,%.3f,%.4f,%.3f,%.3f,%.1f\n', t, math.sqrt(dx * dx + dz * dz), agl, ias,
            me.Pitch, Export.LoGetAngleOfAttack(), accel.y, Export.LoGetAltitudeAboveSeaLevel()))
        if agl > 15 and not gearUp then
            Export.LoSetCommand(430)
            gearUp = true
        end
        stop = agl > 60 or t > 90
    end
    if stop then
        handle:close()
        finished = true
        local done = io.open(path .. '.done', 'w')
        done:write('done')
        done:close()
    end
end
DCS.setUserCallbacks(hook)
"""


def build_mission(template, target, fuel_kg, runway_start=False):
    from lupa import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
    with zipfile.ZipFile(template) as source:
        names = {name: source.read(name) for name in source.namelist()}
    lua.execute(names['mission'].decode('utf-8'))
    mission = lua.globals().mission
    h = START_ALT_FT * FT_TO_M
    tas = mach_from_cas(START_KCAS, h) * isa(h)[3]
    found = False
    for side in ('blue', 'red', 'neutrals'):
        coalition = mission['coalition'][side]
        countries = coalition['country'] if coalition else None
        for c in (list(countries) if countries else []):
            country = countries[c]
            for category in ('plane', 'helicopter', 'vehicle', 'ship', 'static'):
                groups = country[category]
                if not groups or not groups['group']:
                    continue
                for g in list(groups['group']):
                    group = groups['group'][g]
                    unit = group['units'][1]
                    if unit['skill'] == 'Player' and not found:
                        found = True
                        unit['payload']['fuel'] = fuel_kg
                        unit['payload']['pylons'] = lua.table()
                        point = group['route']['points'][1]
                        if runway_start:
                            if not point['airdromeId']:
                                raise SystemExit('--takeoff needs a mission whose player starts at an airfield')
                            point['type'], point['action'] = 'TakeOff', 'From Runway'
                            unit['parking'], unit['parking_id'] = None, None
                        else:
                            unit['alt'], unit['alt_type'], unit['speed'] = h, 'BARO', tas
                            unit['parking'], unit['parking_id'] = None, None
                            point['type'], point['action'] = 'Turning Point', 'Turning Point'
                            point['alt'], point['alt_type'], point['speed'] = h, 'BARO', tas
                            point['airdromeId'], point['helipadId'], point['linkUnit'] = None, None, None
                    else:
                        groups['group'][g] = None
    if not found:
        raise SystemExit(f'{template} has no player aircraft')
    weather = mission['weather']
    weather['season']['temperature'] = 10 if runway_start else 15
    weather['qnh'] = 760
    weather['groundTurbulence'] = 0
    for level in ('atGround', 'at2000', 'at8000'):
        weather['wind'][level]['speed'] = 0
    names['mission'] = ('mission = ' + _lua(mission) + '\n').encode('utf-8')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as out:
        for name, data in names.items():
            out.writestr(name, data)


def run_dcs(dcs_exe, saved_games, mission, hook_text=None):
    running = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout
    if 'DCS.exe' in running:
        raise SystemExit('Close DCS first.')
    output = saved_games / 'Logs/F117_bench_check.csv'
    done = Path(str(output) + '.done')
    hook_path = saved_games / 'Scripts/Hooks/zz_f117_bench_check.lua'
    for old in (output, done):
        old.unlink(missing_ok=True)
    schedule = '{' + ','.join('{' + ','.join(str(v) for v in row) + '}' for row in SCHEDULE) + '}'
    hook_path.write_text(hook_text or HOOK.format(SCHEDULE=schedule, END=END_S, SETTLE=SETTLE_S), encoding='utf-8')
    process = subprocess.Popen([str(dcs_exe), '--mission', str(mission)])
    try:
        deadline = time.time() + 420.0
        while not done.exists():
            if time.time() > deadline:
                raise SystemExit('DCS did not finish in 7 minutes. Check dcs.log for errors from the hook.')
            if process.poll() is not None:
                raise SystemExit('DCS closed before the sequence finished.')
            time.sleep(2.0)
    finally:
        process.terminate()
        hook_path.unlink(missing_ok=True)
    with open(output, newline='') as handle:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def run_bench(dll, first, inertia, work, mass_lb):
    sim = Sim(efm_module.Efm(dll, work), inertia)
    sim.start(mass_lb, first['alt_m'], first['mach'], alpha_deg=first['aoa_deg'], throttle=1.0, burn_fuel=True)
    rows = []
    t = 0.0
    index = 0
    efm = sim.efm
    while t < END_S:
        while index + 1 < len(SCHEDULE) and t >= SCHEDULE[index + 1][0]:
            index += 1
        _, pitch, roll, yaw, throttle = SCHEDULE[index]
        efm.command(CMD_PITCH_AXIS, pitch)
        efm.command(CMD_ROLL_AXIS, roll)
        efm.command(CMD_YAW_AXIS, yaw)
        efm.command(CMD_THROTTLE_AXIS, throttle)
        sim.step()
        t += DT
        rows.append({'t': t, 'alt_m': sim.h, 'tas_mps': sim.V, 'mach': sim.mach, 'aoa_deg': sim.alpha, 'nz': sim.nz,
                     'pitch_rad': sim.pitch * RAD, 'bank_rad': sim.roll * RAD, 'roll_rate': sim.p, 'beta': sim.beta,
                     'mass': sim.mass})
    return rows


def _at(rows, t, field):
    return min(rows, key=lambda row: abs(row['t'] - t))[field]


def _window(rows, start, end, field, reduce=lambda v: sum(v) / len(v)):
    values = [row[field] for row in rows if start <= row['t'] <= end]
    return reduce(values)


def compare(dcs, bench):
    rows = []

    def add(label, a, b, unit):
        rows.append(f'| {label} | {a:.2f} | {b:.2f} | {b - a:+.2f} {unit} |')

    for t in (15.0, 30.0, 44.0):
        add(f'Mach at {t:.0f} s, full power', _at(dcs, t, 'mach'), _at(bench, t, 'mach'), '')
    add('Altitude change at 44 s, hands off', _at(dcs, 44.0, 'alt_m') - dcs[0]['alt_m'], _at(bench, 44.0, 'alt_m') - bench[0]['alt_m'], 'm')
    add('Angle of attack at 30 s', _at(dcs, 30.0, 'aoa_deg'), _at(bench, 30.0, 'aoa_deg'), 'deg')
    add('Peak roll rate', abs(_window(dcs, 45.0, 47.5, 'roll_rate', lambda v: max(v, key=abs))) / RAD,
        abs(_window(bench, 45.0, 47.5, 'roll_rate', lambda v: max(v, key=abs))) / RAD, 'deg/s')
    add('Roll rate reversal after release', -_window(dcs, 46.9, 49.0, 'roll_rate', min) / RAD,
        -_window(bench, 46.9, 49.0, 'roll_rate', min) / RAD, 'deg/s')
    add('Bank after the roll', _at(dcs, 51.0, 'bank_rad') / RAD, _at(bench, 51.0, 'bank_rad') / RAD, 'deg')
    add('Load factor in the steady pull', _window(dcs, 55.0, 58.0, 'nz'), _window(bench, 55.0, 58.0, 'nz'), 'g')
    add('Angle of attack in the steady pull', _window(dcs, 55.0, 58.0, 'aoa_deg'), _window(bench, 55.0, 58.0, 'aoa_deg'), 'deg')
    add('Bank at the end of full pedal', _at(dcs, 70.0, 'bank_rad') / RAD, _at(bench, 70.0, 'bank_rad') / RAD, 'deg')

    def energy_height(data, t):
        return _at(data, t, 'alt_m') + _at(data, t, 'tas_mps') ** 2 / (2.0 * 9.81)

    add('Energy height gained at full power, first 44 s', energy_height(dcs, 44.0) - energy_height(dcs, 0.0),
        energy_height(bench, 44.0) - energy_height(bench, 0.0), 'm')
    add('Energy height lost in 30 s at idle', energy_height(dcs, 76.0) - energy_height(dcs, 106.0),
        energy_height(bench, 76.0) - energy_height(bench, 106.0), 'm')
    return rows


def takeoff_report(rows):
    """Compare a scripted takeoff with the manual's worked example."""
    settled = rows[0]
    liftoff = next((row for row in rows if row['agl_m'] > 0.3), None)
    clear = next((row for row in rows if row['agl_m'] > 50.0 * FT_TO_M), None)
    print(f"On the ground before the run: pitch {settled['pitch_rad'] / RAD:.2f} deg, airfield {settled['msl_m'] / FT_TO_M:.0f} ft above sea level")
    print("The manual's example is at sea level, so expect a longer run from a higher airfield.")
    lines = ['| Check | Manual | DCS |', '|---|---|---|']
    if liftoff:
        lines.append(f"| Ground run, ft | {TAKEOFF_GROUND_RUN_FT:.0f} | {liftoff['distance_m'] / FT_TO_M:.0f} |")
        lines.append(f"| Liftoff speed, KIAS against KCAS | {TAKEOFF_LIFTOFF_KCAS:.0f} | {liftoff['ias_mps'] / KT_TO_MPS:.0f} |")
    else:
        lines.append(f"| Ground run, ft | {TAKEOFF_GROUND_RUN_FT:.0f} | did not lift off |")
    if clear:
        lines.append(f"| Distance to clear 50 ft | {TAKEOFF_CLEAR_50_FT:.0f} | {clear['distance_m'] / FT_TO_M:.0f} |")
    return lines


def runway_activity(saved_games):
    """How far the elevons moved during the last DCS run's takeoff roll, with the stick centred."""
    with open(saved_games / 'Logs/F117_GLimiter_Debug.csv', newline='') as handle:
        rows = [row for row in csv.DictReader(handle) if row.get('ground_contact_fade')]  # DCS can stop mid-line.
    number = lambda row, name: float(row[name])
    run = [row for row in rows if number(row, 'ground_contact_fade') >= 1.0 and number(row, 'velocity_mps') > 10.0
           and abs(number(row, 'stickInput')) < 0.01 and abs(number(row, 'roll_stick')) < 0.01]
    print(f"After liftoff the ground contact fade ends at {number(rows[-1], 'ground_contact_fade'):.2f}, and it should be 0.")
    return [f"| Largest elevon roll movement on the runway, deg | none expected | {max(abs(number(row, 'roll_surface_out')) for row in run):.2f} |",
            f"| Largest elevon pitch movement on the runway, deg | none expected | {max(abs(number(row, 'elevatorOut')) for row in run):.2f} |",
            f"| Largest roll rate on the runway, deg/s | | {max(abs(number(row, 'roll_rate_dps')) for row in run):.2f} |"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--mission', type=Path, required=True, help='a mission on any map with a player F-117')
    parser.add_argument('--dcs', type=Path, default=Path(r'E:\Eagle Dynamics\DCS World\bin-mt\DCS.exe'))
    parser.add_argument('--saved-games', type=Path, default=efm_module.MOD_ROOT.parents[2])
    parser.add_argument('--dll', type=Path)
    parser.add_argument('--reuse', action='store_true', help='compare the last DCS run again without starting DCS')
    parser.add_argument('--takeoff', action='store_true', help='fly the takeoff in the manual\'s worked example instead')
    parser.add_argument('--fuel-kg', type=float, default=WEIGHT_LB * LB_TO_KG - EMPTY_KG, help='internal fuel in the DCS mission')
    parser.add_argument('--bench-weight-lb', type=float, help='weight flown on the bench (default: empty weight plus the fuel)')
    args = parser.parse_args()

    dll = args.dll or efm_module.default_dll()
    efm_module.build_stub()
    RESULTS.mkdir(exist_ok=True)
    if args.takeoff:
        mission = RESULTS / 'dcs_check_takeoff.miz'
        build_mission(args.mission, mission, TAKEOFF_WEIGHT_LB * LB_TO_KG - EMPTY_KG, runway_start=True)
        rows = run_dcs(args.dcs, args.saved_games, mission, TAKEOFF_HOOK.format(ROTATE=TAKEOFF_ROTATE_KCAS * KT_TO_MPS))
        lines = takeoff_report(rows) + runway_activity(args.saved_games)
        (RESULTS / 'dcs_check_takeoff.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('\n'.join(lines))
        return
    if args.reuse:
        with open(args.saved_games / 'Logs/F117_bench_check.csv', newline='') as handle:
            dcs = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]
    else:
        mission = RESULTS / 'dcs_check.miz'
        build_mission(args.mission, mission, args.fuel_kg)
        dcs = run_dcs(args.dcs, args.saved_games, mission)
    print(f"DCS start: {dcs[0]['alt_m']:.0f} m, Mach {dcs[0]['mach']:.3f}, AOA {dcs[0]['aoa_deg']:.2f}, fuel fraction {dcs[0]['fuel_fraction']:.3f}")
    bench_lb = args.bench_weight_lb or (EMPTY_KG + args.fuel_kg) / LB_TO_KG
    print(f'Bench weight: {bench_lb:.0f} lb')
    bench = run_bench(dll, dcs[0], read_inertia(), tempfile.mkdtemp(prefix='fm_bench_check_'), bench_lb)
    lines = ['| Check | DCS | Bench | Difference |', '|---|---|---|---|'] + compare(dcs, bench)
    (RESULTS / 'dcs_check.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
