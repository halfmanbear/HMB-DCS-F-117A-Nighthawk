# Clickable cockpit status and flight-manual gaps

Snapshot: 30 October 2026. Two parts:

1. **Clickable cockpit** – investigated, then put **on hold**. What exists, what
   is missing, and how to resume.
2. **Manual gap list** – what `Lockheed F-117A Nighthawk Utility Flight Manual.pdf`
   describes that the mod does not yet implement, ranked by importance.

---

## Part 1: Clickable cockpit (ON HOLD)

### Already in place

| Piece | Where |
|---|---|
| Lua cockpit devices (LIGHTS, DISPLAYS, WEAPONS, MISCFUNC, …) | `Cockpit/Scripts/device_init.lua`, `devices.lua` |
| Lua → EFM command path (`dispatch_action(nil, cmd, value)`) | `Systems/Displays.lua`; received by `ed_fm_set_command` (EFM `F_117_NightHawk.cpp`) |
| EFM → cockpit parameter path (`ed_get_cockpit_param_api`) | EFM `F_117_NightHawk.cpp` |
| Click-command ID range from 5000 (`click_cmd`) | `Cockpit/Scripts/command_defs.lua` |

The EFM needs no new plumbing. It only changes for systems it owns
(engine start, gear, master arm, laser and similar).

### Missing

1. **No `clickabledata.lua`.** No clickable definitions exist.
2. **No click zones in the cockpit EDM.** There are no `PNT_*` objects.
3. **Most controls are not separate meshes.** From `Cockpit/Shape/cockpit_f-117.dot`
   (same date as the current `Cockpit_F-117.edm`), only these are separate:
   `Switch_07`–`Switch_16`, `Gaz_handle`, `joystick`, `Pedale_Left/Right`,
   `Gears_Handle`, gauge pointers and `attitude_ball_pilot`. Everything else is
   merged into `Cockpit.001`–`Cockpit.051`.
4. **`Switch_07`–`Switch_16` have no animation argument**, so they cannot move.

Animation arguments already used in the cockpit EDM (avoid them for new switches):
6, 22, 24, 30, 32, 35, 36, 40, 41, 83, 180, 181, 523, 540, 998–1007, 1010, 1011, 5000.

### Work per control

| Layer | Where | Approx. time |
|---|---|---|
| Click zone `PNT_xxx` | Blender | ~2 min |
| Animation (separate mesh, pivot, key to argument) | Blender | 5–20 min |
| Clickable entry | `clickabledata.lua` | ~2 min |
| Behaviour | Lua device `SetCommand`, plus EFM for real systems | 5 min (lights) to hours (engine/fuel/electrics) |

Click zones work without animation. A first pass can place zones over the merged
meshes, and the switches can be animated later.

**Open item:** confirm which object type the ED Blender EDM exporter needs for
`PNT_` click zones (connector or shell) before making more than one.

### How to resume

Start with one switch, tested end to end: `Switch_07` → nav lights.

1. Blender: set the pivot of `Switch_07`, key it to a free argument (for example 100),
   add a `PNT_NAV_LIGHT` click zone and export.
2. Add `Cockpit/Scripts/clickabledata.lua` with one 2-position entry →
   `devices.LIGHTS`, argument 100.
3. Add a `SetCommand` branch in `Systems/lights_system.lua` that toggles nav lights
   and sets argument 100.
4. Check in DCS that the switch flips and the nav lights come on.

The cockpit panel inventory (below) lists what to make clickable next.

---

## Part 2: Flight manual gaps

### What the PDF is

- **TO 1F-117A-1A**, Issue B, 3 February 1992. It is the **OCIP supplement**
  (Offensive Combat Improvement Program, Service Bulletin N-2618), 87 scanned pages.
- It only describes what OCIP **changes**. Basic aircraft systems (engine start,
  fuel, electrical, hydraulics, limits, performance) are in the base manual,
  **TO 1F-117A-1**, which is **not** in this PDF. Weapons delivery and SMD are in
  **TO 1F-117A-34-1**, which is also not included.
- The page with Figure 3-1 (equipment failure alert list) is missing from the scan.
- The PDF has no text layer. OCR text is saved at `docs/reference/TO1F-117A-1A_ocr.txt`
  (two-column pages come out interleaved; check figures against the PDF).

Page references below are **PDF page / printed page**.

### Already implemented from this manual

- Basic OCIP HUD, Fig 4-4 (PDF 21 / 4-8) – `docs/hud-ocip-design.md`
- Basic VSD, Fig 4-13 (PDF 33 / 4-20) – `docs/left-vsd-design.md`
- Basic HSD, Fig 4-14 (PDF 36 / 4-23) – `docs/right-hsd-design.md`
- Autothrottle CAS hold and PAARS (PDF 15–20, 52) – `docs/autothrottle-paars.md`
- IRADS sensor display, designation, laser and weapon release (described in the
  weapons manual rather than this one)

All three displays still show dashes for navigation data (destination, range,
TTG, course, DME) because nothing supplies it. **Navigation is the main gap.**

### Ranked gap list

#### Tier 1: core OCIP functions (everything else depends on these)

| # | Feature | Manual | Current state | Size |
|---|---|---|---|---|
| 1 | **Flight plan / waypoints + destination steering** (DEST, CRS LINE, CRS SEL, MAN HDG) | PDF 44–49 / 4-31…4-36 | None. HUD destination box, HSD course pointer, RNG/TTG have validity flags waiting for a source | Days |
| 2 | **Data Entry Panel (DEP)** main menu, submenus and keypad | PDF 42–43 / 4-29…4-30, FO-3 (PDF 80–87) | None | Days |
| 3 | **Autopilot per OCIP**: CH1/DUAL/CH2, no-reference PITCH/ROLL lights, stick de-reference, paddle disconnect, coupled steering | PDF 15–17 / 4-2…4-4 | EFM has FC3-style alt / attitude / alt+roll hold only | 1–2 days |
| 4 | **Autothrottle** (CAS/Mach/GS/AOA hold, A/T DISC light, inboard throttle disengage button) | PDF 15–17, 52 / 4-2, 4-39 | **Done 30 Oct 2026** (CAS hold; Mach/GS/AOA need the DEP) – `docs/autothrottle-paars.md` | – |
| 5 | **TACAN and ILS steering** on HUD (Fig 4-5, 4-6), VSD (loc/GS indicators) and HSD (bearing pointer, DME) | PDF 23–24, 50–51 / 4-10…4-11, 4-37…4-38 | None | 1–2 days |
| 6 | **Track select (TRK SEL)** / destination change and auto-sequencing (within 3000 ft, range increasing) | PDF 44, 55 / 4-31, 4-42 | None | Part of #1 |

#### Tier 2: high-value additions once navigation exists

| # | Feature | Manual | Size |
|---|---|---|---|
| 7 | **HUD declutter switch** NORM / DCLTR1 / DCLTR2 (exact symbol removal lists) | PDF 23 / 4-10 | Hours (easy win) |
| 8 | **PAARS / ARS** automatic recovery: wings level, small positive pitch; response-map sectors; inhibit conditions; minimum pullout altitude in red on VSD | PDF 19–20 / 4-6…4-7 | **Done 30 Oct 2026** – `docs/autothrottle-paars.md` |
| 9 | **CMDI format switching** (lower legends HSD / MAP / STAT / SMD / DFRM; IRADS on left CMDI only) | PDF 24–25 / 4-11…4-12 | Hours–1 day |
| 10 | **FAAD** pitch ladder on the sensor display (upper right), and FAAD backup mode | PDF 39–40 / 4-26…4-27 | Hours |
| 11 | **VSD extras**: MEA switch, velocity-vector switch, pitch-ladder selector, FMS status letters (H/V/S/T, C when coupled), altitude/airspeed carets, ARS readout | PDF 31–34 / 4-18…4-21 | 1 day |
| 12 | **Pre-planned modes** HNAV / VNAV / SNAV / TOT / TOP | PDF 52–54 / 4-39…4-41 | Days |
| 13 | **Out-of-corridor warning and MEA breakaway X** cue | PDF 24, 42 / 4-11, 4-29 | Hours (after #1) |
| 14 | **Master caution, annunciator panel, equipment failure alerts** | PDF 13, 16 / 3-2, 4-3 | 1 day + base manual needed |

#### Tier 3: large or low return

| # | Feature | Manual | Note |
|---|---|---|---|
| 15 | Moving map DMAP/PMAP (ranges 10/25/50/100/140 nm, 4 orientations, threat symbols, elevation bands) | PDF 25–29 / 4-12…4-16 | Very large |
| 16 | EDIT display (flight-plan table) | PDF 29–30 / 4-16…4-17 | Needs #1, #2 |
| 17 | STATUS display (maintenance / mission / SMS fault formats), Image Data Frame (DFRM) | PDF 32, 37–38 / 4-19, 4-24…4-25 | Mostly cosmetic |
| 18 | Sensor / visual / IRADS-map updates, MARK points 94–98, altitude calibration | PDF 56–58 / 4-43…4-45 | Only useful if INS drift is modelled |
| 19 | Return-to-Base degraded mode and computer failure matrix | PDF 39, 41 / 4-26, 4-28 | Failure modelling |
| 20 | VTR recorder (RCRD / STBY), TM/SRCH | PDF 55 / 4-42 | Cosmetic / weapons manual |
| 21 | Normal procedures: FCS prestart BIT, APU start (battery → BIT → APU → wait 3 s after APU OFF light) | PDF 10–11 / 2-1…2-2 | Needs APU/EPU/electrics that the EFM does not model; base manual needed |
| 22 | Emergency procedures: engine fire, oil pressure, starter engaged, AMAD oil, ECS overheat, fuel pressure low, INS failure → DR mode | PDF 12–13 / 3-1…3-2 | INS-failure W symbol is already in the HUD |

### Concrete values to use when implementing

**Keypad entry limits** (FO-3, PDF 83):

| Parameter | Low | High |
|---|---|---|
| TRK CHG | 1 | 99 |
| DEST STR | 1 | 94 |
| CAS | 140 kt | 525 kt |
| MACH | 0.20 | 0.90 |
| AOA | 7.0 | 9.5 |
| MAN HDG / ILS / TCN / CRS SEL | 0 | 360 |
| ELEV, OA1/OA2 ELEV | −2000 ft | 99,900 ft |
| MEA, ALT | 1000 ft | 99,900 ft |
| VRT VEL | −99,900 ft/min | 99,900 ft/min |
| TOT | 00:00:00 | 23:59:59 |
| WIND DIR / VEL | 0 / 0 kt | 360 / 999 kt |
| FUEL | 0 lb | 99,900 lb |

**Steering and autopilot limits:**
- Autothrottle climb angle ≤ 12°, descent angle ≤ 18° (PDF 43 / 4-30).
- Roll commands ≤ 50° bank in navigation modes; ≤ 30° in TACAN; ≤ 35° during ILS capture (PDF 44, 50, 51).
- ILS: capture starts at ≤ 3.4 dots; capture inhibited for 6 s after mode select;
  pitch command +12.5° / −2.5°; bank limit drops to ±10° after 30 s below 5° commanded bank (PDF 51 / 4-38).
- New starting point is computed when cross-track deviation exceeds 0.10 nm (PDF 45 / 4-32).
- HSD deviation dots: INS ±3/±6 nm, TACAN ±5°/±10°, ILS ±1.25°/±2.5°, attack ±3/±6 nm (PDF 35, 37).
- Autopilot de-references an axis when the stick moves more than ±0.04 in (PDF 17 / 4-4).
- Safe corridor includes a 5 nm radius around each destination point (PDF 42 / 4-29).

**Discrepancy to check:** the VSD AOA scale marks optimum approach AOA at **9.5°**
(PDF 31 / 4-18), and the DEP limits AOA to 7.0–9.5. The HUD approach bracket
currently uses a **12°** optimum (`docs/hud-ocip-design.md`, already flagged as
needing validation).

### Cockpit panel inventory (FO-1, PDF 69–74)

Use this list to choose clickable targets when Part 1 resumes.

- **Left side panels:** left circuit breaker panel; weapon bay ground switch and
  master test panel; cockpit lights control panel; external lights control panel;
  seat adjust switch.
- **Left console:** engine data events switch; EPU/APU panel; laser control panel;
  throttle panel; autopilot/autothrottle control panel; canopy/seat ejection handle;
  low-observable recorder control panel; AMAD/EPU ground control panel; anti-g valve;
  weapon interface panel; PALAMAC (DCU-201) weapons controller; FCS panel;
  fuel control panel.
- **Main instrument panel (66 items), main groups:** HUD and DEP (with DEP reload
  button); left/right CMDIs; sensor display and sensor display control; auxiliary
  navigation panel; armament control panel; HSI, ADI, standby ADI, altimeter,
  airspeed, VVI, AOA, accelerometer, radar altimeter, clock, turn-and-slip; engine
  performance indicator, fuel quantity, flight/utility hydraulic pressure, oxygen
  quantity, cabin altimeter; annunciator panel and reset; master caution; A/P
  pitch/roll, A/P DISC, A/T DISC lights; left/right engine and APU fuel cutoff
  switchlights; landing gear handle, gear lights, horn silence, emergency gear
  handle; landing/taxi light switch; brake anti-skid, brake select and emergency
  brake; tailhook switchlight; drag chute handle and stow reset; air-refuelling
  ready/latch/disconnect/receptacle lights; UHF and ICS panels; pedal adjust handle;
  canopy unsafe, blow-in door, antenna down, RLS down, inlet grid wiper, marker
  beacon, IFF mode 4, dual CS, beta indicator lights.
- **Right console:** AHRS control; oxygen control; IFF; TACAN; ILS/marker beacon;
  antenna control; ECS control; EDTM interface; utility light; electrical fault
  indicator; KY-58 (provisions only); IRADS panel; RLS panel; computer panel;
  INS control and display unit (CDU); electrical panel; AHRS fast erect.
- **Right side panels:** emergency air refuelling handle; miscellaneous switch panel;
  anti-ice/de-ice panel; canopy manual crank; right circuit breaker panel.

### Recommended order

1. HUD declutter switch (#7): small, self-contained, gives a visible result.
2. Flight plan + destination steering (#1) from DCS mission waypoints. This fills
   the empty HUD/VSD/HSD fields that are already drawn.
3. TACAN/ILS steering (#5).
4. DEP (#2) and OCIP autopilot/autothrottle (#3, #4).
5. PAARS (#8).
