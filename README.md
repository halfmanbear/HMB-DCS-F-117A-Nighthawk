# F-117A Nighthawk for DCS

A community rework of [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117),
with a fully reworked External Flight Model, OCIP III displays, IRADS targeting and internal weapon delivery.

[Community Discord](https://discord.gg/qj6wz48jAn) · [EFM source](https://github.com/halfmanbear/HMB-DCS-F-117A-EFM)

## Install

Download the latest `.zip` from Releases and extract it to:

```text
Saved Games/DCS/Mods/aircraft/F-117-NightHawk
```

For older Open Beta installations, use `Saved Games/DCS.openbeta/Mods/aircraft/` instead.

## Controls and weapon delivery

Open DCS Controls for `F-117-NightHawk`. Find the bindings under
`F-117A Essential System Controls` and `F-117A IRADS`; select `Axis Commands`
in the `Adjust Controls` dropdown for axes. Bind or verify the following:

| Purpose | Binding | Default key / setup |
|---|---|---|
| Sensor power | `IRADS On/Off` | O or LCtrl+I; toggle |
| Select IRADS for TDC control | `Designate Select - Center (IRADS)` | RCtrl+RShift+1 |
| Slew the sight | `TDC Slew Horizontal` and `TDC Slew Vertical` | Bind both slew stick axes |
| Slew without axes | `Throttle Designator Controller - Up` / `Down` / `Left` / `Right` | `;` / `.` / `,` / `/` |
| Designate a terrain point | `Throttle Designator Controller - Depress / Slew Stop` | Enter; press and release |
| Clear and recentre | `IRADS Scan Return / Undesignate` | Verify or assign in your profile |
| Field of view | `IRADS FOV - Wide` / `IRADS FOV - Narrow` | `[` / `]`; or bind `IRADS FOV (Wide / Narrow)` axis |
| Arm weapons | `Master Arm` / `Master Safe` | Bind both; starts SAFE |
| Arm the laser | `IRADS Laser Arm` / `IRADS Laser Safe` | Bind both for laser-guided stores |
| Select a store | `Weapon Change` (stock) / `Weapon Station Previous` | Verify or assign in your profile |
| Release consent | `Weapon Release (Pickle)` | RAlt+Space; use this for automatic bay operation |

The Throttle Designator Controller (TDC) slews and designates. **Designate Select**
chooses what receives those inputs: IRADS, HUD or MAP. IRADS is selected initially.
Use `Designate Select - Center (IRADS)` to return after selecting HUD or MAP;
“Center” selects IRADS, rather than centring the sight. You only need to reselect it
when changing control from another display.

1. **Prepare.** Select the loaded store, check it on the VSD, and command
   `Master Arm`. IRADS is on at mission start; use `IRADS On/Off` only if you have
   switched it off.
2. **Aim.** With TDC control on IRADS, slew onto the target terrain below the horizon.
   Use wide FOV to find the target and narrow FOV to refine your aim.
3. **Designate.** Press and release TDC depress (`Enter`). `SRCH` changes to `CUED`
   and a HUD box marks the terrain coordinate. Range reads `ER` without laser
   illumination and `LR` with it.
4. **Illuminate if required.** For laser-guided stores, command `IRADS Laser Arm`.
   A valid designation provides code-1688 illumination when the laser can fire:
   `AF` means armed and firing; `AX` means designated but not firing. Maintain
   designation and illumination until impact. JDAMs use the coordinate and need no laser.
5. **Release.** Fly toward the point and hold `Weapon Release (Pickle)` for CCRP
   consent. The selected bay opens automatically and one store releases when the
   release conditions are met. After weapon-away, release pickle, then press again
   for the next store. Use `Weapon Release (Pickle)` for this procedure; `Weapon Fire`
   does not provide automatic bay operation.

To acquire a new point, use `IRADS Scan Return / Undesignate` to clear and recentre.
TDC depress also clears an existing designation; slewing exits point track.
`IRADS Laser Safe` stops illumination.

Manual bay overrides are optional. A bay opened manually stays open until you close it:

| Binding | Default key |
|---|---|
| `Bomb Bay Doors Toggle (Both)` | LShift+T |
| `Bomb Bay Door Toggle (Selected Store)` | LShift+LCtrl+T |
| `Bomb Bay Door Toggle (Left)` | LShift+LAlt+T |
| `Bomb Bay Door Toggle (Right)` | LShift+RAlt+T |

Also bind `Drag Chute` for shorter-field landings and `Refueling Hatch` for air refuelling.
See [weapon bay operation](docs/systems/weapon-bays.md) for details.

## Cold start

1. Turn on `Electric Power Switch` (RShift+L) for battery power.
2. Start the APU with `APU Start / Stop` (RShift+U); allow about 8 seconds.
   It provides display power and engine start air.
3. Command `Engines Start` (RShift+Home). The right engine starts first, then the
   left uses crossbleed air. Allow about 30 seconds per engine to reach ground idle.
4. Wait for the displays to boot and instruments to align: about 30 seconds for
   attitude and 50 seconds for heading. Once the engines run, the APU can be stopped.

For individual starts, use `Engine Left Start` (RAlt+Home) or `Engine Right Start`
(RCtrl+Home). The matching End keys stop each engine; `Engines Stop` (RShift+End)
stops both.

Alternatively, connect ground power with `Ground Power Connect / Disconnect`
(RCtrl+RShift+P) and start air with `Ground Air Connect / Disconnect` (RCtrl+RShift+A).
Ground power alone cannot supply start air. Without start air, the start is refused
with `ENGINE START NEEDS START AIR`. Carts connect only while stopped on the ground
and disconnect when you taxi away.

Engine generators supply power above 56% core rpm. The starter lights the engine
at 15% and disengages at 54%; an engine still turning above 15% can relight without
start air. Typical start EGT peaks near 600°C and settles near 420°C at idle;
oil pressure peaks near 85 psi and settles near 70 psi. Start fuel flow is
600 lb/hr per engine (TO 1F-117A-1, page 2-7).

The displays boot in sequence: DEP, HUD, left CMDI, SD, right CMDI. Self-test and
calibration screens are illustrative. Without APU or ground power, shutting down
the engines makes the displays go dark. Hot and air starts begin powered and aligned.

## Displays and flight aids

The default layout is **left colour VSD | centre green IRADS | right colour MAP**.
Under `F-117A Displays`, choose VSD, grayscale EO/IRADS, MAP or HSD on the left CMDI,
and MAP, HSD or VSD on the right. Ctrl+Shift+E toggles left EO/VSD. Changing format
preserves sensor power, pointing and designation. Map terrain imagery depends on
the configured chart source being available.

The HUD's open-centred cross shows the IRADS look direction and holds at the edge
when outside the HUD's 20° field of view or drawn area. A 10 mrad box marks the
designated ground point; this requires the matching EFM build. The IRADS FOV axis
uses -1 for wide and +1 for narrow; its centre retains the previous selection.

For HUD/MAP cursors, MARK points and INS updates, see
[Designate Select and INS](docs/systems/designate-select-ins.md).
Map LOOK and SCROLL require `Designate Select - Left (MAP)`.

For autothrottle, `J` engages CAS HOLD at the current airborne airspeed; press again
to disengage. `LCtrl+J` disconnects A/T, `LAlt+9` operates the stick disengage paddle,
and `LAlt+3` selects PAARS. See [autothrottle and PAARS](docs/systems/autothrottle-paars.md).

## Included content

- Nine liveries covering the exterior model, bays and doors.
- Three quick start missions: Caucasus free flight, Caucasus SA-3 strike and Nevada
  night free flight; plus five Nevada night lessons under `Missions/Training`.
- Fourteen stock DCS stores: GBU-27, GBU-10 and GBU-12 (laser code 1688);
  GBU-31(V)1/B, GBU-31(V)3/B and GBU-32(V)2/B JDAMs; AGM-154A/B/C JSOW;
  CBU-105, Mk-82, Mk-84; and trial AGM-65D/E Mavericks. All release from the bays.
- A 25-cell damage model, platypus exhaust heat haze with night glow, overwing vapour,
  cockpit lighting, power and engine start systems.

## Development

| Location | Contents |
|---|---|
| `tools/fm_bench/` | EFM checks against flight manual data; see its README |
| `tools/missions/` | Mission generation (`build_missions.py`) and DCS store-release tests |
| `tools/cockpit/` | Layout Studio, offline display checks, HUD/font/combiner generators |
| `tools/models/` | Exterior Blender build, EDM export checks, livery table rebuild (`sync_livery_materials.py`) |
| `tools/textures/` | UV, paint, export and install pipeline; retired scripts in `legacy/` |
| `tools/release/package_release.py` | Runtime ZIP packaging |
| `tests/` | Offline checks: `python -m pytest tests` |
| `docs/` | Display, system, model and review notes; [release packaging](docs/packaging.md) |
| `blender_files/`, `texture_sources/` | Model sources and texture source library |
| `dist/` | Release output |

## Credits

- Initial development and base mod project, including the community liveries, textures and EDM models that remain from it: `@JinxxDCS`, `@WatchBambi`
- Latest development, fixes, improvements, and new features, including the fully reworked EFM: `HalfManBear (HMB)`

## Legal / Attribution

Please keep attribution to the upstream project when redistributing or further forking this work:

- Original mod base (community liveries, textures and EDM models): [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117)
- The EFM started from [WatchBambi/DCS-F-117-EFM](https://github.com/WatchBambi/DCS-F-117-EFM) and has since been fully reworked.