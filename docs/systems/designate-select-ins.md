# Designate Select, HUD cursor, INS, MARK and sensor update

Implements the control-stick DESIGNATE SELECT switch and what it feeds, from TO 1F-117A-1A (the OCIP
supplement). **Where the supplement and the base TO 1F-117A-1 disagree, the supplement wins**; the base is
used only where the supplement is silent. All of it is Lua in the Displays device. The EFM is unchanged.

Status: unit-tested only. None of it has been flown in DCS, and the display layouts are unchecked on glass.

## The switch

| Position | Selects | Stock command (bound to DISPLAYS) |
|---|---|---|
| Center | IRADS | `iCommandPlane_HOTAS_TargetManagementSwitchOff` (548) |
| Up | HUD cursor | `...SwitchUp` (544) |
| Left | MAP | `...SwitchLeft` (546) |
| Down, right | not used: nothing is selected | `...SwitchDown` (545), `...SwitchRight` (547) |

Bind Up / Left / Off to a hat and the switch is momentary. Bind them to buttons and it latches like the
detented switch. The keyboard profile has `RCtrl+RShift+1/2/3` for center, HUD and MAP.

`Systems/DesignateSelect.lua` routes the throttle X-Y slew and designate input (stock `Selecter*`, TDC depress
on/off and the two slew axes):

- **IRADS:** forwarded to the EFM exactly as before (10110-10114, 10119, 10120).
- **HUD / MAP:** nothing reaches the EFM. Held keys and axes are integrated in `update()` and handed to the
  cursor owner. Designate takes effect on release.
- **Leaving IRADS** sends zero for every EFM slew demand so the gimbal does not keep moving.
- **SCAN RETURN** (`iCommandSensorReset`, 1635): the EFM undesignates and recentres IRADS. In HUD it re-slaves
  the HUD cursor to the IRADS look angle; in MAP it returns the manual-mode cursor to the selected destination.

## HUD cursor

`Systems/HudCursor.lua`. A free cursor in the HUD's optical-plane coordinates, 8 deg/s at full deflection,
clamped to the 20 degree field of view and the drawn area. It shares the one HUD/IRADS cursor symbol: while the
switch is on HUD, `HUD/Device/OCIP_data.lua` draws the HUD cursor instead of the IRADS look angle. The IRADS
look angle is always published as `F117_OCIP_IRADS_LOOK_*`.

Ground point (the manual's rule): a cursor on or below the horizon takes the elevation of the current
destination, and the ray is intersected with that horizontal plane from the INS position. At or above the
horizon there are no coordinates. The point is wrong over steep terrain; that is the manual's method.

## Map

`Systems/MovingMap.lua`: LOOK and SCROLL can only be entered with the switch on MAP (leaving is always
possible). They start at the selected destination, and LOOK is centred North-up. Throttle slew moves the cursor
a quarter of the range per second. A free UPDT cursor works in auto mode (see sensor update). Stored marks are
drawn as diamonds with their number.

## INS

`Systems/INS.lua`. Navigation and the map see **true position plus a drifting bias**. IRADS, the HUD velocity
vector, weapons and the GPS-labelled IRADS coordinates stay on true data.

- Starts once the INS is aligned: from spawn on a hot start, otherwise 50 s after bus power (the heading
  alignment has settled; `Electrical.lua` publishes `F117_ALIGN_INS_DONE`). Losing power loses alignment.
- Starting error up to 0.1 nm, then drift of 0.5 to 1.0 nm/h in a random direction. **These are tuning
  constants, not from the manual** (`INS.DRIFT_NM_PER_HR`, `INS.INITIAL_ERROR_NM`).
- VSD advisory: ALIGN while aligning, INS UP once aligned (`F117_INS_ADVISORY`). DR shows after the INS alert.

## MARK

`Systems/NavUpdate.lua` with the store in `Systems/Navigation.lua`. Points 94-98 are assigned in order and
stored in the INS frame with their elevation. The remaining count shows under the MARK legend. MARK needs
the switch on IRADS or HUD and ground coordinates (IRADS lock, else the HUD cursor ground point); otherwise an X
shows over the legend. ENTR stores, CLR or MARK again exits. It is not available in manual map mode, and a
MARK activation on the ground uses up one of the five points. Marks can be selected as the TO point with the
waypoint step commands.

## Sensor update (SNSR and map UPDT)

The INS sees a sensor point at `true + bias`, so the correction is `destination - sensor point` (INS frame).
ENTR moves the INS by the correction and adds it to the running bias, which is kept as destination point 99
(a vector sum). Only the pilot's cursor placement error remains.

| Source | Needs |
|---|---|
| IRADS | switch on IRADS or HUD, an IRADS lock, the aircraft above the ground at the destination. Altitude is corrected only with the laser armed. |
| HUD | switch on HUD, no IRADS lock, cursor below the horizon |
| MAP (UPDT) | switch on MAP, an IRADS lock, auto map mode. Slew the map cursor onto the landmark, designate, ENTR. |

SNSR stays boxed until the conditions are met. The bias display (bearing, range to 99.99 nm, altitude to
99,999 ft) replaces GS/TAS on the HSD and MAP. CLR, deselecting SNSR, UPDT, or moving the switch off MAP rejects.
A correction of 120 nm or more raises POSUNR then the INS alert; both inhibit updates until CLR clears them.

New commands (no default keys, bind in Controls): `MARK Point (94-98)`, `SNSR Sensor Update`,
`Map UPDT Sensor Update`, `ENTR (Accept)`, `CLR (Reject / Clear Alerts)`. IDs 3040-3044 in `update_commands`.

## Not implemented

- **OAP** (offset select, OAP1/2): needs CDU keypad entry. SNSR always uses the current destination.
- **ALT CAL and visual update (VIS UPDT):** CDU functions.
- **TP display:** not in the mod (the supplement's "CLR not available on TP" case).
- **HUD DEST and OFFSET cues:** still placeholders.
- **A HUD ground point for weapons:** weapons use the EFM's IRADS lock only, as in the manual.

## Manual contradictions and how they were resolved

| Topic | Base TO | Supplement (used) |
|---|---|---|
| Switch LEFT | left MDI | MAP |
| Slewing the HUD cursor | warning says "down" | up only; down is not used |
| X over MARK clears | on designate, requirements met or deselect | requirements met or deselect |
| Bias display replaces | TAS / DME (HSD, TP) | TAS / GS (HSD, MAP) |
| CLR while SNSR boxed | always available | "not available on TP and HSD", yet "reject with HSD or MAP CLR": CLR works on HSD and MAP |
| OAP invalid during IRADS update | continues with an unknown error | same (OAP is not modelled) |

## Tests

`tests/test_designate_select.py`, `test_hud_cursor.py`, `test_ins.py`, `test_nav_update.py`, plus additions in
`test_navigation.py`, `test_electrical.py`, `test_ocip_hud.py`.
