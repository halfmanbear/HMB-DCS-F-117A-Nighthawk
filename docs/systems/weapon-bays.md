# Weapon bays

The F-117A has two weapon bays side by side, each with its own door and trapeze. Station 1 is the
left bay and station 2 is the right bay. The EFM drives each bay separately, so one door can open
for the selected store, or both can open together.

## What the manual says

Sources are TO 1F-117A-1 (`docs/reference/TO1F-117A-1_ocr.txt`). The supplement (TO 1F-117A-1A) has
only a panel callout ("weapon bay ground switch and master test panel") and no operating text. The
detailed procedures are in the Utility Nonnuclear Weapons Delivery Manual (TO 1F-117A-34-1), which
isn't in `docs/reference`.

- **Two bays, doors and trapezes** (Section I, PDF pages 83 to 86). "The weapons bay doors can be
  operated together or separately." The trapeze can extend only if its safety pin is removed.
- **BAY DOOR-SEL JETT selector** on the armament control panel (ACP), five positions:
  - `AUTO/CLOSE`: the door opens and the trapeze lowers automatically from the attack mode and
    Master Arm. They return on weapon release or when Master Arm goes to SAFE.
  - `L OPEN` / `R OPEN`: that bay opens directly, with Master Arm ARM or SAFE. Weapon release does
    not close it. Only `AUTO/CLOSE` does.
  - `L JETT` / `R JETT`: past a detent (pull the switch out), enables the JETT button to release
    the store unarmed.
- **Attack modes** (Section IV, PDF page 265): Level and Loft open the door before release and close
  it on weapon-away. Manual release opens when selected and closes on weapon-away (the OCR is
  inconsistent about manual mode in Section I).
- **Ground**: the ACP is inhibited with weight on wheels. The GND CONT DR switch on the master test
  panel (OPEN, OFF, CLS) opens both doors to 90 degrees, slowly. In the air they open to 91 degrees
  at the fast rate. The before-taxi checklist (PDF page 97) says the selector must be at
  `AUTO/CLOSE` or a door opens immediately after takeoff.
- **Lights**: an amber door light and a green trapeze light per bay. A light flashes in transit and
  stays on when the door is open or the trapeze is down.
- **Flight**: one or two doors open is limited to 470 KCAS / 0.90 M (Section V, Figure 5-6). A note
  on that figure says "TRAP DOWN IS PROHIBITED", and the OCR doesn't make its scope clear. Opening
  a single door "has effects similar to gear extension" (Section VI, page 6-4). For the gear the
  manual gives about one degree of nose-left sideslip that the pilot can retrim.

## Design

| Layer | Behaviour |
|---|---|
| Model | Left bay on arg 27, right bay on arg 28. Each opens its door over 0 to 0.7 and lowers its trapeze over 0.6 to 1. `Pylon1` is under 27 and `Pylon2` under 28. The lights in the bay switch on at 0.4. Nothing is animated by arg 26. |
| EFM | One servo per bay, two seconds for the full travel. Draw args 27 and 28, and arg 26 reads the larger of the two. DCS draws the stores only while the standard bay arg 26 is open, so without it the store of an open bay vanished whenever the other bay was shut (seen in DCS on 2026-11-08). Positions are published as `F117_BAY_L` and `F117_BAY_R`. `net_animation` carries 26, 27 and 28. |
| Pickle | Opens the bay of the selected store only. The store is released when that bay is fully open. The bay then closes one second after release. After a release `Weapons.lua` steps to the next loaded station, so the next pickle opens the other bay, and the first bay's close timer keeps running. |
| Manual | A bay opened by hand is never closed by a pickle. Any manual bay command, a change of Master Arm and a session restart end an automatic sequence: the doors the pickle opened close. |
| Drag and yaw | Bay drag is shared between the bays and totals 0.015 with both open, as before. A bay open more than the other adds a yaw term sized for one degree of sideslip, toward the open side. The size is from the manual, and the sign is a choice (the extra drag on that side). |
| Lights | `Systems/bomb_bay.lua` turns each bay position into `F117_BAY_L_DOOR`, `F117_BAY_L_TRAP`, `F117_BAY_R_DOOR` and `F117_BAY_R_TRAP`: 0 off, 1 in transit (flashing), 2 steady. No cockpit model uses them yet. |

## Controls

| Command | Default key | ID | Acts on |
|---|---|---|---|
| Bomb Bay Doors Toggle (Both) | LShift+T | 10100 | Both bays: closes them if either is open or opening, otherwise opens them |
| Bomb Bay Door Toggle (Selected Store) | LShift+LCtrl+T | 10130 | The bay of the station chosen with `Weapon Station Next / Previous` |
| Bomb Bay Door Toggle (Left) | LShift+LAlt+T | 10131 | Station 1 |
| Bomb Bay Door Toggle (Right) | LShift+RAlt+T | 10132 | Station 2 |

Each toggle reverses a bay that is still travelling. 10101 and 10102 (open and close both) still
exist in the EFM for tools and future panels.

## Not modelled

- The ACP selector positions, the jettison detent and button, and the master test panel ground
  switch. The commands above stand in for the selector until the clickable cockpit resumes.
- The ground inhibit (the commands work on the ground), slow ground-speed doors and trapeze pins.
- The 470 KCAS door-open limit and the hydraulic supply.

## Checking a change

- `python -m pytest tests/test_weapon_bays.py` checks command IDs, bindings, light states and (with
  the EFM checked out) the EFM's constants.
- The EFM release logic is tested by `tests/weapon_delivery_regression.py` in the EFM repository.
- `tools/models/split_weapon_bays.py` makes the model change in a Blender scene and checks that
  every part keeps its pose and that each bay moves on its own argument.
  `tools/models/check_edm_export.py` then checks the exported model against the previous one, and
  that `Pylon1` and the left door are on 27 only and `Pylon2` and the right door on 28 only.
- `python tools/missions/bay_shots.py` flies a level test in DCS with a store on each pylon, steps
  through both bays open, each bay closed in turn and both closed, and saves screenshots and the
  arg values to `tools/missions/results/bays/`. Close DCS first.
