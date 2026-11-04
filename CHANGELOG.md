## HUD/IRADS cursor and lock box (3 November 2026)

Needs the matching EFM build.

- **HUD/IRADS cursor.** A small open-centred cross on the HUD now marks where
  the IRADS is looking (TO 1F-117A-1, Figure 4-4 item 7). Outside the 20 deg
  total field of view, or off the drawn HUD area, its centre holds at the edge
  in the direction of the sensor. Once locked it sits on the lock point.
- **Lock box.** A 10 mrad box marks the IRADS ground lock point. The manual has
  no HUD lock box; it was added on request.
- The EFM publishes the IRADS view direction as `F117_IRADS_LOS_VALID` and
  `F117_IRADS_LOS_X/Y/Z` (world unit vector). It is invalid when the IRADS is
  off or its image has not been drawn for 0.5 s.

## Platypus exhaust heat haze and night glow (3 November 2026)

- **Heat haze.** Each engine's two old exhaust points sat 0.2 m high and inboard
  of the real slots, and were copied from another aircraft. Each platypus slot
  (2.85 m by 0.10 m, measured from the model) now feeds four narrow nozzles along
  its length. The DCS heat blur, smoke and contrails form a flat sheet behind each
  slot instead of a round plume. Flow runs aft with 8 deg outboard splay. Total
  smoke per engine is unchanged.
- **Night glow.** Two dim orange lights per slot light the slot lip and aft deck.
  Draw arguments 1002 (left) and 1003 (right) follow each engine's rpm with a
  6 s thermal lag: none below 60 %, a trace at ground idle, full at military
  power. Both arguments go over the network.

## Liveries cover the whole airframe again (3 November 2026)

- All nine liveries now texture every skin, bay and door material of the current
  exterior model. Its re-export renamed most skin materials (`Aircraft_01.006`
  and so on), so most of the airframe had kept the default texture.
- `tools/sync_livery_materials.py` rebuilds the livery tables from the model;
  rerun it after any exterior re-export. `tests/test_liveries.py` fails when
  they fall out of step.

## Engine starts on start air, two engines, ground carts (3 November 2026)

Needs the matching EFM build.

- **Two engines.** The EFM now models each engine separately: its own N2, thrust,
  start, flameout and damage. `Engine Left Start` / `Engine Right Start`
  (RAlt+Home / RCtrl+Home) and their stops work, and `Engines Start`
  (RShift+Home) starts the right engine, then the left.
- **Start air.** Each starter needs start air from the APU, the ground crew's
  air cart or crossbleed from the other running engine, and the start air feeds
  one starter at a time. Without it the cockpit shows
  `ENGINE START NEEDS START AIR - APU OR AIR CART`.
- **Start sequence.** The starter motors the core to light-off at 15 % core rpm,
  the engine lights and accelerates, and the starter disengages at 54 %,
  reaching ground idle about 30 s after the start. N2 now spools down after a
  shutdown instead of dropping to zero, and an engine still above 15 % relights
  without start air.
- **Ground carts.** `Ground Power Connect / Disconnect` (RCtrl+RShift+P) and
  `Ground Air Connect / Disconnect` (RCtrl+RShift+A), new, connect only while
  stopped on the ground. Ground power keeps the displays up through an engine
  shutdown without the APU.
- **Indications.** Engine data now follows TO 1F-117A-1 page 2-7:
  - EGT peaks at about 600 °C during a start and settles at about 420 °C at
    idle. It read 690 °C before.
  - Fuel flow is the flow the EFM actually burns: 600 lb/hr per engine during a
    start and about 790 lb/hr at idle. Before, it reported about 4,200 per engine
    at idle, in lb/hr where DCS expects kg/s.
  - Oil pressure peaks at about 85 psi and settles at 70 psi.
  - The generators come on line at 56 % core rpm instead of 50 %.

## Cold-start display power, boot and alignment (3 November 2026)

Cold starts are now dark. Previously every display was forced on at spawn. The
battery (`Electric Power Switch`, RShift+L) gates everything. With it on, the APU
(`APU Start / Stop`, new, RShift+U, about 8 s to come up) or an engine above 56 % core rpm
powers the bus. The displays boot on a staggered timeline:

1. The DEP.
2. The HUD, fading in.
3. The left CMDI.
4. The SD.
5. The right CMDI.

The CMDIs, SD and DEP show a self-test / auto-cal screen first. The boot screens
are illustrative. Attitude, heading, altitude and vertical speed start wrong and
slew to the true values with a slight overshoot. That applies to the HUD, VSD,
HSD and map.

The EFM and weapons always use true data. Hot and air starts are powered and
aligned from spawn. The cold-start HUD brightness is no longer zeroed, because
there is no HUD brightness bind yet. Lesson 1 now starts with the battery and APU.

## Every pylon store releases, and new Nevada missions (3 November 2026)

All 14 stores on the pylon list now release from the bays: the five original JDAM and
laser-guided bombs plus GBU-10, Mk-82, Mk-84, CBU-105, AGM-154A/B/C and AGM-65D/E.
Each store has a kind that sets its release rule. Unguided bombs drop on the CCRP cue.
The CBU-105 uses a wide window and needs 300 m above the target. JSOWs use the stock DCS
glide launch tables. Mavericks launch inside their range with the target in the seeker
cone. GBU-10 and AGM-65E need the laser; the AGM-65D does not.
The Maverick pylon entries now use the real DCS store IDs, so they load in the editor.
`tools/missions/store_drop_test.py` flew one release per store in DCS on 3 November.
Every store released and destroyed its target. The guided stores, Mavericks and
Mk-84 landed within 2 m of the designation; Mk-82, CBU-105 and AGM-154B within 14 m.
Mk-82 and Mk-84 drag was fitted to releases from 4,500 m at 420 kt; other heights are untested.
The four Su-25T-derived Single missions are removed. New: five Nevada night training
lessons in `Missions/Training` (cold start and navigation, laser-guided bombs, GPS
weapons, unguided and area weapons, Mavericks) and a Nevada night free-flight quick start.
The Caucasus free flight lost a stray third pylon. Missions are generated by
`tools/missions/build_missions.py` (pydcs); see `tools/missions/requirements.txt`.


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


## Point lock, auto-step and pickle update (28 October 2026)

Current build: point-pickle-v8. Final rendered camera LOS is stabilized directly
onto the saved fixed world designation after native motor/frame updates. Each
accepted native release automatically selects the next loaded supported station.
Holding pickle still permits only one accepted release; release and press again
for the next store. Weapon Release (Pickle) now uses generic commands 350/351.
Keyboard default: Right Alt + Space. Plain Space is restored to Weapon Fire.
The saved keyboard Space-to-bomb override was removed; unrelated bindings remain.
Offline tracking/store/input/delivery tests and Release x64 build pass.


## Render-stage lock and JDAM envelope update (28 October 2026)

Current build: render-dlz-v9. Native camera pose extrapolation is suppressed only
while constructing a point-locked camera or capturing its terrain intersection;
the original native timestamp is restored immediately. This addresses the stage
that could overwrite v8 cached aim. Final-render ray diagnostics are logged.
JDAM min/max release range now comes from each local weapon definition launch
tables, interpolated by height above target and true airspeed; no out-of-grid
extrapolation. MFD MIN/MAX are horizontal metres; RNG remains slant range.
Automatic store step and generic pickle work. New tracking
and release-window changes pass offline tests and need DCS confirmation.
Weapon guidance/aerodynamics were not changed; steep flight/fin motion still
needs observation after an earlier release.


## Terrain-validated IRADS lock (28 October 2026)

Current build: terrain-lock-v11. Flat-road diagnostics measured native saved
points 826Ã¢â‚¬â€œ898 m above Terrain.GetHeight. Designation now intersects a snapshot
of the rendered ray with DCS terrain in cockpit Lua, then commits a matching
validated result to the EFM. Pending/no-hit targets cannot arm laser or pass
release gates. The v10 camera-point hook remains removed. Offline checks pass.
Confirmed the v11 terrain lock works in DCS; repeated accepted points match
terrain height to the logs' printed 0.001 m precision. Separate weapon impact,
laser acquisition and fuselage visibility checks are not implied.

## OCIP display arrangement (30 October 2026)

The left CMDI now starts in IRADS EO/targeting mode. Ctrl+Shift+E toggles EO/VSD;
IRADS power still uses its existing control. The central screen shows a Harris
moving-map outline with live ownship data and a valid designated IRADS point.
The right HSD is unchanged.

- Ctrl+Shift+[ / ]: central map range decrease/increase (10, 25, 50, 100, 140 NM).
- Ctrl+Shift+M: centered/decentered north-up/track-up orientation cycle.
- Dedicated EO/VSD and map actions are under **F-117A Displays** in Controls.

The central page now follows the supplied manual map figures, with planned
waypoint/threat symbols and manual panning. Planning data is explicitly supplied
in `Cockpit/Scripts/Systems/MapMission.lua` (empty by default); automatic mission
route import and Harris-specific elevation shading remain unimplemented.
Geographic backgrounds now use the experimental common DCS chart backend. See [OCIP cockpit research](docs/ocip-cockpit-research.md)
for sources, confirmed facts, interpretation and validation limits.


The generic DCS theatre-chart backend is now enabled experimentally. It uses
an isolated common chart device, with native build checks and camera-readiness
gating. Correct chart pixels and refresh still need an in-DCS check. Disable
`Cockpit/Scripts/MFD/Indicator/Map/Charts/config.lua` to restore the fallback.
The shared view contract and native rendering findings are documented in
[native map rendering](docs/native-map-rendering.md).

## Stock JDAMs (2 November 2026)

The GBU-31(V)1/B, GBU-31(V)3/B and GBU-32(V)2/B now use the stock DCS weapons, replacing
the mod's own copies. Pylons, default payloads and bundled missions use the stock IDs. Your
own missions that use `GBU31_JDAM`, `GBU31_V3B_JDAM` or `GBU32_JDAM` need re-arming. The
release ranges are unchanged, and the GBU-31(V)1/B weighs 934 kg instead of 925 kg.
Release of all three stock JDAMs is confirmed in DCS.
