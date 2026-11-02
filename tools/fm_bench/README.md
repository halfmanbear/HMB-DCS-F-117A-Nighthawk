# Flight model bench

Flies the built EFM DLL outside DCS and scores it against the flight test data in TO 1F-117A-1. A full scorecard takes about a minute, so a change to the aero, engine or flight controls can be checked without a flight. It needs Python with `lupa`, `numpy` and `scipy`, the Visual Studio C++ tools, and a built EFM.

## Tools

| Command | What it does |
|---|---|
| `python tools/fm_bench/scorecard.py` | Flies every test and writes `results/scorecard.md`. Use `--only turn,accel` for some tests, `--dll` for another build and `--inertia roll,yaw,pitch` to try other values. |
| `python tools/fm_bench/fit_performance.py` | Solves for the lift, drag, thrust and fuel constants that best fit the manual, using a point-mass copy of the EFM's equations. It only proposes constants: put them in the EFM and check them with the scorecard. |
| `python tools/fm_bench/inertia_sweep.py --inertia 40000,260000,225000` | Steps the stick and pedals at five flight conditions and reports response time, overshoot and oscillation. Repeat `--inertia` to compare values. |
| `python tools/fm_bench/dcs_check.py --mission <miz>` | Flies one input sequence in DCS and on the bench, then compares them. Starts and closes DCS by itself in about 2.5 minutes. Overwrites `dcs.log` and the EFM's debug logs. |
| `python tools/fm_bench/dcs_check.py --takeoff --mission <miz>` | Flies the takeoff worked example on manual page A3-4. The mission's player must start at an airfield. |

Test data and its page references are in `targets.json`. Printed tables were copied as they are. Curves were read by eye, so allow about 0.1 g on the sustained turn data.

## How it works

`efm.py` loads a private copy of the DLL in a scratch folder, with a small stand-in for the cockpit parameter API (`cockpit_stub.cpp`). `F117_LOG_ROOT` keeps its debug logs away from those of real flights. `sim.py` does what DCS does between EFM calls: it integrates the forces and moments and feeds the state back. Its pilot moves the same stick axes as a player's joystick, so the flight controls stay in the loop.

## What the data can and can't set

The manual gives steady-state performance, so these come from it: lift slope, drag, thrust, fuel flow, AOA limits, maximum roll rates and full-pedal sideslip.

- **Inertia:** the manual has no inertia figures or transient data, so it can't set these. `FM/config.lua` follows the F-15C, which has almost the same mass and size, and is good to about 30%. The roll law takes its gain from the inertia DCS reports, so roll response stays the same across that range. The sweep shows the other axes are stable across it too.
- **How fast the roll stops:** the manual gives no figure. The law is set for about 23 deg of overrun after releasing a full-stick roll at 190 deg/s, with no reversal, which is a choice made for feel.
- **Handling feel:** response times and control harmony have no data behind them. They need judging in flight.
- **Aero tables:** these descend from an F-16 model and are scaled to fit, so they match F-117 numbers without being F-117 aerodynamics. Sideslip and control derivatives are the least checked.

## Known differences from the manual

- Level acceleration at 30,000 ft runs about 15% to 25% quick at 32,000 and 36,000 lb. At 52,000 lb and 20,000 ft, the last step to 424 KCAS is about 10% slow.
- Sustained turns at low altitude from Mach 0.7 to 0.85 are up to 0.35 g short.
- Idle thrust is fitted up to 30,000 ft, where the deceleration data stops, and held constant above that. The manual's descent tables aren't checked.
- The takeoff ground run is about 7% long, while the distance to clear 50 ft is about 4% short.
- There's no ground or gear model on the bench, so takeoff and landing need `dcs_check.py` or a flight. Landing distance isn't checked yet. `scenarios.ground_bumps` only checks that the flight controls ignore runway bumps while the wheels are reported on the ground, and `dcs_check.py --takeoff` reports the elevon movement on a real runway.

## DCS behaviour this depends on

- DCS starts the aircraft at `M_empty`, with no fuel in its mass, and adds `delta_mass` from `ed_fm_change_mass`. So the EFM reports fuel as loaded (positive) and burned (negative).
- DCS collects that mass before it calls the `ed_fm_hot_start` functions, so only `ed_fm_release` clears the EFM's record of it.
- The body accelerations passed to `ed_fm_set_current_state_body_axis` exclude gravity: they read zero on a parked aircraft.
