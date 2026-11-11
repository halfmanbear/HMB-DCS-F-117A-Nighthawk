"""Build the F-117 missions that ship with the mod.

    python tools/missions/build_missions.py           # write every mission into Missions/
    python tools/missions/build_missions.py --probe   # write a terrain probe mission instead

Every mission is generated here, so change this file and run it again rather than
editing a mission in the editor. pydcs places the aircraft, targets and route. Then
miz.py stamps the module requirement and adds the lesson script, which prompts the pilot
through each step and reports success.

Needs: pip install -r tools/missions/requirements.txt
"""
import argparse
import logging
import math
import sys
from datetime import datetime
from pathlib import Path

logging.disable(logging.CRITICAL)  # pydcs reports every stock livery it cannot parse

import dcs  # noqa: E402
from dcs import mapping, statics, vehicles, weather  # noqa: E402
from dcs.mission import StartType  # noqa: E402
from dcs.terrain import Nevada  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from missions.f117_type import F117  # noqa: E402
from missions.miz import Miz  # noqa: E402

MOD = HERE.parents[1]
MISSIONS = MOD / 'Missions'
TRAINING = MISSIONS / 'Training'
QUICKSTART = MISSIONS / 'QuickStart'
AIRFIELD = 'Tonopah Test Range'
# The Tonopah canyon hangars are the D row on the south side of the field.
PARKING = 'D01'
NIGHT = datetime(1990, 10, 16, 20, 0)  # about two hours after sunset
FT = 0.3048

# Target areas: flat valley floors of the Nevada Test and Training Range (latitude, longitude).
SITES = {
    'kawich': (37.72, -116.42),     # Kawich Valley, east of Tonopah Test Range
    'gold_flat': (37.40, -116.38),  # Gold Flat, south-east
    'ralston': (37.90, -116.99),    # Ralston Valley, north-west; terrain probe: 6 m relief
    'cactus': (37.66, -116.70),     # south end of Cactus Flat
}
# Navigation lesson turn points.
ROUTE = [
    ('GOLDFIELD', 37.70, -117.23),
    ('SARCOBATUS', 37.28, -116.95),
    ('PAHUTE', 37.24, -116.45),
    ('KAWICH', 37.72, -116.42),
]

# Key reminders used in several briefings. Keep these in step with
# Input/F-117-NightHawk/keyboard/default.lua.
KEYS_FLIGHT = """\
Battery: RShift+L   APU start / stop: RShift+U
Ground power / ground air cart: RCtrl+RShift+P / RCtrl+RShift+A
Engines start / stop: RShift+Home / RShift+End (left RAlt+Home, right RCtrl+Home)
Canopy: LCtrl+C   Gear: G (LCtrl+G up, LShift+G down)
Nosewheel steering 45 degree range: hold N
Wheel brakes: W   Drag chute: P
Autopilot: A, path hold LAlt+1, altitude/heading hold LAlt+2, disengage LAlt+9
Autothrottle: J engage, LCtrl+J disengage
Next / previous waypoint: LCtrl+LAlt+LShift+. / ,
NVG: LShift+H"""

KEYS_ATTACK = """\
Master Arm: no default key. Bind 'Master Arm / Safe' in Controls before flying.
Weapon station next / previous: no default key ('Weapon Station Next / Previous').
Air-to-ground mode: 7   Navigation mode: 1
IRADS on/off: O   Slew: ; . , /   Designate / slew stop: Enter   Clear: Backspace
IRADS field of view: ] narrow, [ wide
Laser arm / safe: LShift+L (code 1688)
Weapon release (pickle): hold RAlt+Space. The selected store's bay opens and the store drops at the release point.
Bay doors: LShift+T both, LShift+LCtrl+T selected store, LShift+LAlt+T left, LShift+RAlt+T right
Jettison: LCtrl+W"""

DELIVERY = """\
The attack sequence:
1. Master Arm on. The VSD shows the selected store.
2. Slew the IRADS onto the target and press Enter to designate.
3. For laser-guided stores, arm the laser with LShift+L. It fires automatically from release to impact.
4. Fly towards the target with the steering cue centred.
5. Hold RAlt+Space. The cockpit releases when the solution is in zone.
The release status on the central display tells you what is still missing:
MASTER SAFE, NO TARGET, LASER NOT READY, ALIGN TARGET, OUT OF RANGE, RELEASE READY."""

LESSON_SCRIPT = r"""
-- Lesson prompts. Each step waits for its condition, shows its text and moves on.
local lesson = LESSON
local step, started = 1, false
local landed, airborne = false, false
local handler = {}
function handler:onEvent(e)
    local player = world.getPlayer()
    if not player or e.initiator ~= player then return end
    if e.id == world.event.S_EVENT_TAKEOFF then airborne = true end
    if e.id == world.event.S_EVENT_LAND or e.id == world.event.S_EVENT_RUNWAY_TOUCH then landed = airborne end
end
world.addEventHandler(handler)

local function gone(name)
    local group = Group.getByName(name)
    if group then
        for _, unit in ipairs(group:getUnits()) do
            if unit:isExist() and unit:getLife() >= 1 then return false end
        end
        return true
    end
    local object = StaticObject.getByName(name)
    return not object or not object:isExist() or object:getLife() < 1
end

local function done(s)
    local player = world.getPlayer()
    if s.kind == 'airborne' then return airborne end
    if s.kind == 'landed' then return landed end
    if s.kind == 'time' then return timer.getTime() >= s.at end
    if s.kind == 'near' and player then
        local p = player:getPoint()
        return math.sqrt((p.x - s.x) ^ 2 + (p.z - s.z) ^ 2) <= s.radius
    end
    if s.kind == 'destroyed' then
        for _, name in ipairs(s.targets) do if not gone(name) then return false end end
        return true
    end
    return false
end

local function tick()
    local s = lesson[step]
    if not s then return nil end
    if done(s) then
        trigger.action.outText(s.text, s.seconds or 20, true)
        if s.flag then trigger.action.setUserFlag(s.flag, true) end
        step = step + 1
    end
    return timer.getTime() + 1
end
timer.scheduleFunction(tick, nil, timer.getTime() + 2)
"""


def lua_value(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return repr(round(value, 1) if isinstance(value, float) else value)
    if isinstance(value, str):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(value, dict):
        return '{' + ', '.join(f'{k} = {lua_value(v)}' for k, v in value.items()) + '}'
    return '{' + ', '.join(lua_value(v) for v in value) + '}'


# Mission building ----------------------------------------------------------------

class Builder:
    def __init__(self, sortie):
        self.m = dcs.Mission(Nevada())
        self.m.set_sortie_text(sortie)
        self.m.start_time = NIGHT
        self.m.weather = clear_night()
        self.usa = self.m.country('USA')
        self.enemy = self.m.country('Russia')
        self.airfield = self.m.terrain.airports[AIRFIELD]
        self.lesson = []

    def point(self, lat, lon, heading=0.0, distance=0.0):
        p = mapping.Point.from_latlng(mapping.LatLng(lat, lon), self.m.terrain)
        return p.point_from_heading(heading, distance) if distance else p

    def player(self, name, stores, start, lat_lon_alt=None, heading=0.0, speed_kts=420):
        if start == 'air':
            lat, lon, alt_ft = lat_lon_alt
            group = self.m.flight_group_inflight(self.usa, name, F117, self.point(lat, lon), int(alt_ft * FT),
                                                 speed=speed_kts * 1.852)
            group.units[0].heading = heading
            group.points[0].alt_type = 'BARO'
        else:
            start_type = {'cold': StartType.Cold, 'hot': StartType.Warm, 'runway': StartType.Runway}[start]
            slots = [s for s in self.airfield.parking_slots if s.slot_name == PARKING] if start != 'runway' else None
            group = self.m.flight_group_from_airport(self.usa, name, F117, self.airfield, start_type=start_type,
                                                     parking_slots=slots or None)
        group.units[0].set_player()
        group.units[0].name = name
        group.units[0].fuel = F117.fuel_max
        F117.arm(group, *stores)
        self.group = group
        return group

    def waypoint(self, name, lat, lon, alt_ft, speed_kts=420):
        wp = self.group.add_waypoint(self.point(lat, lon), int(alt_ft * FT), speed_kts * 1.852)
        wp.name = name
        return wp

    def home(self):
        self.group.add_runway_waypoint(self.airfield)
        self.group.land_at(self.airfield)

    def vehicles(self, name, unit_type, lat, lon, count=1, heading=0.0, spacing=40):
        group = self.m.vehicle_group(self.enemy, name, unit_type, self.point(lat, lon), heading=heading,
                                     group_size=count, formation=dcs.unitgroup.VehicleGroup.Formation.Line)
        for i, unit in enumerate(group.units):
            p = self.point(lat, lon, heading + 90, (i - (count - 1) / 2) * spacing)
            unit.position = p
        group.points[0].position = self.point(lat, lon)
        hold_fire(group)
        return group

    def static(self, name, unit_type, lat, lon, heading=0.0, offset=(0.0, 0.0)):
        p = self.point(lat, lon, offset[0], offset[1])
        return self.m.static_group(self.enemy, name, unit_type, p, heading=heading)

    def say(self, kind, text, seconds=20, **extra):
        self.lesson.append(dict(kind=kind, text=text, seconds=seconds, **extra))

    def say_near(self, lat, lon, text, radius_nm=2.0):
        p = self.point(lat, lon)
        self.say('near', text, x=p.x, z=p.y, radius=radius_nm * 1852)

    def save(self, path, briefing, task):
        self.m.set_description_text(briefing)
        self.m.set_description_bluetask_text(task)
        if self.lesson:
            script = LESSON_SCRIPT.replace('LESSON', lua_value(self.lesson), 1)
            trigger = dcs.triggers.TriggerStart(comment='Lesson prompts')
            trigger.add_action(dcs.action.DoScript(self.m.string(script)))
            self.m.triggerrules.triggers.append(trigger)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.m.save(str(path))
        finish(path)
        print('wrote', path.relative_to(MOD))


def clear_night():
    w = weather.Weather(Nevada())
    w.clouds_density = 0
    w.clouds_thickness = 200
    w.clouds_base = 3000
    w.wind_at_ground = weather.Wind(270, 2)
    w.wind_at_2000 = weather.Wind(270, 6)
    w.wind_at_8000 = weather.Wind(280, 12)
    w.season_temperature = 10
    w.qnh = 760
    w.visibility = 80000
    return w


def hold_fire(group):
    """Range targets: they sit still and never shoot back."""
    from dcs.task import OptROE, OptAlarmState
    group.points[0].tasks.append(OptROE(OptROE.Values.WeaponHold))
    group.points[0].tasks.append(OptAlarmState(1))  # 1 = green: radars and weapons stowed


def finish(path):
    """Post-pass on the saved file: things pydcs does not write for a mod aircraft."""
    miz = Miz.load(path)
    miz.mission['requiredModules'] = miz.table({'F-117-NightHawk': 'F-117-NightHawk'})
    miz.files['theatre'] = miz.mission['theatre'].encode('utf-8')  # the mission list reads the map from here
    players = list(miz.player_units())
    assert len(players) == 1, f'{path.name}: expected one player, found {len(players)}'
    pylons = players[0][1]['payload']['pylons']
    assert sorted(pylons.keys()) == [1, 2], f'{path.name}: pylons {list(pylons.keys())}'
    miz.save(path)


# The missions --------------------------------------------------------------------

def lesson_1():
    b = Builder('F-117A Lesson 1 - Cold Start and Night Navigation')
    b.player('Bandit 1', ('GBU-27',), 'cold')
    for name, lat, lon in ROUTE:
        b.waypoint(name, lat, lon, 18000)
    b.home()
    b.say('time', 'Lesson 1. Battery on with RShift+L, then start the APU with RShift+U.\n'
          'Watch the displays boot and the attitude and heading settle as they align.', 30, at=8)
    b.say('time', 'Start the engines with RShift+Home. The right engine starts on APU air,\n'
          'then the left. Both reach idle in about a minute.', 30, at=40)
    b.say('time', 'Engines at idle. Shut down the APU with RShift+U, then taxi to the runway.\n'
          'Hold N for full nosewheel steering while you taxi.', 30, at=105)
    b.say('airborne', 'Airborne. Gear up with LCtrl+G. Climb to 18,000 ft and fly to waypoint 1, GOLDFIELD.\n'
          'The HSD and the map show the route. Engage the autopilot with A if you want it.')
    for i, (name, lat, lon) in enumerate(ROUTE, start=1):
        following = ROUTE[i][0] if i < len(ROUTE) else 'Tonopah Test Range'
        b.say_near(lat, lon, f'Waypoint {i}, {name}. The steering moves to the next point by itself inside 1 NM.\n'
                   f'Turn towards {following}.')
    b.say('landed', 'Good landing. Deploy the drag chute with P if you need it, and taxi clear.\n'
          'Lesson 1 complete.', 30, flag='lesson_complete')
    b.save(TRAINING / 'F-117A - Lesson 1 - Cold Start and Night Navigation.miz',
           'Night familiarisation sortie from Tonopah Test Range.\n\n'
           'You start in the canyon hangars, cold and dark. Switch on the battery and start the APU,\n'
           'let the displays boot and align, then start the engines, taxi, take off and fly the\n'
           'route GOLDFIELD - SARCOBATUS - PAHUTE - KAWICH at 18,000 ft, then return and land.\n\n'
           'Instructions appear on screen at each step.\n\n' + KEYS_FLIGHT,
           'Start, take off, fly the four-point route and land at Tonopah Test Range.')


def lesson_2():
    b = Builder('F-117A Lesson 2 - Laser-Guided Bombs')
    lat, lon = SITES['kawich']
    b.player('Bandit 1', ('GBU-27', 'GBU-10'), 'runway')
    b.waypoint('IP', lat + 0.25, lon - 0.10, 20000)
    b.waypoint('TGT', lat, lon, 20000)
    b.home()
    b.static('Bunker', statics.Fortification.Fire_Control_Bunker, lat, lon)
    b.vehicles('Convoy', vehicles.Unarmed.Ural_375, lat, lon + 0.02, count=4, heading=90, spacing=30)
    b.say('time', 'Lesson 2. Take off and climb to 20,000 ft. Fly to the IP, then the target.\n'
          'Master Arm on before the IP.', 30, at=8)
    b.say_near(lat + 0.25, lon - 0.10, 'IP. Slew the IRADS onto the bunker at the target point and press Enter.\n'
               'Arm the laser with LShift+L. Then hold RAlt+Space and keep the steering cue centred.', 4)
    b.say('destroyed', 'Bunker destroyed. Step to the other station and attack the trucks 2 km east.',
          targets=['Bunker'])
    b.say('destroyed', 'Trucks destroyed. Return to Tonopah Test Range and land.', targets=['Convoy'])
    b.say('landed', 'Lesson 2 complete.', 30, flag='lesson_complete')
    b.save(TRAINING / 'F-117A - Lesson 2 - Laser-Guided Bombs.miz',
           'Laser-guided bomb attack on the Kawich Valley range.\n\n'
           'Station 1: GBU-27 (penetrator) for the bunker. Station 2: GBU-10 for the truck line 2 km east.\n'
           'Both bombs follow the IRADS laser, code 1688. Keep the laser on the target until impact.\n'
           'The targets are inert and do not shoot back.\n\n' + DELIVERY + '\n\n' + KEYS_ATTACK,
           'Destroy the bunker with the GBU-27 and the trucks with the GBU-10, then land.')


def lesson_3():
    b = Builder('F-117A Lesson 3 - GPS Weapons')
    lat, lon = SITES['gold_flat']
    b.player('Bandit 1', ('AGM-154C', 'GBU-31V3'), 'air', (37.95, -116.50, 22000), heading=math.radians(170))
    b.waypoint('IP', lat + 0.30, lon, 22000)
    b.waypoint('TGT', lat, lon, 22000)
    b.home()
    site = b.vehicles('SAM', vehicles.AirDefence.Kub_1S91_str, lat, lon)
    for i, offset in enumerate((0, 120, 240)):
        launcher = b.m.vehicle_group(b.enemy, f'SAM launcher {i + 1}', vehicles.AirDefence.Kub_2P25_ln,
                                     b.point(lat, lon, offset, 250))
        hold_fire(launcher)
    b.static('Command bunker', statics.Fortification.Fire_Control_Bunker, lat - 0.03, lon + 0.04)
    b.say('time', 'Lesson 3. You are airborne north of the range. Master Arm on.\n'
          'Station 1 is the AGM-154C JSOW: it glides to its target from up to about 50 km at this height.', 30, at=6)
    b.say_near(lat + 0.30, lon, 'IP. Designate the SA-6 radar at the target point. The JSOW is in range when\n'
               'the status reads RELEASE READY. Hold RAlt+Space to launch.', 4)
    b.say('destroyed', 'Radar destroyed. Step to station 2, the GBU-31(V)3/B, and designate the command\n'
          'bunker 4 km south-east of the SAM site.', targets=['SAM'])
    b.say('destroyed', 'Bunker destroyed. Return to Tonopah Test Range.', targets=['Command bunker'])
    b.say('landed', 'Lesson 3 complete.', 30, flag='lesson_complete')
    b.save(TRAINING / 'F-117A - Lesson 3 - GPS Weapons.miz',
           'GPS-guided attack on Gold Flat.\n\n'
           'Station 1: AGM-154C JSOW against the SA-6 radar. Station 2: GBU-31(V)3/B against the command bunker.\n'
           'GPS weapons need no laser: designate, get in zone, release, and turn away.\n'
           'The SAM site is switched off for this lesson.\n\n' + DELIVERY + '\n\n' + KEYS_ATTACK,
           'Destroy the SA-6 radar with the JSOW and the command bunker with the JDAM, then land.')


def lesson_4():
    b = Builder('F-117A Lesson 4 - Unguided and Area Weapons')
    lat, lon = SITES['ralston']
    b.player('Bandit 1', ('MK-84', 'CBU-105'), 'air', (37.80, -116.60, 14000), heading=math.radians(300))
    b.waypoint('IP', lat, lon + 0.25, 14000)
    b.waypoint('TGT', lat, lon, 14000)
    b.home()
    b.static('Depot', statics.Fortification._Command_Center, lat, lon)
    b.vehicles('Armour', vehicles.Armor.T_72B, lat, lon + 0.03, count=4, heading=0, spacing=60)
    b.say('time', 'Lesson 4. Station 1 is a Mk-84 with no guidance: the cockpit releases it at the exact\n'
          'computed point, so fly straight and level with the steering cue centred.', 30, at=6)
    b.say('destroyed', 'Depot destroyed. Station 2 is the CBU-105. Its wind-corrected dispenser spreads\n'
          'anti-armour submunitions: designate the middle of the tank line 2.5 km east.', targets=['Depot'])
    b.say('destroyed', 'Armour destroyed. Return to Tonopah Test Range.', targets=['Armour'])
    b.say('landed', 'Lesson 4 complete.', 30, flag='lesson_complete')
    b.save(TRAINING / 'F-117A - Lesson 4 - Unguided and Area Weapons.miz',
           'Free-fall and area weapons in Ralston Valley.\n\n'
           'Station 1: Mk-84 against the depot. Station 2: CBU-105 against the tank line.\n'
           'Unguided bombs need an accurate pass: wings level, steady speed, cue centred until release.\n'
           'Release at 1,000 ft above the target or higher so the CBU-105 can open.\n\n'
           + DELIVERY + '\n\n' + KEYS_ATTACK,
           'Destroy the depot with the Mk-84 and the tanks with the CBU-105, then land.')


def lesson_5():
    b = Builder('F-117A Lesson 5 - Maverick')
    lat, lon = SITES['cactus']
    b.player('Bandit 1', ('AGM-65E', 'AGM-65D'), 'air', (37.90, -116.72, 11000), heading=math.radians(180))
    b.waypoint('TGT', lat, lon, 11000)
    b.home()
    b.vehicles('Trucks', vehicles.Unarmed.Ural_375, lat, lon, count=2, heading=90, spacing=40)
    b.vehicles('Tanks', vehicles.Armor.T_72B, lat - 0.03, lon, count=2, heading=90, spacing=60)
    b.say('time', 'Lesson 5. Mavericks are rockets: launch inside about 11 km with the target within\n'
          '28 degrees of the nose. Station 1 is the laser AGM-65E: arm the laser with LShift+L.', 30, at=6)
    b.say('destroyed', 'Trucks destroyed. Station 2, the AGM-65D, homes on the heat of the target:\n'
          'designate the tanks 3 km south. No laser needed.', targets=['Trucks'])
    b.say('destroyed', 'Tanks destroyed. Return to Tonopah Test Range.', targets=['Tanks'])
    b.say('landed', 'Lesson 5 complete.', 30, flag='lesson_complete')
    b.save(TRAINING / 'F-117A - Lesson 5 - Maverick.miz',
           'Maverick attack on Cactus Flat.\n\n'
           'Station 1: AGM-65E laser Maverick against the trucks. Station 2: AGM-65D infrared Maverick against\n'
           'the tanks. The F-117 never carried Mavericks in service; this lesson shows the trial loadout.\n\n'
           + DELIVERY + '\n\n' + KEYS_ATTACK,
           'Destroy the trucks with the AGM-65E and the tanks with the AGM-65D, then land.')


def quick_start():
    b = Builder('F-117A Nevada - Free Flight (Night)')
    b.player('Bandit 1', ('GBU-27',), 'air', (37.95, -116.78, 15000), heading=math.radians(180))
    for name, lat, lon in ROUTE:
        b.waypoint(name, lat, lon, 18000)
    b.home()
    lat, lon = SITES['kawich']
    b.static('Bunker', statics.Fortification.Fire_Control_Bunker, lat, lon)
    b.save(QUICKSTART / 'F-117A-NightHawk - Nevada - Free Flight (Night).miz',
           'Night free flight over the Nevada Test and Training Range, starting just north of Tonopah Test Range.\n'
           'Two GBU-27s are loaded and an inert bunker sits in Kawich Valley (waypoint 4) for practice.\n\n'
           + KEYS_FLIGHT + '\n\n' + KEYS_ATTACK,
           'Free flight. Land at Tonopah Test Range when you are done.')


ALL = [lesson_1, lesson_2, lesson_3, lesson_4, lesson_5, quick_start]


def probe(grid=False):
    """A mission that logs the terrain at every site and route point to dcs.log.

    With grid=True it samples the whole range on a 0.05 degree grid instead, to find flat ground."""
    b = Builder('F-117A terrain probe')
    b.player('Bandit 1', ('GBU-27',), 'air', (37.95, -116.78, 15000))
    points = list(SITES.items()) + [(n, (la, lo)) for n, la, lo in ROUTE]
    if grid:
        points = [(f'{37.25 + 0.05 * i:.2f},{-117.15 + 0.05 * j:.2f}', (37.25 + 0.05 * i, -117.15 + 0.05 * j))
                  for i in range(14) for j in range(18)]
    rows = []
    for name, (lat, lon) in points:
        p = b.point(lat, lon)
        rows.append({'name': name, 'x': p.x, 'z': p.y})
    script = ('local points = ' + lua_value(rows) + '\n' + r"""
for _, p in ipairs(points) do
    local low, high = 1e9, -1e9
    for dx = -1000, 1000, 250 do for dz = -1000, 1000, 250 do
        local h = land.getHeight({x = p.x + dx, y = p.z + dz})
        low, high = math.min(low, h), math.max(high, h)
    end end
    env.info(string.format('F117PROBE %s centre=%.0f low=%.0f high=%.0f surface=%d', p.name,
        land.getHeight({x = p.x, y = p.z}), low, high, land.getSurfaceType({x = p.x, y = p.z})))
end
local ab = Airbase.getByName('Tonopah Test Range')
if ab then local q = ab:getPoint(); env.info(string.format('F117PROBE airfield %.0f %.0f %.0f', q.x, q.y, q.z)) end
""")
    trigger = dcs.triggers.TriggerStart(comment='probe')
    trigger.add_action(dcs.action.DoScript(b.m.string(script)))
    b.m.triggerrules.triggers.append(trigger)
    path = HERE / ('results/terrain_grid.miz' if grid else 'results/terrain_probe.miz')
    path.parent.mkdir(exist_ok=True)
    b.m.save(str(path))
    finish(path)
    print('wrote', path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--probe', action='store_true', help='write the terrain probe mission instead')
    parser.add_argument('--probe-grid', action='store_true', help='write a probe of the whole range on a grid')
    args = parser.parse_args()
    if args.probe or args.probe_grid:
        probe(args.probe_grid)
        return
    for build in ALL:
        build()


if __name__ == '__main__':
    main()
