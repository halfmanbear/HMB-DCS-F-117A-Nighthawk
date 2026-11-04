# F-117A Nighthawk for DCS

Community Discord: https://discord.gg/qj6wz48jAn

This mod is a substantial rework and fork of [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117).

The External Flight Model used by this mod is also a substantial rework and fork of [WatchBambi/DCS-F-117-EFM](https://github.com/WatchBambi/DCS-F-117-EFM).

- Current EFM source code and related work: [halfmanbear/HMB-DCS-F-117A-EFM](https://github.com/halfmanbear/HMB-DCS-F-117A-EFM)

## Install

Download the latest `.zip` from Releases and extract it to:

```text
Saved Games/DCS/Mods/aircraft/F-117-NightHawk
```

If you still use the older Open Beta folder structure, install it to the corresponding `Saved Games/DCS.openbeta/Mods/aircraft/` path instead.

## First setup in DCS

Before flying, open the Controls menu for `F-117-NightHawk`, then use the `Adjust Controls` dropdown and configure the bindings under `F-117A Essential System Controls`.

At minimum, bind or verify these commands:

- `Air-To-Ground Mode` - required to employ munitions
- `Electro-Optical System On/Off` - required to enable the targeting MFD in Air-To-Ground mode
- `IRADS FOV - Narrow` / `IRADS FOV - Wide` (or the `IRADS FOV (Wide / Narrow)` axis)
- `Weapon Release` - for automatic bomb bay door opening on release, do not bind `Weapon Fire`
- `Bomb Bay Door Toggle` - manual bay door override
- `IRADS Laser Arm/Safe` - arms the EFM laser for laser-guided munitions
- `Drag Chute` - recommended for shorter-field landings
- `Refueling Hatch`
- `Tail Hook` - optional

### IRADS input migration

After updating, rebind any saved controls that used the old custom zoom IDs or
stock laser / sensor axes. Use `Throttle Designator Controller` directions and
`Depress / Slew Stop` to slew and designate; use `IRADS Designation Clear` to clear.
`TDC Slew Horizontal` and `TDC Slew Vertical` now route directly to the EFM IRADS
sensor. The FOV axis selects wide/narrow; its centre retains the previous selection.
The unsupported `Target Box Size` axis has been removed. `DLIR MFD Overlay Toggle`
is available for keyboard and joystick assignment.

The EFM repository's `Cockpit/Scripts` directory keeps copies of some cockpit
Lua files. This mod's files are the ones DCS loads, so change them here and copy
them over; `tests/test_efm_lua_copies.py` fails when a copy falls behind. IRADS
motion is handled by the EFM. Cockpit FOV controls dispatch absolute endpoint
selections, avoiding the legacy intermediate zoom preset.

## Cold start

A cold start is dark. `Electric Power Switch` (RShift+L) turns the battery on;
nothing powers without it. With the battery on, any of these powers the
displays:

- `APU Start / Stop` (RShift+U): the APU, which takes about 8 s to come up.
- `Ground Power Connect / Disconnect` (RCtrl+RShift+P): the ground crew's power
  cart.
- An engine generator, which comes on line at 56 % core rpm.

The displays then boot one at a time: the DEP, the HUD fading in, then the left
CMDI, the SD and the right CMDI. Each CMDI, the SD and the DEP show a self-test
and auto-cal screen first. The attitude, heading and air data then slew to the
true values while the gyros erect and the heading aligns, which takes about
30 s for attitude and 50 s for heading. The boot screens are illustrative: the
references don't document the real ones. Without the APU or ground power, the
displays go dark when the engines are shut down, and boot again on the next
start.

Each engine's air turbine starter needs start air from the APU, the ground
crew's air cart (`Ground Air Connect / Disconnect`, RCtrl+RShift+A) or
crossbleed from the other engine once it runs. Without start air a start is
refused with `ENGINE START NEEDS START AIR`. The carts connect only while the
aircraft is stopped on the ground, and taxiing away disconnects them.

- `Engines Start` (RShift+Home) starts the right engine, then the left on
  crossbleed or the start air. Each starter takes the start air in turn.
- `Engine Left Start` (RAlt+Home) and `Engine Right Start` (RCtrl+Home) start one
  engine; the matching End keys stop it. `Engines Stop` (RShift+End) stops both.

The starter turns the core to light-off at 15 %. The engine lights and
accelerates, the starter disengages at 54 %, and the engine settles at ground
idle about 30 s after its start. The APU and carts can go once the engines run.
An engine still turning above 15 % (spooling down, or windmilling after a
flameout) relights without start air.

EGT peaks at about 600 °C during a start and settles at about 420 °C at idle.
Oil pressure peaks at about 85 psi and settles at 70 psi, and fuel flow is
600 lb/hr per engine during the start (TO 1F-117A-1 page 2-7). Hot and air
starts begin powered and aligned.

## OCIP III displays

Mission defaults: **left colour VSD | centre green IRADS | right colour MAP**.
Under **F-117A Displays**, select VSD, grayscale EO/IRADS, MAP or HSD on the
left CMDI; select MAP, HSD or VSD on the right. Ctrl+Shift+E toggles left EO/VSD.
Format selection preserves sensor power, pointing and designation. MAP uses the
existing navigation overlay and configured chart source; terrain imagery depends
on that source being available.

IRADS has two selectable FOVs: **wide and narrow**. Rebind saved FOV buttons to
`IRADS FOV - Wide` / `IRADS FOV - Narrow`: these now use cockpit commands that
select the installed EFM's endpoints directly. Legacy direct EFM command IDs can
still access its old intermediate preset. The axis uses -1 wide and +1 narrow;
its centre retains the previous selection, with hysteresis around zero. The
existing endpoint optics are retained; no new historical FOV angles are asserted.

## HUD and IRADS cursor

A small open-centred cross on the HUD marks where the IRADS is looking. Past the
20 deg total field of view, or off the drawn HUD area, it holds at the edge toward
the sensor. A 10 mrad box marks the IRADS ground lock point once locked. This needs
the matching EFM build.

## Weapon delivery

1. `Air-To-Ground Mode`, then `Electro-Optical System On/Off`. Master Arm starts SAFE.
2. Slew the IRADS and designate terrain with `Depress / Slew Stop`. POINT and RNG on
   the display show the lock state. Slewing again exits point track.
3. `IRADS Laser Arm/Safe` plus a valid designation gives code-1688 illumination.
   Laser-guided bombs need a live laser spot until impact. JDAMs take the designated
   coordinate and need no laser.
4. `Weapon Station Next / Previous` selects the store. Hold `Weapon Release`
   (Right Alt+Space) to give CCRP consent. The EFM opens the bay and releases one store
   when every release gate passes, then steps to the next loaded station. Press again
   for the next store.

ALIGN TARGET means the lateral offset is too large and OUT OF RANGE means the estimated
range window is missed. The JDAM alignment limit (30 deg) and the laser-guided limit
(15 deg) are tuning assumptions. EST TOF is predicted flight time, not tracking of the
released weapon.

## Autothrottle and PAARS

`J` engages CAS HOLD at the current airspeed once airborne and `J` again disengages.
`LCtrl+J` is the A/T disconnect button and `LAlt+9` the stick disengage paddle. `LAlt+3`
selects PAARS. Details are in [docs/autothrottle-paars.md](docs/autothrottle-paars.md).

## Included content

This package currently includes:

- Nine liveries covering every skin, bay and door material of the exterior model
- Quick start missions (Caucasus day, Nevada night) and five Nevada night training
  lessons under `Missions/Training`, all generated by `tools/missions/build_missions.py`
- All 14 pylon stores release from the bays, and all are stock DCS weapons: GBU-27,
  GBU-10 and GBU-12 (laser code 1688), GBU-31(V)1/B, GBU-31(V)3/B and GBU-32(V)2/B
  JDAMs, AGM-154A/B/C JSOW, CBU-105, Mk-82, Mk-84, and the trial AGM-65D and AGM-65E
  Mavericks. Missions made before the stock JDAM change need those JDAMs re-armed.
- A 25-cell damage model, platypus exhaust heat haze with night glow, and overwing vapour
- Cockpit lighting, power, engine start and display scripts

## Development tools

- `tools/fm_bench/` flies the built EFM against the flight manual data; see its README.
- `tools/missions/` builds the missions and runs DCS store-release tests.
- `tools/sync_livery_materials.py` rebuilds the livery tables after an exterior re-export.
- `tests/` holds the offline tests: `python -m pytest tests`.

## Credits

- Initial development, EFM, EDMs, and base mod project: `@JinxxDCS`, `@WatchBambi`
- Latest development, fixes, improvements, and new features: `HalfManBear (HMB)`

## Legal / Attribution

Please keep attribution to the upstream projects when redistributing or further forking this work:

- Original Mod fork base: [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117)
- Original EFM fork base:[WatchBambi/DCS-F-117-EFM](https://github.com/WatchBambi/DCS-F-117-EFM).