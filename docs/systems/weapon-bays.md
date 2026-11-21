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
| Model | Left bay on arg 904, right bay on arg 905. Each opens its door over 0 to 0.7 and lowers its trapeze over 0.6 to 1. Both also animate from standard arg 26, with inverse motion on 906. When the EFM supplies 906 = 26, the shared motion cancels and only the individual positions apply. With only 26 supplied, both doors and trapezes move together, including the pylon connectors. Interior lamps follow 26 and switch on at 0.4. Bay size is under [Bay size and store fit](#bay-size-and-store-fit). |
| EFM | One servo per bay, two seconds for the full travel. Draw args 904 and 905, with 26 and 906 both reading the larger of the two. DCS draws the stores only while standard arg 26 is open. Positions are published as `F117_BAY_L` and `F117_BAY_R`. `net_animation` carries 26, 904, 905 and 906; the left fan's network slot was reassigned to stay within 32 entries. |
| Pickle | Opens the bay of the selected store only. The store is released when that bay is fully open. The bay then closes one second after release. After a release `Weapons.lua` steps to the next loaded station, so the next pickle opens the other bay, and the first bay's close timer keeps running. |
| Manual | A bay opened by hand is never closed by a pickle. Any manual bay command, a change of Master Arm and a session restart end an automatic sequence: the doors the pickle opened close. |
| Drag and yaw | Bay drag is shared between the bays and totals 0.015 with both open, as before. A bay open more than the other adds a yaw term sized for one degree of sideslip, toward the open side. The size is from the manual, and the sign is a choice (the extra drag on that side). |
| Lights | `Systems/bomb_bay.lua` turns each bay position into `F117_BAY_L_DOOR`, `F117_BAY_L_TRAP`, `F117_BAY_R_DOOR` and `F117_BAY_R_TRAP`: 0 off, 1 in transit (flashing), 2 steady. No cockpit model uses them yet. |

## Bay size and store fit

### Replay and AI fallback (2026-11-21)

The previous model used 27/28 only, so an AI or replay driving only DCS's standard
bay argument 26 could release stores through closed doors. The replacement uses
904/905/906, absent from both the local `dcs-opensource-modding-guide` reserved
argument list and the [older animation list](https://dcs-modding-guideline.fandom.com/wiki/Animation_Arguments_for_Aircraft).
The latter lists 27 as country and 28 as right afterburner, but warns its entries
are unverified; a DCS overwrite of those arguments has not been established here.

`tools/models/weapon_bay_replay.py` applies the animation-only conversion after
the bay split/enlargement export. It checks 441 asymmetric EFM positions and 101
arg-26-only positions per transform. Old tracks that contain only 26 can show
paired opening; missing individual bay information cannot be recovered from 26.
AI likewise opens both bays through DCS's standard channel, without cockpit Lua.
The model and EFM DLL must be updated together for independent player motion.

The 2026-11-21 DCS bay-shot flight and its `.trk` replay both passed all six
states (closed, both open, right only, both open again, left only, closed).
Replay used `bay_shots.py --replay <track>` with no flight or bay commands.
Screenshots and logs are in `tools/missions/results/bays/` and `bays_replay/`.
The AI Mk-82 check (`tools/missions/ai_bay_test.py`) also opened arg 26 to 1,
released `Mk_82` with arg 26 = 1, then closed it. Its custom args 904/905/906
stayed at zero throughout, verifying the standard-channel fallback. Results are
in `tools/missions/results/bays_ai/ai.log`.

The focused bay/damage suite passes (16 tests). The wider weapon-delivery script
passes its release-gate checks but its separate native-cockpit contract stub
does not compile (`Cc_cockpit_context_layout` missing). The Lua-copy audit also
reports pre-existing differences in device_init, MFD_indication_page, Electrical,
and lights_system; the bay Lua copy matches. Those files were not changed here.

Manual Figure 2-5 (ground clearance) marks the bay from FS 348 to FS 531, 4.65 m. Its leader lines run
to the inner side of the zigzags at the bay ends, so these are the bay's inside ends. The model's gear
sits at the manual's stations (nose axle FS 288 at x 5.09, main axle FS 503 at x -0.30, 212 in apart
against 215), so FS 348 and 531 fall at x 3.60 and -1.04.
The original model's doors ran from 2.91 to -0.95, and its bay was too shallow for a 2,000 lb store
(0.46 m across) between the trapeze beam and the closed door.

A local Blender script (the bay enlargement, kept outside the repository) changes the model to match:

- The bay's end walls are at x 3.600 and -1.040 (FS 348 and FS 531): 4.65 m between them. The
  interior is 0.877 m longer at the front and 0.242 m longer at the back than the original. Only a 5 mm
  slice at each split is stretched, so the walls stay straight.
- The doors reach past the walls by as much as the original's did, so their tooth tips are at x 3.734
  and -1.147 and they and their collision cells are 4.88 m long, at full width to the front. Ahead of x 3.24
  the belly's flat facet meets an angled one along the body line (from x 4.92 on the centreline to
  x 1.80 at y 1.78). Outboard of it the doors and the edge of the opening fold onto the angled facet,
  so the front outboard teeth run onto it with the same seam as the others.
- Each end of each door has six sawtooth teeth, as on the aircraft (photos in
  `docs/reference/ExteriorImages/BAY DOORS`), where the model had four. They are copies of the model's
  own teeth, the same at both ends: 0.12 m apart and 0.086 m deep. The seal band inset along their
  edges on the inner panel is scaled with them.
- The trim at each end of the opening moves with the doors: the sawtooth's walls, and the flange plate
  behind it that closes off the space between the teeth and the bay's end wall. Only the flat outer
  belly is cut to the new opening. Its paint and shading are kept from the original surface.
- The roof, both trapezes and so the pylon connectors are 0.18 m higher (pylon y 0.117).

Each store's `attach_point_position` in `F-117-NightHawk.lua` was chosen by sweeping its carried shape
through the whole door and trapeze cycle against the model. The sweep checks the bay walls, the
trapeze beam, the doors and the skin. DCS draws stores by their own `AttachPoint` connector unless
`attach_point_position` is set; it then puts the store's origin there, in the pylon connector's axes.
Paveways are carried with their wings folded (arg 2 = 1).

DCS also puts the store's mass at `attach_point_position`, and moves it with the trapeze. Measured with
two GBU-27s (2026-11-14, EFM mass log): their mass sat at x 1.181, y 0.009 with the trapeze up (the
connector plus the offset) and at x 1.853, y -0.803 with it down. So each store's CG effect follows its
offset. With full fuel the clean aircraft is at 45.8% MAC (MAC 10.9 m, 45.2% at x = 0):

| Pair of stores | Mass point x | CG loaded | CG shift on release | Offset's share |
|---|---|---|---|---|
| GBU-27, GBU-10, GBU-31(V)1/B | 1.18 to 1.27 | 44.8 to 44.9% | 0.9 to 1.0% aft | 0.3% forward |
| GBU-31(V)3/B, Mk-84 | 1.06 to 1.09 | 44.9 to 45.0% | 0.8 to 0.9% aft | 0.2% forward |
| AGM-154A, AGM-154B, AGM-154C | 1.19 | 45.3% | 0.5% aft | 0.2% forward |
| GBU-12, GBU-32, CBU-105, Mk-82, AGM-65D/E | 0.62 to 1.06 | 45.5 to 45.6% | 0.1 to 0.3% aft | under 0.1% |

With 4,000 lb of fuel the loaded CG is about 0.9% further forward and a release shifts it up to 1.3%.
All cases stay inside the manual's 41.3 to 46.5% limits. Lowering the trapeze moves the CG about 0.5%
forward while it is down. The flight model bench puts stores at the GBU-27 point (`STORES_CG` in
`tools/fm_bench/sim.py`).

"Ahead" is how far the store's lugs (its `AttachPoint`, about its CG) sit ahead of the connector, so
that the store is centred in the bay.

| Store (model) | Ahead | Fit through the door and trapeze cycle |
|---|---|---|
| GBU-12, Mk-82, CBU-105 (`cbu-97`) | 0 | Clear |
| GBU-32(V)2/B, AGM-65D, AGM-65E | 0.2 m | Clear |
| Mk-84, GBU-31(V)1/B, GBU-31(V)3/B, AGM-154C | 0.53 to 0.74 m | Clear, with 8 to 27 mm to spare |
| GBU-27 (`gbu-27`, no `AttachPoint`) | 0.42 m (origin) | Clear while stowed. Its folded fins fill the 0.68 m bay width, and they touch the left door's inner panel as the trapeze lowers with the bay open |
| AGM-154A, AGM-154B | 0.53 m | Clear, with 12 mm to spare. DCS lists `kab-500s` as their pylon shape but draws `agm-154`, the same shape as AGM-154C, so they share its offset |
| GBU-10 | 0.08 m | Fits the 4.65 m length, but its folded fins touch the bay's side structure while stowed and the left door as the trapeze lowers |

The bay meshes are the original model's, stretched. GBU-27 and GBU-10 are limited by the bay's
width, not its length; a closer match needs the bay interior reworked. The order of that and other dimension fixes is in
[Dimensions against the references](../models/dimensions-vs-reference.md).

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
  The bay enlargement script runs after it. It checks that the closed doors sit in the belly
  plane, that the skin is open exactly over them and that nothing inside the bay shows with the doors
  shut.
  `tools/models/check_edm_export.py` then checks the exported model against the previous one, and
  that `Pylon1` and the left door use 26/904/906 and `Pylon2` and the right door use 26/905/906.
- `python tools/missions/bay_shots.py` flies a level test in DCS with a store on each pylon, steps
  through both bays open, each bay closed in turn and both closed, and saves screenshots and the
  arg values to `tools/missions/results/bays/`. `--store <name>` loads any bay store instead of GBU-27
  and `--right <name>` puts a different one on the right pylon; results go to `results/bays_<store>[_<right>]/`.
  All 14 stores were checked this way on 2026-11-14. Close DCS first.
