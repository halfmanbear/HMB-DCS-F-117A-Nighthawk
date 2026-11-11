#!/usr/bin/env python3
"""Show how the flight controls respond at different moments of inertia.

The flight manual has no inertia figures and no transient data, so this can't say which inertia is right.
It shows how fast the aircraft responds at each value and whether the flight controls stay stable.

    python tools/fm_bench/inertia_sweep.py
    python tools/fm_bench/inertia_sweep.py --inertia 40000,260000,225000 --inertia 300000,900000,680000
"""
import argparse
import shutil
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import efm as efm_module  # noqa: E402
from scenarios import _level  # noqa: E402
from scorecard import read_inertia  # noqa: E402
from sim import FT_TO_M, RAD, Sim, mach_from_cas, pitch_axis_for_nz_delta  # noqa: E402

CONDITIONS = [
    ('170 KCAS, 2000 ft, gear down', 170, 2000, 40000, True),
    ('250 KCAS, 10000 ft', 250, 10000, 40000, False),
    ('350 KCAS, 10000 ft', 350, 10000, 40000, False),
    ('500 KCAS, 5000 ft', 500, 5000, 40000, False),
    ('300 KCAS, 30000 ft', 300, 30000, 36000, False),
]
SAMPLE_DT = 0.006


def _record(pilot, seconds, field):
    sim = pilot.sim
    values = []

    def watch(_):
        values.append(getattr(sim, field))

    pilot.fly(seconds, watch)
    return values


def _rise_time(values, final):
    """Seconds from 10% to 90% of the final change."""
    start = values[0]
    change = final - start
    if abs(change) < 1e-6:
        return float('nan')
    t10 = t90 = None
    for i, value in enumerate(values):
        fraction = (value - start) / change
        if t10 is None and fraction >= 0.1:
            t10 = i
        if t90 is None and fraction >= 0.9:
            t90 = i
            break
    return float('nan') if t10 is None or t90 is None else (t90 - t10) * SAMPLE_DT


def _swing(values):
    return max(values) - min(values)


def pitch_step(sim, kcas, alt_ft, weight, gear):
    """Ask for 1.5 g more than level flight and hold the stick there."""
    pilot = _level(sim, weight, alt_ft, mach_from_cas(kcas, alt_ft * FT_TO_M), seconds=20.0 if gear else 8.0, gear_down=gear)
    sim.freeze_speed = True
    pilot.pitch_axis = pitch_axis_for_nz_delta(1.5)
    nz = _record(pilot, 8.0, 'nz')
    final = sum(nz[-300:]) / 300.0
    return {'rise': _rise_time(nz, final), 'overshoot': 100.0 * (max(nz) - final) / max(final - nz[0], 0.01),
            'residual': _swing(nz[-300:]), 'final': final}


def roll_step(sim, kcas, alt_ft, weight, gear):
    """Full stick for a 90 degree roll, then let go: how fast it gets there and how cleanly it stops."""
    pilot = _level(sim, weight, alt_ft, mach_from_cas(kcas, alt_ft * FT_TO_M), seconds=20.0 if gear else 8.0, gear_down=gear)
    pilot.pitch_axis = 0.0
    pilot.roll_axis = 1.0
    rates = []

    def turning(s):
        rates.append(abs(s.p) / RAD)
        return s.roll >= 90.0

    pilot.fly(8.0, turning)
    peak = max(rates)
    to_90 = next((i for i, r in enumerate(rates) if r >= 0.9 * peak), len(rates)) * SAMPLE_DT
    pilot.roll_axis = 0.0
    stop_roll = sim.roll
    rollout = []

    def after_release(s):
        rollout.append((s.roll, s.p / RAD))

    pilot.fly(4.0, after_release)
    after = [roll for roll, _ in rollout]
    return {'peak': peak, 'to_90': to_90, 'stop_overrun': max(after) - stop_roll, 'reversal': max(0.0, -min(rate for _, rate in rollout)),
            'settled_swing': _swing(after[-300:])}


def yaw_step(sim, kcas, alt_ft, weight, gear):
    """Half pedal for 4 seconds then release: sideslip overshoot and how the oscillation dies away."""
    pilot = _level(sim, weight, alt_ft, mach_from_cas(kcas, alt_ft * FT_TO_M), seconds=20.0 if gear else 8.0, gear_down=gear)
    sim.freeze_speed = True
    pilot.yaw_axis = 0.5
    beta = _record(pilot, 4.0, 'beta')
    final = sum(beta[-150:]) / 150.0
    pilot.yaw_axis = 0.0
    release = _record(pilot, 6.0, 'beta')
    return {'overshoot': 100.0 * (max(abs(b) for b in beta) - abs(final)) / max(abs(final), 0.01),
            'early_swing': _swing(release[167:500]), 'late_swing': _swing(release[-300:])}


def run_one(job):
    dll, root, inertia = job
    sim = Sim(efm_module.Efm(dll, tempfile.mkdtemp(dir=root)), inertia)
    results = []
    for label, kcas, alt_ft, weight, gear in CONDITIONS:
        row = {'label': label}
        for name, test in (('pitch', pitch_step), ('roll', roll_step), ('yaw', yaw_step)):
            try:
                row[name] = test(sim, kcas, alt_ft, weight, gear)
            except FloatingPointError:
                row[name] = None
        results.append(row)
    return inertia, results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dll', type=Path)
    parser.add_argument('--inertia', action='append', help='roll,yaw,pitch in kg m2; repeat to compare several')
    args = parser.parse_args()
    dll = args.dll or efm_module.default_dll()
    inertias = [tuple(float(v) for v in text.split(',')) for text in args.inertia] if args.inertia else [read_inertia()]
    efm_module.build_stub()
    root = tempfile.mkdtemp(prefix='fm_bench_')
    try:
        with ProcessPoolExecutor(len(inertias)) as pool:
            outcomes = list(pool.map(run_one, [(dll, root, inertia) for inertia in inertias]))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    for inertia, results in outcomes:
        print(f'\nInertia roll {inertia[0]:.0f}, yaw {inertia[1]:.0f}, pitch {inertia[2]:.0f} kg m2')
        print(f"{'':30s} | pitch: rise s  over%  steady swing g | roll: peak dps  to 90% s  stop overrun deg  reversal dps | yaw: over%  swing after release deg, early/late")
        for row in results:
            pitch, roll, yaw = row['pitch'], row['roll'], row['yaw']
            text = f"{row['label']:30s} | "
            text += f"{pitch['rise']:6.2f} {pitch['overshoot']:6.0f} {pitch['residual']:8.3f}     | " if pitch else 'DIVERGED | '
            text += f"{roll['peak']:7.0f} {roll['to_90']:8.2f} {roll['stop_overrun']:9.1f} {roll['reversal']:9.1f}    | " if roll else 'DIVERGED | '
            text += f"{yaw['overshoot']:5.0f} {yaw['early_swing']:7.2f} {yaw['late_swing']:6.3f}" if yaw else 'DIVERGED'
            print(text)


if __name__ == '__main__':
    main()
