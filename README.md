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
- `IRADS FOV - Narrow` / `IRADS FOV - Wide` (or the `IRADS FOV (Wide / Medium / Narrow)` axis)
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
sensor. The zoom axis uses -1 = wide, 0 = medium and +1 = narrow, with hysteresis.
The unsupported `Target Box Size` axis has been removed. `DLIR MFD Overlay Toggle`
is available for keyboard and joystick assignment.

Cockpit Lua development copies are maintained in the EFM repository's
`Cockpit/Scripts` directory and deployed to the same paths in this mod. IRADS
motion and zoom are handled by the EFM; cockpit Lua does not redispatch them.

The 28 October camera correction removes the invalid registration of `avTVSensor`
as an `avDevice`. A private camera-indicator vtable bridges `get_camera()` to the
native sensor's exported `fill_camera()`, so rendering consumes its optical zoom
and gimbal pose. Native exports and the virtual slot are checked before installing
the bridge. This integration still needs a fresh DCS session to verify.

`IRADS On/Off` now uses command 87 and gates the feed; the overlay toggle controls
text and symbols only. `ARM` means the laser is armed. `LASE` means the EFM has a
live native laser spot; automatic lasing requires a designation and an active
post-release laser window. Arming alone does not emit a laser.

The sensor axes target the DISPLAYS cockpit device (7), using actions 3001/3002/3003.
Displays forwards signed values once on custom EFM commands 10119/10120/10121.
The former direct axes 2110/2111/2112 and 20110/20111/20112 remain DLL aliases.
Saved local bindings were migrated to the new device signatures without changing their assigned axes.
Keyboard and analog slew now scale with optical FOV: native multiplier = 60 × 1.4 / zoom.
Wide (1.4×) uses 60, Medium (10×) uses 8.4 and Narrow (80×) uses 1.05.
Wide is 6× faster than the previous v4 rate; Narrow provides finer adjustment.
Analog deflection remains proportional with a 5% deadzone, and held directions update immediately when zoom changes.
A held keyboard direction takes priority over its analog axis, so centering that axis cannot cancel keyboard motion.
The user confirmed live video, keyboard motion and the v4 TDC axis route in DCS.
The new fov-slew-v5 speed tuning still needs a simulator check.
Existing saved F-117 profiles on this workstation were backed up and migrated,
including inconsistent zoom signatures and the undefined power command.
Keyboard and joystick FOV signatures now match so DCS can combine each into one row.

## Included content

This package currently includes:

- Multiple liveries
- Quick start and single missions
- Custom weapons definitions for supported stores
- Cockpit lighting and basic aircraft systems scripts

## Credits

- Initial development, EFM, EDMs, and base mod project: `@JinxxDCS`, `@WatchBambi`
- Latest development, fixes, improvements, and new features: `HalfManBear (HMB)`

## Legal / Attribution

Please keep attribution to the upstream projects when redistributing or further forking this work:

- Original Mod fork base: [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117)
- Original EFM fork base:[WatchBambi/DCS-F-117-EFM](https://github.com/WatchBambi/DCS-F-117-EFM).


## IRADS designation and delivery update (28 October 2026)

The installed delivery-v6 build adds actual point-lock/release status, Master Arm / Safe,
and Weapon Station Next/Previous. Master Arm starts SAFE. Designate terrain with TDC Depress;
POINT and RNG reflect EFM lock state. Active slew exits point track.
Laser Arm plus a valid powered designation automatically creates code-1688 illumination.
JDAM launches receive the designated world coordinate snapshot and do not require laser.
LGB release requires a live laser spot; retain illumination until impact.
Hold CCRP consent: the EFM opens the bay and releases one supported selected store only
when the release gates pass and DCS accepts the launch. No untargeted Lua fallback remains.
The selected station/profile refreshes for mixed loads, depletion and rearm.
EST TOF is predicted flight time, not confirmed tracking of the released weapon or impact.
Delivery behavior still needs a live DCS check. See local F117-mod-status.html for findings.


## Guided release-zone correction (28 October 2026)

The current guided-zone-v7 build separates the ballistic CCRP cue from the provisional
guided-store release window. The old narrow unguided impact gate could hold guided
weapons indefinitely outside the flight path. ALIGN TARGET now identifies excessive
lateral offset; OUT OF RANGE identifies the estimated range window. Turn toward the
designated target and hold consent while approaching. JDAM uses an approximate
30-degree alignment limit, LGB 15 degrees. These are tuning assumptions pending
live DCS guidance/release validation. All other release gates remain active.
See _irads_zone_fix_20261028/README.md for limits, diagnostics, tests and rollback.


## Point lock, auto-step and pickle update (28 October 2026)

Current build: point-pickle-v8. Final rendered camera LOS is stabilized directly
onto the saved fixed world designation after native motor/frame updates. Each
accepted native release automatically selects the next loaded supported station.
Holding pickle still permits only one accepted release; release and press again
for the next store. Weapon Release (Pickle) now uses generic commands 350/351.
Keyboard default: Right Alt + Space. Plain Space is restored to Weapon Fire.
The saved keyboard Space-to-bomb override was removed; unrelated bindings remain.
Offline tracking/store/input/delivery tests and Release x64 build pass. DCS visual
tracking and auto-step checks are pending; the user confirmed v7 release worked.
See _irads_tracking_store_fix_20261028/README.md for tests and rollback.


## Render-stage lock and JDAM envelope update (28 October 2026)

Current build: render-dlz-v9. Native camera pose extrapolation is suppressed only
while constructing a point-locked camera or capturing its terrain intersection;
the original native timestamp is restored immediately. This addresses the stage
that could overwrite v8 cached aim. Final-render ray diagnostics are logged.
JDAM min/max release range now comes from each local weapon definition launch
tables, interpolated by height above target and true airspeed; no out-of-grid
extrapolation. MFD MIN/MAX are horizontal metres; RNG remains slant range.
The user confirms automatic store step and generic pickle work. New tracking
and release-window changes pass offline tests and need DCS confirmation.
Weapon guidance/aerodynamics were not changed; steep flight/fin motion still
needs observation after an earlier release. See _irads_geometry_dlz_fix_20261028/README.md.


## Terrain-validated IRADS lock (28 October 2026)

Current build: terrain-lock-v11. Flat-road diagnostics measured native saved
points 826–898 m above Terrain.GetHeight. Designation now intersects a snapshot
of the rendered ray with DCS terrain in cockpit Lua, then commits a matching
validated result to the EFM. Pending/no-hit targets cannot arm laser or pass
release gates. The v10 camera-point hook remains removed. Offline checks pass. The user
confirmed the v11 terrain lock works in DCS; repeated accepted points match
terrain height to the logs' printed 0.001 m precision. Separate weapon impact,
laser acquisition and fuselage visibility checks are not implied. See
_irads_terrain_lock_fix_20261028/README.md for evidence, limits and rollback.
