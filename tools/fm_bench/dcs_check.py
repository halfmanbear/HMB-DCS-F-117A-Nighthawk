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
import math
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
TAKEOFF_LIFTOFF_AOA_DEG = 6.5

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


# Landing from the worked example on TO 1F-117A-1 pages A8-2 to A8-4: 36,000 lb, sea level, 10 kt headwind,
# 0.5% upslope, dry runway. Final approach speed is reached at 50 ft, touchdown is 7.5 s later at 95% of it, the
# nose comes down at about 2.5 deg/s, the chute goes out at nose touchdown and the brakes go on at the chart's
# brake application speed.
LANDING_WEIGHT_LB = 36000.0
LANDING_FINAL_KCAS = 158.0
LANDING_TOUCHDOWN_KCAS = 149.0
LANDING_HEADWIND_KT = 10.0
LANDING_CASES = {
    # chute: (brake application KCAS, ground roll ft, total from 50 ft)
    True: (126.0, 3000.0, 4900.0),
    False: (139.0, 4100.0, 5900.0),
}
LANDING_START_M = 2500.0  # Distance from the aim point to the air start, on a 3 deg glide path.
LANDING_WHEEL_HEIGHT_M = 2.12  # Height of the aircraft origin above the runway on its wheels, measured in DCS.
LANDING_START_WIND_KT = 15.0  # DCS sets the air start speed over the ground; the wind at the start height is about this.
# Kobuleti runway 07 from Mods/terrains/Caucasus/Beacons.lua. The far homer and localizer are on the centreline;
# the aim point is abeam the glideslope antenna.
KOBULETI_FAR_HOMER = (-319739.03125, 630753.5625)
KOBULETI_LOCALIZER = (-317495.75, 636918.25)
KOBULETI_GLIDESLOPE = (-318329.625, 634820.8125)
KOBULETI_ELEVATION_M = 18.01

LANDING_HOOK = r"""-- Temporary hook written by tools/fm_bench/dcs_check.py. Safe to delete.
local ux, uz, aimX, aimZ = __UX__, __UZ__, __AIMX__, __AIMZ__
local chute, brakeIas = __CHUTE__, __BRAKE__
local finalIas, touchdownIas = __FINAL__, __TOUCHDOWN__
local wheelHeight, tanGlide = __WHEEL__, math.tan(math.rad(3))
local path = lfs.writedir() .. 'Logs\\F117_bench_check.csv'
local handle, startTime, lastTime, finished
local phase = 0 -- 0 approach, 1 flare, 2 main gear down, 3 nose gear down
local trim, nzFiltered, throttleI, bankI, pitchI = 0, 1, 0, 0, 0
local braked, chuteOut, flareThrottle = 0, 0, 0
local lastCockpit, cockpitCas = nil, -1
local function clamp(v, lo, hi) return math.max(lo, math.min(hi, v)) end
-- Inverse of the stick shaping in FlightControls.cpp, as pitch_axis_for_nz_delta and roll_axis_for_rate in sim.py.
local function pitchAxis(delta)
    if delta >= 0 then
        local force = delta < 0.4 and (delta + 0.128) / 0.016 or (delta + 1.811) / 0.067
        return math.min(force / 180, 1)
    end
    local pull = -delta
    local force = pull < 0.4 and (pull + 0.128) / 0.016 or (pull + 2.128) / 0.0766
    return math.max(-force / 80, -1)
end
local function rollAxis(rate)
    if math.abs(rate) < 0.05 then return 0 end
    local force = 3 + math.sqrt(math.abs(rate) / (150 / 72 ^ 2))
    local axis = math.min(force / 75, 1)
    return rate < 0 and -axis or axis
end
local function throttleFor(target, ias, dt)
    throttleI = clamp(throttleI + 0.02 * (target - ias) * dt, -0.4, 0.5)
    return clamp(0.45 + 0.08 * (target - ias) + throttleI, 0, 1)
end
local hook = {}
function hook.onSimulationFrame()
    if finished then return end
    if DCS.getPause() then DCS.setPause(false) end
    local now = DCS.getModelTime()
    local me = Export.LoGetSelfData()
    if not startTime then
        if not me then return end
        startTime, lastTime = now, now
        Export.LoSetCommand(431)
        handle = io.open(path, 'w')
        handle:write('t,phase,along_m,xtrack_m,agl_m,ias_mps,gs_mps,vs_mps,pitch_deg,aoa_deg,nz,throttle,wind_along_mps,chute,brake,dcs_ias_mps,cockpit_cas_mps\n')
    end
    if not me then
        handle:close()
        finished = true
        local done = io.open(path .. '.done', 'w')
        done:write('lost')
        done:close()
        return
    end
    local t, dt = now - startTime, math.max(now - lastTime, 0.001)
    lastTime = now
    local dx, dz = me.Position.x - aimX, me.Position.z - aimZ
    local along, xtrack = dx * ux + dz * uz, -dx * uz + dz * ux
    local v = Export.LoGetVectorVelocity()
    local vs, gs = v.y, math.sqrt(v.x * v.x + v.z * v.z)
    local xrate = -v.x * uz + v.z * ux
    local agl = Export.LoGetAltitudeAboveGroundLevel()
    local above = agl - wheelHeight
    -- With wind set, DCS's true airspeed export is ground speed and its IAS reads high, so take the airspeed
    -- the EFM flies on from ground velocity less the wind. Calibrated and true differ by under 1% here.
    local wind = Export.LoGetVectorWindVelocity() or {x = 0, y = 0, z = 0}
    local ax, ay, az = v.x - wind.x, v.y - (wind.y or 0), v.z - wind.z
    local ias = math.sqrt(ax * ax + ay * ay + az * az) * __CAS_PER_TAS__
    local dcsIas = Export.LoGetIndicatedAirSpeed()
    -- The airspeed the cockpit shows (F117_CAS_MPS from the EFM), or -1 if this DCS can't list cockpit params here.
    if not lastCockpit or now - lastCockpit > 0.25 then
        lastCockpit = now
        local ok, text = pcall(net.dostring_in, 'export', 'return list_cockpit_params()')
        cockpitCas = ok and tonumber((text or ''):match('F117_CAS_MPS:%s*([%-%d%.eE]+)')) or -1
    end
    local pitch, bank = math.deg(me.Pitch), math.deg(me.Bank)
    local nz = (Export.LoGetAccelerationUnits() or {y = 1}).y
    local q = math.deg((Export.LoGetAngularVelocity() or {z = 0}).z)
    local herr = math.deg(me.Heading - math.atan2(uz, ux))
    herr = (herr + 180) % 360 - 180

    if phase == 0 and above <= 15.24 then phase = 1 end
    if phase == 1 and above <= 0.12 then phase = 2 pitchI = 0 end
    if phase == 2 and pitch <= 0.9 then
        phase = 3
        if chute then Export.LoSetCommand(76) chuteOut = 1 end
    end

    local stick, throttle, roll, yaw = 0, 0, 0, 0
    if phase <= 1 then
        local vsCmd, iasCmd
        if phase == 0 then
            vsCmd = -gs * tanGlide + 0.3 * (wheelHeight + math.max(0, -along) * tanGlide - agl)
            iasCmd = finalIas
        else
            -- Gentle flare, timed for the manual's 7.5 s from 50 ft to touchdown.
            vsCmd = -math.min(gs * tanGlide, 0.65 + 0.19 * math.max(0, above))
        end
        -- Page 2-12 retards the throttles to idle "in the flare and touchdown phase". The approach setting is held
        -- into the flare and cut to idle 10 ft above the runway, so touchdown speed is a result, not a target.
        if phase == 0 then
            throttle = throttleFor(iasCmd, ias, dt)
            flareThrottle = throttle
        elseif above > 3.0 then
            throttle = flareThrottle
        end
        local accel = clamp(1.2 * (vsCmd - vs), -3, 3)
        local att = math.cos(math.rad(bank)) * math.cos(math.rad(pitch))
        local desired = (1 + accel / 9.81) / math.max(att, 0.5)
        nzFiltered = nzFiltered + (nz - nzFiltered) * math.min(1, 8 * dt)
        trim = clamp(trim + 0.5 * (desired - nzFiltered) * dt, -3, 3)
        stick = pitchAxis(desired - att + trim)
        pitchI = stick
        local bankCmd = clamp(-0.5 * xtrack - 2.0 * xrate, -10, 10)
        bankI = clamp(bankI + 0.6 * (bankCmd - bank) * dt, -30, 30)
        roll = rollAxis(clamp(2.5 * (bankCmd - bank) + bankI, -40, 40))
    else
        if phase == 2 then
            -- Lower the nose in about 3 s, as the manual's landing data assume (2.5 deg/s on average).
            pitchI = clamp(pitchI + 0.15 * (-3.0 - q) * dt, -0.6, 0.3)
            stick = clamp(pitchI + 0.06 * (-3.0 - q), -0.6, 0.3)
        else
            stick = -0.1
        end
        roll = rollAxis(clamp(-2.5 * bank, -20, 20))
        yaw = clamp(-(0.08 * herr + 0.05 * xtrack), -0.6, 0.6)
        if phase == 3 and braked == 0 and ias <= brakeIas then
            Export.LoSetCommand(74)
            braked = 1
        end
    end
    Export.LoSetCommand(2001, stick)
    Export.LoSetCommand(2002, roll)
    Export.LoSetCommand(2003, yaw)
    Export.LoSetCommand(2004, 1 - 2 * throttle)
    handle:write(string.format('%.3f,%d,%.2f,%.2f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%d,%d,%.3f,%.3f\n', t, phase, along,
        xtrack, agl, ias, gs, vs, pitch, Export.LoGetAngleOfAttack(), nz, throttle, wind.x * ux + wind.z * uz, chuteOut, braked,
        dcsIas, cockpitCas))
    if (phase == 3 and gs < 0.5) or t > 240 then
        handle:close()
        finished = true
        local done = io.open(path .. '.done', 'w')
        done:write('done')
        done:close()
    end
end
DCS.setUserCallbacks(hook)
"""


def landing_geometry():
    """Runway course unit vector and aim point, in DCS world x (north) and z (east)."""
    fx, fz = KOBULETI_FAR_HOMER
    lx, lz = KOBULETI_LOCALIZER
    length = math.hypot(lx - fx, lz - fz)
    ux, uz = (lx - fx) / length, (lz - fz) / length
    gx, gz = KOBULETI_GLIDESLOPE
    s = (gx - lx) * ux + (gz - lz) * uz
    return ux, uz, lx + s * ux, lz + s * uz


def build_landing_mission(template, target, fuel_kg, wind_from_deg):
    """Air start on a 3 deg final to Kobuleti runway 07 with the gear up, standard sea level weather and a headwind."""
    from lupa import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
    with zipfile.ZipFile(template) as source:
        names = {name: source.read(name) for name in source.namelist()}
    lua.execute(names['mission'].decode('utf-8'))
    mission = lua.globals().mission
    if mission['theatre'] != 'Caucasus':
        raise SystemExit('--landing needs a Caucasus mission: it lands at Kobuleti')
    ux, uz, aim_x, aim_z = landing_geometry()
    x, z = aim_x - LANDING_START_M * ux, aim_z - LANDING_START_M * uz
    h = KOBULETI_ELEVATION_M + LANDING_WHEEL_HEIGHT_M + LANDING_START_M * math.tan(3.0 * RAD)
    tas = mach_from_cas(LANDING_FINAL_KCAS, h) * isa(h)[3] - LANDING_START_WIND_KT * KT_TO_MPS  # Ground speed.
    heading = math.atan2(uz, ux)
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
                        unit['x'], unit['y'], unit['alt'], unit['alt_type'], unit['speed'] = x, z, h, 'BARO', tas
                        unit['heading'], unit['psi'] = heading, -heading
                        unit['parking'], unit['parking_id'] = None, None
                        group['units'] = lua.table_from({1: unit})  # No wingmen.
                        group['x'], group['y'] = x, z
                        first = group['route']['points'][1]
                        points = lua.table()
                        for i, distance in ((1, 0.0), (2, 20000.0)):
                            point = lua.table_from(dict(first.items()))
                            point['x'], point['y'] = x + distance * ux, z + distance * uz
                            point['type'], point['action'] = 'Turning Point', 'Turning Point'
                            point['alt'], point['alt_type'], point['speed'] = h, 'BARO', tas
                            point['airdromeId'], point['helipadId'], point['linkUnit'] = None, None, None
                            points[i] = point
                        group['route']['points'] = points
                    else:
                        groups['group'][g] = None
    if not found:
        raise SystemExit(f'{template} has no player aircraft')
    weather = mission['weather']
    weather['season']['temperature'] = 10
    weather['qnh'] = 760
    weather['groundTurbulence'] = 0
    for level in ('atGround', 'at2000', 'at8000'):
        weather['wind'][level]['speed'] = LANDING_HEADWIND_KT * KT_TO_MPS
        weather['wind'][level]['dir'] = wind_from_deg
    names['mission'] = ('mission = ' + _lua(mission) + '\n').encode('utf-8')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as out:
        for name, data in names.items():
            out.writestr(name, data)
    return ux, uz, aim_x, aim_z


def landing_cas_per_tas():
    """Calibrated over true airspeed at Kobuleti with standard pressure and 10 C, at landing speeds."""
    density = 101325.0 / (287.058 * 283.15)
    return math.sqrt(density / 1.225)


def landing_hook(geometry, chute):
    ux, uz, aim_x, aim_z = geometry
    values = {'__UX__': ux, '__UZ__': uz, '__AIMX__': aim_x, '__AIMZ__': aim_z, '__CHUTE__': 'true' if chute else 'false',
              '__BRAKE__': LANDING_CASES[chute][0] * KT_TO_MPS, '__FINAL__': LANDING_FINAL_KCAS * KT_TO_MPS,
              '__TOUCHDOWN__': LANDING_TOUCHDOWN_KCAS * KT_TO_MPS, '__WHEEL__': LANDING_WHEEL_HEIGHT_M,
              '__CAS_PER_TAS__': landing_cas_per_tas()}
    text = LANDING_HOOK
    for key, value in values.items():
        text = text.replace(key, value if isinstance(value, str) else repr(float(value)))
    return text


def landing_report(rows, chute):
    """Compare a scripted landing with the manual's worked example."""
    brake_kt, roll_ft, total_ft = LANDING_CASES[chute]
    fifty = next((row for row in rows if row['phase'] >= 1), None)
    touch = next((row for row in rows if row['phase'] >= 2), None)
    nose = next((row for row in rows if row['phase'] >= 3), None)
    brake = next((row for row in rows if row['brake'] >= 1), None)
    stop = rows[-1]
    label = 'with chute' if chute else 'without chute'
    flare_rows = [row for row in rows if row['phase'] == 1] or rows
    headwind = -sum(row['wind_along_mps'] for row in flare_rows) / len(flare_rows) / KT_TO_MPS
    lines = [f'### {label.capitalize()}', '', f'Measured headwind in the flare: {headwind:.1f} kt (the manual example has 10 kt).', '',
             '| Check | Manual | DCS |', '|---|---|---|']
    if not (fifty and touch):
        return lines + ['| Landing | | did not touch down |']
    glide = [row for row in rows if row['phase'] == 0 and row['t'] >= fifty['t'] - 10.0]
    lines += [f"| Throttle on the glideslope, last 10 s | | {sum(r['throttle'] for r in glide) / len(glide):.0%} |",
              f"| Throttle in the flare | retarded to idle | approach setting to 10 ft, then idle (scripted) |",
              f"| Speed at 50 ft, KCAS | {LANDING_FINAL_KCAS:.0f} | {fifty['ias_mps'] / KT_TO_MPS:.0f} |",
              f"| 50 ft to touchdown, s | 7.5 | {touch['t'] - fifty['t']:.1f} |",
              f"| Touchdown speed, KCAS | {LANDING_TOUCHDOWN_KCAS:.0f} | {touch['ias_mps'] / KT_TO_MPS:.0f} |",
              f"| DCS IAS at touchdown, kt | | {touch['dcs_ias_mps'] / KT_TO_MPS:.0f} |",
              f"| Cockpit airspeed (EFM air data) at touchdown, kt | | "
              f"{touch['cockpit_cas_mps'] / KT_TO_MPS:.0f} |" if touch['cockpit_cas_mps'] >= 0 else
              "| Cockpit airspeed (EFM air data) at touchdown, kt | | not readable from the hook |",
              f"| Touchdown pitch, deg | below 12 (elevon strike) | {touch['pitch_deg']:.1f} |",
              f"| Touchdown AoA, deg | | {touch['aoa_deg']:.1f} |",
              f"| Touchdown sink rate, ft/min | | {-touch['vs_mps'] * 196.85:.0f} |",
              f"| Air distance, 50 ft to touchdown, ft | {total_ft - roll_ft:.0f} | {(touch['along_m'] - fifty['along_m']) / FT_TO_M:.0f} |"]
    if nose:
        lines.append(f"| Main to nose touchdown, s | about 3 | {nose['t'] - touch['t']:.1f} |")
    if brake:
        lines.append(f"| Brake application speed, KCAS | {brake_kt:.0f} | {brake['ias_mps'] / KT_TO_MPS:.0f} |")
    stopped = stop['phase'] >= 3 and stop['gs_mps'] <= 0.6
    if stopped:
        lines += [f"| Ground roll, ft | {roll_ft:.0f} | {(stop['along_m'] - touch['along_m']) / FT_TO_M:.0f} |",
                  f"| Total from 50 ft, ft | {total_ft:.0f} | {(stop['along_m'] - fifty['along_m']) / FT_TO_M:.0f} |"]
    else:
        lines.append(f"| Ground roll, ft | {roll_ft:.0f} | did not stop |")
    lines.append(f"| Largest distance from the centreline, m | | {max(abs(r['xtrack_m']) for r in rows if r['phase'] >= 2):.1f} |")
    return lines


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
        # DCS takes a while to exit, and a second run in the same call must not find it still open.
        for _ in range(60):
            if 'DCS.exe' not in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq DCS.exe'], capture_output=True, text=True).stdout:
                break
            time.sleep(2.0)
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
        # Manual page A3-1: liftoff is about 2 deg under the 8.5 deg reference, from ground effect and the second engine.
        lines.append(f"| Liftoff AoA, deg | about {TAKEOFF_LIFTOFF_AOA_DEG:.1f} | {liftoff['aoa_deg']:.1f} |")
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
    parser.add_argument('--landing', action='store_true',
                        help='fly the manual\'s landing example at Kobuleti, with and without the chute (needs a Caucasus mission)')
    parser.add_argument('--wind-from', type=float, default=250.0,
                        help='mission wind direction for --landing; the report shows the headwind DCS actually gave')
    parser.add_argument('--no-chute-only', action='store_true', help='with --landing, fly only the landing without the chute')
    parser.add_argument('--fuel-kg', type=float, default=WEIGHT_LB * LB_TO_KG - EMPTY_KG, help='internal fuel in the DCS mission')
    parser.add_argument('--bench-weight-lb', type=float, help='weight flown on the bench (default: empty weight plus the fuel)')
    args = parser.parse_args()

    dll = args.dll or efm_module.default_dll()
    efm_module.build_stub()
    RESULTS.mkdir(exist_ok=True)
    if args.landing:
        mission = RESULTS / 'dcs_check_landing.miz'
        geometry = build_landing_mission(args.mission, mission, LANDING_WEIGHT_LB * LB_TO_KG - EMPTY_KG, args.wind_from)
        lines = [f'# Landing check against TO 1F-117A-1 pages A8-2 to A8-4', '',
                 f'{LANDING_WEIGHT_LB:.0f} lb at Kobuleti (59 ft), 10 C. The manual example also has a 0.5% upslope, '
                 'which this runway does not model.', '']
        for chute in ((False,) if args.no_chute_only else (True, False)):
            rows = run_dcs(args.dcs, args.saved_games, mission, landing_hook(geometry, chute))
            lines += landing_report(rows, chute) + ['']
            print('\n'.join(lines))
        (RESULTS / 'dcs_check_landing.md').write_text('\n'.join(lines), encoding='utf-8')
        return
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
