# Flight model bench

Flies the built EFM DLL outside DCS and scores it against the flight test data in TO 1F-117A-1. A full scorecard takes about a minute, so a change to the aero, engine or flight controls can be checked without a flight. It needs Python with `lupa`, `numpy` and `scipy`, the Visual Studio C++ tools, and a built EFM.

## Tools

| Command | What it does |
|---|---|
| `python tools/fm_bench/scorecard.py` | Flies every test and writes `results/scorecard.md`. Use `--only turn,accel` for some tests, `--dll` for another build and `--inertia roll,yaw,pitch` to try other values. |
| `python tools/fm_bench/fit_performance.py` | Solves for the drag, thrust table, idle thrust and fuel constants that best fit the manual, using a point-mass copy of the EFM's equations. It only proposes constants: put them in the EFM, copy them over `fitted_constants.json` and check them with the scorecard. `--bench` also fits the row-by-row gap to the last scorecard, which must have been flown with `fitted_constants.json`. |
| `python tools/fm_bench/inertia_sweep.py --inertia 40000,260000,225000` | Steps the stick and pedals at five flight conditions and reports response time, overshoot and oscillation. Repeat `--inertia` to compare values. |
| `python tools/fm_bench/dcs_check.py --mission <miz>` | Flies one input sequence in DCS and on the bench, then compares them. Starts and closes DCS by itself in about 2.5 minutes. Overwrites `dcs.log` and the EFM's debug logs. |
| `python tools/fm_bench/dcs_check.py --takeoff --mission <miz>` | Flies the takeoff worked example on manual page A3-4. The mission's player must start at an airfield. |
| `python tools/fm_bench/dcs_check.py --landing --mission <miz>` | Flies the landing worked example on manual pages A8-2 to A8-4 (36,000 lb, 10 kt headwind) onto Kobuleti, with and without the chute, in about 6 minutes. Needs any Caucasus mission with a player F-117. Writes `results/dcs_check_landing.md`. |

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

- Two of the 249 manual tests are out of tolerance: 200 to 250 KCAS at 20,000 ft and 40,000 lb is 0.12 min quick, and the sea level turn at Mach 0.4 is 0.16 g high. Closing them by more fitting would push neighbouring rows out.
- Thrust below Mach 0.30 isn't covered by the in-flight data. It rises to the engines' 94 kN rating at a standstill, set from the takeoff example.
- Idle thrust is fitted up to 30,000 ft, where the deceleration data stops, and held constant above that. The manual's descent tables aren't checked.
- `--takeoff` rotates straight to 9 deg of pitch and lifts off at about 182 KIAS, where the manual's example lifts off at 194 KCAS. So its ground run (about 4,500 ft against 4,700) and distance to clear 50 ft (about 6,000 ft against 6,950) are set by that technique as much as by the aircraft.
- Gear drag is set from the glide chart (Figure 3-5, data basis estimated): best glide drops from about 8.5 to 5.9 with the gear down, and the model's ratio is 1.43 against the chart's 1.44. The model's own best glides are lower, about 6.8 and 4.7, because its clean drag is fitted to the flight test data.
- There's no ground or gear model on the bench, so takeoff and landing need `dcs_check.py` or a flight. The bench never reports a surface height, so ground effect is off there.
- Ground effect adds 20% lift on the wheels, halving for every 0.15 span of height. The size is set by manual page A3-1, which puts liftoff AOA about 2 deg under the 8.5 deg reference: `--takeoff` lifts off at about 6.9 deg. How fast it fades with height is a choice, since the manual gives one point.
- Brake strength and chute drag were set from the landing example (`--landing`), after ground effect was added. Ground roll and total distance from 50 ft are within about 1% of the manual, with and without the chute. The script holds the approach throttle (about 70%) into the flare and cuts to idle 10 ft above the runway. That touches down at 145 KCAS 7.7 s after 50 ft, against the manual's 149 KCAS and 7.5 s, at 9 deg of pitch, under the 12 deg elevon strike angle. Cutting to idle at 50 ft loses 28 kt instead of 9: approach drag is about 40 kN and idle thrust is reached within about 3 s. The manual gives no engine spool-down time to check that against.
- With wind set, DCS's `LoGetTrueAirSpeed` returns ground speed and its indicated airspeed reads high. Test hooks use ground velocity less the wind, and the cockpit uses the EFM's `F117_CAS_MPS` and `F117_TAS_MPS`. `scenarios.ground_bumps` only checks that the flight controls ignore runway bumps while the wheels are reported on the ground, and `dcs_check.py --takeoff` reports the elevon movement on a real runway.

## Runway ride

The bench has no gear, so strut changes need DCS. For a fair comparison with a stock jet, use a power setting that gives it the same acceleration: on full afterburner the F-15C leaves the ground by about 520 m and never reaches the rougher part of the runway. At similar acceleration, load factor on the runway now matches the F-15C. Roll rate is still about 1.5 times higher while the bank movement is about the same. The aircraft rocks at about 3 Hz on its main gear against 1 to 2 Hz for the F-15C, which fits its wider gear.

On the takeoff from the SA-3 Strike mission's Caucasus airfield, the largest roll rate on the runway is 12 to 14 deg/s, from ±0.7 deg bank rocking just before rotation, with the elevons still. Ground effect isn't the cause: the build before it gave 12.2 deg/s there. Main strut damping doesn't lower the peak. Compared with the current 30000 in both directions:

| Main strut damping, compress / extend | Peak roll rate | RMS roll rate | RMS vertical jolt | Notes |
|---|---|---|---|---|
| 45000 / 45000 | 16.5 deg/s | 4.4 | 0.23 g | worse |
| 20000 / 20000 | 12.8 | 2.9 | 0.16 | aircraft rises 0.24 m after a 2.7 m/s touchdown |
| 20000 / 30000 | 13.5 | 3.0 | 0.16 | rises 0.17 m after the same touchdown |
| 30000 / 30000 | 12.7 | 3.4 | 0.19 | kept: lighter damping only lowers the RMS figures |

## DCS behaviour this depends on

- DCS starts the aircraft at `M_empty`, with no fuel in its mass, and adds `delta_mass` from `ed_fm_change_mass`. So the EFM reports fuel as loaded (positive) and burned (negative).
- DCS collects that mass before it calls the `ed_fm_hot_start` functions, so only `ed_fm_release` clears the EFM's record of it.
- The body accelerations passed to `ed_fm_set_current_state_body_axis` exclude gravity: they read zero on a parked aircraft.
