# Exterior model dimensions against the references

Where the exterior model (`blender_files/f-117-nighthawk-exterior.bigbay.blend`, installed as
`Shapes/f-117-nighthawk.edm`) differs from the published dimensions, what fixing each difference
involves, and the order to do it in. Measured 2026-11-14.

## Sources

| Source | What it gives |
|---|---|
| TO 1F-117A-1, Section I, "Dimensions" (`docs/reference/TO1F-117A-1_ocr.txt`) | Span 43 ft 4 in, length 63 ft 9 in, height 12 ft 9.5 in to the top of the tail and 12 ft 5 in to the closed canopy, main gear 14 ft 3 in apart |
| TO 00-105E-9, F-117A.2 "Aircraft dimensions" (`docs/reference/TO00-105E-9-R11-Segment12.pdf`, screenshot `Screenshot 2026-11-14 at 12.02.55.png`) | Length 65 ft 11 in, front to nose wheel 15 ft 8 in, nose wheel to main wheel 17 ft 11 in, track 14 ft 3 in, span 43 ft 4 in, tail height 12 ft 10 in, wingtip height 5 ft 11 in, struts at 3 in extension |
| TO 1F-117A-1, Figure 2-5 "Ground clearance" (`Screenshot 2026-11-13 at 17.07.09.png`) | Nose wheel FS 288, main wheel FS 503, open bay doors FS 348 to FS 531, ground clearances |

The two lengths differ by 26 in. The dimensions sheet draws the air data probes ahead of the nose in its
top view, so 65 ft 11 in is read here as the length over the probes and 63 ft 9 in as the length of the
airframe. On that reading the probes reach about 26 in ahead of the nose.

Fuselage stations are not distances from the nose. The front of the aircraft is 188 in ahead of the nose
wheel at FS 288, so it is at FS 100. If the front means the probe tips, the airframe nose is at about
FS 126.

## Model against the references

Model axes: x forward, y left, z up, metres. The airframe nose is at x 9.831 and the centre probe tip
at x 10.023. Gear positions are with the gear down.

| Dimension | Reference | Model | Difference | Status |
|---|---|---|---|---|
| Span | 43 ft 4 in (520 in) | 519.0 in | -1.0 in | Matches |
| Length over the probes | 65 ft 11 in (791 in) | 791.0 in | 0 | Matches, but see the next two rows |
| Airframe length | 63 ft 9 in (765 in) | 783.5 in | **+18.5 in (0.47 m)** | Too long |
| Probes ahead of the nose | about 26 in (791 - 765) | 7.6 in | **-18.4 in** | Too short |
| Front to nose wheel | 15 ft 8 in (188 in) | 194.3 in from the probe tip, 186.8 in from the nose | +6.3 in from the probe tip | See issue 1 |
| Airframe nose to nose wheel | about 162 in (188 - 26) | 186.8 in | **+24.8 in (0.63 m)** | Too long |
| Wheelbase | 17 ft 11 in (215 in), FS 288 to 503 | 211.8 in (x 5.087 to -0.292) | -3.2 in | Close |
| Main wheel to tail | about 388 in (765 - 162 - 215) | 384.9 in | -3.1 in | Close |
| Main gear track | 14 ft 3 in (171 in) | 165.1 in between tyre centres (4.194 m) | **-5.9 in** | Narrow |
| Leading-edge sweep | 67.5 degrees (commonly published, not in `docs/reference`) | 68.0 degrees, nose tip to wingtip | +0.5 degrees | Agrees with a nose about 0.4 m too long |
| Main tyre diameter | No source in `docs/reference` | Mesh 28.4 in, `FM/config.lua` and `main_gear_wheel_diameter` 32 in | 3.6 in between the mesh and the physics | Unsourced |
| Nose tyre diameter | No source | Mesh 21.8 in, physics 22 in | 0.2 in | Unsourced |
| Bay inside length | FS 348 to FS 531 (4.65 m). In Figure 2-5 the leader lines run to the inner side of the zigzags that mark the bay ends, so these are inside dimensions | Walls at x 3.600 to -1.040 (4.65 m), placed from the gear | 0 from the gear, about 7 cm forward from the nose | Matches. See issue 6 |
| Bay doors | Not given; they reach past the walls | Tooth tips at x 3.734 to -1.147 (4.88 m) | - | Overlap kept from the original model |
| `height` in `F-117-NightHawk.lua` | Tail 12 ft 9.5 in (3.899 m) | 3.78 m (the canopy height) | -0.12 m | Wrong figure used |
| Heights and ground clearances | Tail 12 ft 10 in, wingtip 5 ft 11 in, canopy 12 ft 5 in, Figure 2-5 clearances | Not measured | - | Unchecked |

The two length readings disagree about where the extra length is. Measured to the probe tip, the
model is the right length overall and only 6 in long ahead of the nose wheel. Measured to the airframe
nose, it is 18.5 in too long overall, and the whole excess is ahead of the nose wheel. The leading-edge
sweep supports the second reading. Issue 1 settles this before anything is changed.

## Issues, what fixing each involves, and the order

The list is in the order to do them. Cheap checks come first because they decide whether the costly fixes
are needed. Fixes to reference points come before anything placed from those points.

### 1. Confirm the nose length (measurement only, about 1 hour)

- Measure two ratios on a true side-profile photo in `docs/reference/ExteriorImages`, corrected for
  lens distortion: airframe nose to nose wheel against nose wheel to main wheel, and probe length
  against the wheelbase. The reference reading predicts 0.75 and about 0.12; the model gives 0.88 and
  0.04.
- Check the leading-edge sweep from a sourced figure.
- Outcome: either the model's nose is about 0.63 m too long with probes about 0.47 m too short (go to
  issue 5), or 65 ft 11 in is not over the probes and the model is right to within 6 in.

### 2. Lua `height` (5 minutes)

- Set `height = 3.90` (12 ft 9.5 in, top of the tail) in `F-117-NightHawk.lua`. It currently uses the
  canopy height.
- No model change.

### 3. Static heights and tyre size (about 1 hour)

- Find a source for the main and nose tyre sizes. The 32 in in the Lua has none, and the mesh is 28.4 in.
- In DCS, at rest on the ground with a typical load, measure the tail height, wingtip height, canopy
  height and the Figure 2-5 clearances. `tools/missions/bay_shots.py` starts in the air, but its
  mission builder can be copied for a ground start that logs heights.
- This shows whether the tyre mismatch makes the visible wheels float or sink, and whether the strut
  travel and `pos` in `FM/config.lua` give the 3 in extension the figures assume.

### 4. Tyre size (30 minutes to half a day, after issue 3)

- If the physics diameter is wrong: change `wheel_radius` in `FM/config.lua` and
  `main_gear_wheel_diameter` in the Lua, then recheck the static attitude and take-off and landing
  behaviour in `tools/fm_bench`.
- If the mesh is wrong: scale the tyre meshes about their hubs (`v_GL_Wheel`, `v_GR_Wheel`,
  `v_GR_Wheel.001`) with a script, and check that the retracted wheel still fits its well.

### 5. Nose length (several days, only if issue 1 confirms it)

- Shorten everything ahead of the nose gear well by about 0.63 m and lengthen the probes by about
  0.47 m. The cockpit, canopy, windscreen, inlets' forward edges, nose gear well and doors, lights,
  connectors, collision shells (`NOSE_CENTER`, `FUSELAGE_*_SIDE`), damage cells and UV-mapped panels all
  move or stretch. The leading-edge sweep changes unless the cut is a straight scale in x.
- The cockpit model and the pilot's eye point (`ViewSettings` in `Views.lua`) must move by the same amount, or the
  cockpit no longer lines up with the canopy.
- Mass properties: the EFM's reference point does not move, but the empty CG and inertia estimates
  were made against this model's layout and should be rechecked.
- Do it as a script like the bay enlargement, run on the tracked blend, so it can be
  reapplied and checked.
- Nothing behind the nose gear moves, so the bay and main gear are unaffected.

### 6. Bay inside length (done 2026-11-14)

- Figure 2-5's FS 348 and FS 531 are the bay's inside ends. Placed from the gear they fall at x 3.600
  and -1.040. The bay enlargement script now moves the end walls there, so the interior is 4.65 m.
- The doors and the trim at the ends of the opening move with the walls, keeping the original model's
  overlap past them, so the door tooth tips are at x 3.734 and -1.147 and the doors are 4.88 m long.
- Placement: placed from the airframe nose at FS 126 (or the probe tip at FS 100), the bay would sit up
  to about 7 cm further aft. The difference is the model's 3 in short wheelbase, so either choice is
  within the model's own error. The gear-based placement is kept, because the gear is what the bay sits
  between.

### 7. Main gear track (about half a day)

- Move both main gear legs outboard by 0.074 m (0.148 m in total), including the struts, wheels, doors
  and wheel wells, or check first whether 14 ft 3 in is measured between the struts. The struts sit
  at about y ±2.20, 173 in apart, close to the reference.
- Update `pos` for both main wheels in `FM/config.lua`, `main_gear_pos` in the Lua, the `WHEEL_L` and
  `WHEEL_R` collision shells and the dust connectors.
- Check the retracted wheel against its well and doors through the whole gear cycle.

### 8. Store fit (several days)

- With the 4.65 m bay, GBU-10 fits the length, and all three AGM-154s clear.
  GBU-10 and GBU-27 still touch the side structure or the left door, because their folded fins fill
  the bay's width. Both need the bay interior rebuilt rather than stretched. See
  [Bay size and store fit](../systems/weapon-bays.md#bay-size-and-store-fit).

### Not worth fixing

- The wheelbase is 3.2 in short (0.08 m, 1.5%). Moving the nose gear forward means a new nose wheel
  well, and the difference is too small to see.
- The span is 1 in short.
