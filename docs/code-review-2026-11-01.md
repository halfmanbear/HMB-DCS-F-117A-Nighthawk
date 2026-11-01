# Extended code review — 1 November 2026

**Follow-up status — all ten findings fixed on 1 November 2026.** The corrected EFM was built as Release x64 and installed at the DLL path used by the existing development proxy. The installed binary matches the validated build. Validation: 95 mod tests, all eight EFM regression scripts, 131 Lua 5.1 syntax checks, calibration validation and release-DLL validation passed. The findings below retain the original review evidence; the resolution table at the end describes the changes.

Reviewed the active mod source and the local EFM repository referenced by `bin/efm.proxy.ini`. This includes cockpit devices and indicators, inputs, aircraft/FM configuration, weapons and payloads, native displays, EFM flight controls/aerodynamics/engine/avionics and lifecycle callbacks, packaging/CI, and layout/generation tools. Existing backups and vendor/SDK code were used as context, not treated as independently maintained features. Binary models, textures and DCS rendering were not visually validated. The EFM findings concern the current source checkout; source parity with the already installed EFM DLL has not been established.

No production code or DLL was changed during this review. The EFM was built into `tmp/code-review-20261101/efm-build`, not installed. The three fixes from the previous review remain in place.

## Findings

### 1. P1 — Fuel burn never reaches the DCS mass-change callback

[EFM mass callback](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:2276>)

Both branches of the initial inertia comparison return `false`. The subsequent fuel-mass block is unreachable, so internal fuel quantity decreases while this callback never supplies the corresponding aircraft mass change. A source-function reproduction with 12 kg of pending consumption returned false and left all 12 kg pending. This is independent of whether the inertia comparison matches.

Remove the unconditional early returns, keep inertia handling separate from fuel reporting, and test successful consumption plus a second call that returns no further change. Also account for unlimited fuel and multiple simulation steps before consumption is collected; the present producer assigns rather than accumulates consumption.

### 2. P1 — Ground effect uses terrain elevation instead of aircraft clearance

[Ground-effect calculation](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:1756>); [Surface callback](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:2048>)

`ed_fm_set_surface` stores terrain elevation in `surface_height_m`. The induced-drag calculation uses that value directly as height above the ground. Over sea-level terrain, its ground-effect multiplier remains zero even at 3,048 m aircraft altitude, eliminating the induced-drag contribution. Over elevated terrain the same aircraft clearance produces a different result.

Compute clearance from aircraft altitude minus the relevant surface height, clamp it to a valid nonnegative distance, and retain a sensible fallback until both observations are available. Test the same AGL over sea-level and elevated terrain, plus high-altitude free-air behavior.

### 3. P1 — PAARS pullout altitude uses body-axis vertical speed

[PAARS altitude publication](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:1468>); [Body-axis state assignment](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:2174>)

The misleadingly named `velocity_world_cs` is assigned body-axis velocity. PAARS treats its Y component as world vertical velocity to derive flight-path angle. An aircraft descending along its own longitudinal axis has near-zero body Y velocity, so this code can treat a steep descent as level flight. At 200 m/s in a 30-degree descent from 10,000 ft, the reproduction published 10,000 ft; the same estimator supplied the world flight-path angle gives 8,000 ft.

Use the world velocity supplied to `ed_fm_set_current_state` (`vx_world`, `vy_world`, `vz_world`) for flight-path angle. Test pitched descent with zero body-axis vertical velocity and a banked case.

### 4. P2 — Release leaves automatic-control and refueling state selected

[EFM lifecycle reset](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:2693>)

`ed_fm_release` clears `alt_hold` twice and never clears `altroll_hold`. It also leaves `airRefuelDoorOpen` set. Neither startup helper clears these fields. A reproduction set both states, called the actual release function, and observed altitude/bank hold still selected and the refuel door flag still open. When the module is reused this can apply an old hold or keep AAR control-law changes/PAARS inhibition in a new aircraft session.

Reset these fields in a common lifecycle initializer and verify cold, ground-hot, air-hot and release/restart transitions. Check other actuator/filter state at the same boundary rather than relying on DLL unloading.

### 5. P2 — VSD altitude mode and altitude calculation use different parameters

[Altitude calculation](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/Cockpit/Scripts/HUD/Device/HUD_Device.lua:149>); [Mode initialization](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/Cockpit/Scripts/Systems/Displays.lua:259>)

The display initializes/toggles `altMode`; the calculation checks `ALTITUDE_MODE`. No producer for `ALTITUDE_MODE` was found in the active mod or EFM source. With the normal zero-initialized handles, a 1,000 m barometric altitude leaves `ALTITUDE_HUD` at zero, so the live VSD altitude box is wrong. Setting `ALTITUDE_MODE=1` makes the same calculation publish 3,280.84 ft. The newer OCIP HUD has its own barometric parameter and is not affected by this particular path.

Use a single mode parameter, initialize it, and test the real selector through barometric/radar transitions.

### 6. P2 — Side displays label airspeed as ground speed

[Ground-speed producer](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/Cockpit/Scripts/HUD/Device/HUD_Device.lua:167>)

`HUD_GS`/`GS_HUD` are computed from `getSelfAirspeed`, then shown as GS on the VSD/HSD. With airspeed 150 m/s and ground velocity 200 m/s, the reproduction displays 291.58 kt instead of 388.77 kt. The central map uses ground velocity independently, so its GS can disagree with the side displays.

Use horizontal world ground velocity for GS, and retain airspeed for the quantities that require it. Include wind and climb/descent cases.

### 7. P2 — TTI includes the four-second laser overrun

[Release timer initialization](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:1172>); [Published flight-time parameter](<C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code/F_117_NightHawk.cpp:1197>); [IRADS TTI readout](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/Cockpit/Scripts/Systems/IRADS_Readouts.lua:29>)

The EFM initializes `laser_window` to predicted flight time plus `kLaserOverrunSeconds` (4 seconds), then publishes that window as `F117_STORE_FLIGHT_TIME`. Lua labels it TTI. A 30-second predicted flight therefore displays `TTI 00:34` and continues counting after predicted impact. This is a timer/label mismatch even though confirmed impact tracking is intentionally unavailable.

Separate predicted remaining flight time from laser illumination duration, preserving the laser overrun independently.

### 8. P2 — Applying color after source edits can change the wrong symbol

[Editor color action](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/tools/layout_editor.py:1068>)

The color action passes the current source text alongside the previous compiled model's source-line locations. It lacks the stale-source guard already present in the transform action. Selecting `SNSR` on the right HSD, inserting one newline before the preceding `MARK` call, then applying red recolors `MARK` instead. The modified Lua still compiles, so validation does not catch the wrong target.

Require a fresh successful preview before applying color, or rebuild the model and resolve the selection against the new source. Add a regression that inserts lines between preview and color application.

### 9. P3 — Beacon rotation stutters and runs slower than its configured rate

[Beacon rotation](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/Cockpit/Scripts/Systems/lights_system.lua:108>)

After `flashcounter` exceeds 1, the direction flag toggles each update while the counter never resets. The counter then advances only on alternate updates. The increment also contains a factor of 0.5 despite the requested rate being expressed as cycles per minute. After the initial transition the effective steady rate is about 21.25 cycles/minute, rather than the configured 85. The reproduction found 80 unchanged outputs in 159 consecutive later updates.

Use a modulo-one phase accumulator advanced at the configured cycles-per-second rate. Keep rotation and any separate flash duty cycle independent.

### 10. P3 — The root HUD preview script no longer loads the live HUD

[Legacy preview shim](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/hud_preview.py:121>)

Its `dofile` shim returns nil. The live HUD now calls a function returned by `dofile` on its first line, so execution fails immediately with an attempt to call nil and registers zero elements. The script catches the error and proceeds toward an empty/partial preview. `tools/layout_editor.py` has a working loader and remains usable.

Route this entry point through the maintained preview runtime, or retire it explicitly so it cannot imply that it previews the current HUD.

## Validation and evidence

- Lua 5.1 syntax: 131 files compiled, zero syntax failures.
- Mod regression suite: `python -m pytest -q -p no:cacheprovider` — 90 passed.
- Calibration validator: passed, including registrations, units, geometry, parents and pitch movement.
- Complete EFM Release x64 build: passed, all build outputs redirected into the review directory.
- EFM regression scripts: autothrottle, PAARS, release-zone and terrain-lock scripts passed.
- Three EFM regression scripts did not complete:
  - `irads_input_regression.py`: still asserts exactly three axes, but the deployed profile also has brightness/contrast axes.
  - `irads_tracking_store_regression.py`: mock supplies a Python function where the updated display code expects a parameter handle exposing `set`.
  - `weapon_delivery_regression.py`: requires copied EFM-repository cockpit files to equal the deployed files; those copies have diverged. Its initial actual Weapons.lua checks passed before that assertion.
- Lua/editor reproductions: [reproduce.py](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/tmp/code-review-20261101/reproduce.py:1>); JSON output in the same directory.
- EFM reproductions: [efm_review.cpp](<E:/Saved Games/DCS/Mods/aircraft/F-117-Nighthawk/tmp/code-review-20261101/efm_review.cpp:1>). This uses extracted production functions with controlled inputs/stubs; it does not launch DCS.
- EFM regression logs: `tmp/code-review-20261101/efm-tests/<test-name>/run.log`.

The obsolete Lua tailhook script has an undefined `hook` variable, but the active EFM independently drives tailhook actuation. It is therefore recorded as dead-code cleanup, not counted as a broken aircraft control. A suspected elevator-table overflow was also excluded: the production aerodynamic wrappers clamp the input before interpolation.

The fixes were applied in that priority order. In-game checks remain necessary for actual DCS mass changes, aerodynamic behavior, PAARS recovery and rendered avionics.


## Resolutions applied

| Finding | Resolution | Regression coverage |
|---|---|---|
| 1. Fuel mass | Accumulate actual consumption, cap it at available fuel, honor unlimited fuel, and drain the pending mass exactly once through the DCS callback. Removed the unreachable absolute-inertia correction. | EFM `simulation_state_regression.py`: multiple ticks, exhaustion, invalid time steps, unlimited fuel and repeated collection. |
| 2. Ground effect | Use aircraft altitude minus the supporting terrain/object elevation. Use free-air behavior until valid surface/altitude observations arrive. | Same AGL over different terrain elevations; elevated object surfaces; contact; high altitude; unknown/invalid observations. |
| 3. PAARS | Use world velocity to derive the descent angle supplied to the pullout estimator. | Upright and banked 30-degree descents, plus level flight. |
| 4. Session state | Common control/actuator reset runs on release and every cold/hot/air start. Clears old hold/refueling modes, trim, filters, actuator state and pending fuel burn. Old thrust is cleared before a new cold start. | Dirty-state tests for release and all three start paths, including gear and engine state. |
| 5. Altitude mode | HUD/VSD altitude calculation now reads the same initialized `altMode` parameter that the selector writes. | Actual display selector through barometric/radar/barometric transitions. |
| 6. Ground speed | Side-display GS now comes from horizontal ground velocity. | Different air/ground speeds, climb/descent, cross-axis motion and low-speed CAS/GS handover. |
| 7. TTI | Predicted remaining weapon flight time has its own countdown, separate from the four-second laser overrun. | Actual release-sequence functions: accepted launch, countdown, publication and expiration. |
| 8. Editor color | Reject applying color to a selection until edited source has been previewed successfully. | Insert a newline after selection and verify that no recoloring occurs. Existing successful recolor/undo tests still pass. |
| 9. Beacon | Advance a modulo-one phase at 85 cycles/minute. | 400 consecutive phase updates across wraps, plus switching the beacon off. |
| 10. HUD preview | Root entry point now uses the maintained Layout Studio model/renderer. Retains roll/pitch arguments and supports headless PNG output. | Live HUD produces visible elements, accepts changed attitude, and exports a PNG. |

The three previously failing EFM harnesses were repaired to validate the deployed mod rather than obsolete mirrored cockpit files. Their native input declarations/assertions were deduplicated and updated for the current optical slew rates. Mock parameter handles now live inside Lua, eliminating the repeated-call Python/Lua handle failure. Personal saved-input files are no longer required by the tracking regression.

### Final build and rollback evidence

- EFM source: `C:/Users/Fraser/Git/HMB-DCS-F-117A-EFM/EFM Source Code`.
- Installed EFM target: `EFM Source Code/bin/F_117_NightHawk.dll` in that repository, as selected by this mod's existing `bin/efm.proxy.ini`.
- Final installed DLL SHA-256: `b068e6507a9d37b6ab820e468734e0111ab1eb429f1d94b5b5d61512a7931a6e`.
- Source/build hashes: `tmp/fix-all-20261101/manifest.json`.
- Pre-change file backups: `tmp/fix-all-20261101/before/`; previous target DLL: `before/EFM-target-F_117_NightHawk.dll`.
- EFM regression logs and pass results: `tmp/fix-all-20261101/efm-tests/`.
- Current-HUD preview smoke test: `python hud_preview.py --roll 30 --pitch -5 --output tmp/fix-all-20261101/hud-preview.png`.

No source commits, pushes or releases were created. Restart DCS before testing the corrected EFM and cockpit scripts.
