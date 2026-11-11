# F-117A Nighthawk for DCS

Community Discord: https://discord.gg/qj6wz48jAn

This mod is a substantial rework of [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117), with a fully reworked External Flight Model. See Credits below.

- EFM source code and related work: [halfmanbear/HMB-DCS-F-117A-EFM](https://github.com/halfmanbear/HMB-DCS-F-117A-EFM)

## Install

Download the latest `.zip` from Releases and extract it to:

```text
Saved Games/DCS/Mods/aircraft/F-117-NightHawk
```

If you still use the older Open Beta folder structure, install it to the corresponding `Saved Games/DCS.openbeta/Mods/aircraft/` path instead.

## First setup in DCS

Before flying, open the Controls menu for `F-117-NightHawk`, then use the `Adjust Controls` dropdown and configure the bindings under `F-117A Essential System Controls`.

At minimum, bind or verify these commands:

- `(7) Air-To-Ground Mode` - required to employ munitions
- `IRADS On/Off` (O) - required to enable the targeting MFD in Air-To-Ground mode
- `IRADS FOV - Narrow` / `IRADS FOV - Wide` (or the `IRADS FOV (Wide / Narrow)` axis)
- `Master Arm / Safe` - starts SAFE
- `Weapon Station Next` / `Weapon Station Previous` - select the store
- `Weapon Release (Pickle)` (RAlt+Space) - for automatic bomb bay door opening on release, do not bind `Weapon Fire`
- `Bomb Bay Door Toggle` - manual bay door override, one binding per door set: `Bomb Bay Doors Toggle (Both)`
  (LShift+T), `Bomb Bay Door Toggle (Selected Store)` (LShift+LCtrl+T), `Bomb Bay Door Toggle (Left)`
  (LShift+LAlt+T) and `Bomb Bay Door Toggle (Right)` (LShift+RAlt+T)
- `IRADS Laser Arm/Safe` - arms the EFM laser for laser-guided munitions
- `Drag Chute` - recommended for shorter-field landings
- `Refueling Hatch`
- `Tail Hook` - optional

### IRADS controls

Use `Throttle Designator Controller` directions (or the `TDC Slew Horizontal` and
`TDC Slew Vertical` axes) and `Depress / Slew Stop` to slew and designate, and
`IRADS Designation Clear` to clear. `DLIR MFD Overlay Toggle` is available for
keyboard and joystick assignment.

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

IRADS has two selectable FOVs: **wide and narrow**, on `IRADS FOV - Wide` /
`IRADS FOV - Narrow`. The axis uses -1 wide and +1 narrow; its centre retains the
previous selection, with hysteresis around zero.

## HUD and IRADS cursor

A small open-centred cross on the HUD marks where the IRADS is looking. Past the
20 deg total field of view, or off the drawn HUD area, it holds at the edge toward
the sensor. A 10 mrad box marks the IRADS ground lock point once locked. This needs
the matching EFM build.

## Weapon delivery

1. `(7) Air-To-Ground Mode`, then `IRADS On/Off`. Master Arm starts SAFE.
2. Slew the IRADS and designate terrain with `Depress / Slew Stop`. POINT and RNG on
   the display show the lock state. Slewing again exits point track.
3. `IRADS Laser Arm/Safe` plus a valid designation gives code-1688 illumination.
   Laser-guided bombs need a live laser spot until impact. JDAMs take the designated
   coordinate and need no laser.
4. `Weapon Station Next / Previous` selects the store. Hold `Weapon Release (Pickle)`
   (Right Alt+Space) to give CCRP consent. The EFM opens the bay of the selected store
   only, releases one store when every release gate passes, then steps to the next loaded
   station. Press again for the next store and its bay. A bay you opened by hand stays
   open until you close it. See [docs/systems/weapon-bays.md](docs/systems/weapon-bays.md).

ALIGN TARGET means the lateral offset is too large and OUT OF RANGE means the estimated
range window is missed. The JDAM alignment limit (30 deg) and the laser-guided limit
(15 deg) are tuning assumptions. EST TOF is predicted flight time, not tracking of the
released weapon.

## Autothrottle and PAARS

`J` engages CAS HOLD at the current airspeed once airborne and `J` again disengages.
`LCtrl+J` is the A/T disconnect button and `LAlt+9` the stick disengage paddle. `LAlt+3`
selects PAARS. Details are in [docs/systems/autothrottle-paars.md](docs/systems/autothrottle-paars.md).

## Included content

This package currently includes:

- Nine liveries covering every skin, bay and door material of the exterior model
- Three quick start missions (Caucasus free flight, Caucasus SA-3 strike, Nevada night free flight) and five Nevada night training
  lessons under `Missions/Training`, all generated by `tools/missions/build_missions.py`
- All 14 pylon stores release from the bays, and all are stock DCS weapons: GBU-27,
  GBU-10 and GBU-12 (laser code 1688), GBU-31(V)1/B, GBU-31(V)3/B and GBU-32(V)2/B
  JDAMs, AGM-154A/B/C JSOW, CBU-105, Mk-82, Mk-84, and the trial AGM-65D and AGM-65E
  Mavericks.
- A 25-cell damage model, platypus exhaust heat haze with night glow, and overwing vapour
- Cockpit lighting, power, engine start and display scripts

## Development tools

- `tools/fm_bench/` flies the built EFM against the flight manual data; see its README.
- `tools/missions/` builds the missions and runs DCS store-release tests.
- `tools/cockpit/` has Layout Studio, the offline display checks, and the HUD, font and combiner generators.
- `tools/models/` builds the exterior Blender project, checks EDM exports and runs `sync_livery_materials.py`, which rebuilds the livery tables after an exterior re-export.
- `tools/textures/` is the UV, paint, export and install pipeline for the texture work; `tools/textures/legacy/` holds the retired remake scripts.
- `tools/release/package_release.py` builds the runtime ZIP.
- `tests/` holds the offline tests: `python -m pytest tests`.

## Repository layout

- `docs/displays/`, `docs/systems/`, `docs/models/`, `docs/reviews/` hold the design notes; `docs/packaging.md` covers releases.
- `blender_files/` has the Blender sources for the shipped models. `texture_sources/` has the texture source library and UV work.
- `dist/` is release output only.

## Credits

- Initial development and base mod project, including the community liveries, textures and EDM models that remain from it: `@JinxxDCS`, `@WatchBambi`
- Latest development, fixes, improvements, and new features, including the fully reworked EFM: `HalfManBear (HMB)`

## Legal / Attribution

Please keep attribution to the upstream project when redistributing or further forking this work:

- Original mod base (community liveries, textures and EDM models): [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117)
- The EFM started from [WatchBambi/DCS-F-117-EFM](https://github.com/WatchBambi/DCS-F-117-EFM) and has since been fully reworked.