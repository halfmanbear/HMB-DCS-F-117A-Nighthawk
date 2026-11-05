#!/usr/bin/env python3
"""Fit the EFM's drag, thrust and fuel constants to the flight manual's performance data.

This uses a point-mass model with the same equations as the EFM, so it runs in seconds. It proposes
constants to put in the EFM; scorecard.py then checks them on the built DLL, flight controls included.

    python tools/fm_bench/fit_performance.py
    python tools/fm_bench/fit_performance.py --bench

fitted_constants.json holds the constants currently in the EFM, and each fit starts from them. --bench also
takes the gap between this model and the last scorecard, row by row, and fits with that gap included. That
only makes sense when the scorecard was flown with those same constants.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares, lsq_linear

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sim import FT_TO_M, G, LB_TO_KG, cas_from_mach, isa, mach_from_cas  # noqa: E402

S = 84.77  # The EFM's wing area (m2).
THRUST_ALIGNMENT = math.cos(math.radians(10.0))  # The EFM toes each engine out by 10 degrees.

DRAG_NAMES = ['cd0', 'k1', 'k', 'wave', 'idle_sl', 'idle_per_10km']
DRAG_LOWER = [0.005, -0.06, -0.2, 0.0, -10000.0, 0.0]
DRAG_UPPER = [0.05, 0.06, 0.5, 5.0, 10000.0, 30000.0]
TABLE_ALT_FT = [0.0, 10000.0, 20000.0, 30000.0, 40000.0]
TABLE_MACH = [0.30, 0.50, 0.70, 0.80, 0.90]
TABLE_ALT_M = np.array(TABLE_ALT_FT) * FT_TO_M
TABLE_MACH_ARRAY = np.array(TABLE_MACH)
THRUST_LOWER_KN = 3.0
THRUST_UPPER_KN = 94.0  # Two F404s at about 47 kN each.
MDIV = 0.85
MLIMIT = 0.91  # Same as Mlimit in the EFM. The manual has no data above Mach 0.90, so the barrier isn't fitted.
BARRIER = 0.096098
CHORD = 6.422  # The EFM's mean chord (m).
CZQ = -30.0  # About what the EFM's Czq table gives between 0 and 15 degrees.
SMOOTHNESS = 6.0  # Weight on sharp changes of slope in the thrust table, per unit of log thrust.
INSIDE = 0.6  # Being this far inside a tolerance is good enough, so most of the penalty starts here.
EDGE = 0.92  # And a row this close to its tolerance is pushed back hard.
EDGE_WEIGHT = 5.0
REACH_MARGIN_FPM = 100.0  # Spare excess power wanted at the Mach limit, so small differences from the bench don't lose it.


def wave_drag(p, mach):
    """Same shape as the EFM: a quadratic rise from Mdiv and a barrier above the limit, scaled to the range up to Mach 1.05."""
    drag = 0.0
    if mach > MDIV:
        drag += p['wave'] * ((min(mach, 1.05) - MDIV) / (1.05 - MDIV)) ** 2
    if mach > MLIMIT:
        drag += BARRIER * ((min(mach, 1.05) - MLIMIT) / (1.05 - MLIMIT)) ** 2
    return drag


def max_thrust(p, mach, h):
    """Installed thrust of both engines, bilinear in altitude and Mach as in the EFM. Above the top row it carries on along the same slope."""
    table = p['table']
    mach = min(max(mach, TABLE_MACH[0]), TABLE_MACH[-1])  # The EFM adds thrust below Mach 0.30 for takeoff. The in-flight data starts here.
    h = min(h, 13716.0)
    i = min(int(np.searchsorted(TABLE_ALT_M, h, side='right')) - 1, len(TABLE_ALT_M) - 2)
    j = min(int(np.searchsorted(TABLE_MACH_ARRAY, mach, side='right')) - 1, len(TABLE_MACH) - 2)
    a = (h - TABLE_ALT_M[i]) / (TABLE_ALT_M[i + 1] - TABLE_ALT_M[i])
    b = (mach - TABLE_MACH[j]) / (TABLE_MACH[j + 1] - TABLE_MACH[j])
    return ((1.0 - a) * ((1.0 - b) * table[i, j] + b * table[i, j + 1])
            + a * ((1.0 - b) * table[i + 1, j] + b * table[i + 1, j + 1]))


def idle_thrust(p, mach, h):
    """Net thrust at idle: gross thrust less the engines' ram drag, so it can be negative. The data stops at 30,000 ft."""
    return p['idle_sl'] + p['idle_per_10km'] * min(h, 9144.0) / 10000.0


class Model:
    def __init__(self, p, cna, alpha0):
        self.p = p
        self.cna = cna
        self.alpha0 = alpha0

    def specific_excess(self, thrust, mach, h, weight_n, n=1.0):
        """Excess power per unit weight: climb angle available in level flight at load factor n."""
        rho = isa(h)[2]
        V = mach * isa(h)[3]
        qs = 0.5 * rho * V * V * S
        cn = n * weight_n / qs
        # In a turn, pitch rate supplies part of the lift, so the wing needs less angle of attack.
        pitch_rate = G / V * (n - 1.0 / n)
        pitch_rate_lift = -CZQ * CHORD / (2.0 * V) * pitch_rate
        alpha = math.radians(self.alpha0 + (cn - pitch_rate_lift) / self.cna)
        cx = self.p['cd0'] + self.p['k1'] * cn + self.p['k'] * cn * cn + wave_drag(self.p, mach)
        return ((THRUST_ALIGNMENT * thrust - qs * cx) * math.cos(alpha) - n * weight_n * math.sin(alpha)) / weight_n, V

    def sustained_g(self, mach, h, weight_n):
        thrust = max_thrust(self.p, mach, h)
        low, high = 0.3, 8.0
        for _ in range(18):
            n = (low + high) / 2.0
            if self.specific_excess(thrust, mach, h, weight_n, n)[0] > 0.0:
                low = n
            else:
                high = n
        return (low + high) / 2.0

    def _seconds(self, thrust_of, h, weight_n, v_from, v_to, sound):
        """Time to change speed from v_from to v_to in level flight, by integrating dt = dV / acceleration."""
        total = 0.0
        points = 6
        step = (v_to - v_from) / points
        for i in range(points):
            mach = (v_from + (i + 0.5) * step) / sound
            excess = self.specific_excess(thrust_of(mach), mach, h, weight_n)[0] * G
            # Keeps the time finite and smooth when the aircraft can barely accelerate, so the fit can recover.
            if step > 0.0:
                excess = max(excess, 0.0) + 0.01 * math.exp(-max(excess, 0.0) / 0.01)
            else:
                excess = min(excess, 0.0) - 0.01 * math.exp(min(excess, 0.0) / 0.01)
            total += step / excess
        return total

    def accel_times(self, alt_ft, weight_lb, kcas, fuel_lb):
        h = alt_ft * FT_TO_M
        sound = isa(h)[3]
        weight = (weight_lb - fuel_lb / 2.0) * LB_TO_KG * G
        out = [0.0]
        for a, b in zip(kcas, kcas[1:]):
            seconds = self._seconds(lambda m: max_thrust(self.p, m, h), h, weight,
                                    mach_from_cas(a, h) * sound, mach_from_cas(b, h) * sound, sound)
            out.append(min(out[-1] + seconds / 60.0, 30.0))
        return out

    def decel_times(self, alt_ft, weight_lb, limit_mach, kcas):
        h = alt_ft * FT_TO_M
        sound = isa(h)[3]
        weight = weight_lb * LB_TO_KG * G
        limit_cas = cas_from_mach(limit_mach, h)
        points = [200.0] + [k for k in kcas if k < limit_cas] + [limit_cas]
        elapsed = {200.0: 0.0}
        for low, high in zip(points, points[1:]):
            seconds = self._seconds(lambda m: idle_thrust(self.p, m, h), h, weight,
                                    mach_from_cas(high, h) * sound, mach_from_cas(low, h) * sound, sound)
            elapsed[high] = min(elapsed[low] + seconds / 60.0, 30.0)
        return [elapsed.get(k, elapsed[limit_cas]) for k in kcas], elapsed[limit_cas]

    def climb_times(self, weight_lb, cas_kt, sched_mach, altitudes_ft, fuel_lb):
        h = 15.0
        t = 0.0
        out = []
        step = 150.0
        points = [0.0] + list(altitudes_ft)
        fuels = [0.0] + list(fuel_lb)

        def speed(height):
            return min(mach_from_cas(cas_kt, height), sched_mach) * isa(height)[3]

        for alt in altitudes_ft:
            target = alt * FT_TO_M
            while h < target:
                fuel = np.interp(h / FT_TO_M, points, fuels)
                weight = (weight_lb - fuel) * LB_TO_KG * G
                V = speed(h)
                mach = V / isa(h)[3]
                excess, _ = self.specific_excess(max_thrust(self.p, mach, h), mach, h, weight)
                dvdh = (speed(h + step) - V) / step
                sin_gamma = excess / (1.0 + V * dvdh / G)
                sin_gamma = max(sin_gamma, 0.0) + 0.002 * math.exp(-max(sin_gamma, 0.0) / 0.002)
                t += step / (V * sin_gamma)
                h += step
            out.append(min(t / 60.0, 60.0))
        return out


def fit_lift(targets):
    """Lift slope and zero-lift angle of attack from the manual's angle of attack tables."""
    cn, aoa = [], []
    for row in targets['trim_aoa']['rows']:
        h = row['alt_ft'] * FT_TO_M
        V = mach_from_cas(row['kcas'], h) * isa(h)[3]
        cn.append(row['weight_lb'] * LB_TO_KG * G / (0.5 * isa(h)[2] * V * V * S))
        aoa.append(row['aoa'])
    slope, intercept = np.polyfit(cn, aoa, 1)
    return 1.0 / slope, intercept, list(zip(cn, aoa))


def performance_rows(model, targets):
    """Every compared value as (test, condition, manual, model, tolerance), named and scored as scorecard.py does."""
    p = model.p
    rows = []
    for table in targets['level_accel']['tables']:
        for row in table['rows']:
            times = model.accel_times(table['alt_ft'], row['weight_lb'], table['kcas'], row['fuel_lb'])
            for kcas, want, have in zip(table['kcas'][1:], row['min'][1:], times[1:]):
                rows.append(('Level acceleration', f"{table['alt_ft']} ft, {row['weight_lb']} lb, to {kcas} KCAS",
                             want, have, max(0.1, 0.1 * want)))
    block = targets['idle_decel']
    for row in block['rows']:
        times, total = model.decel_times(row['alt_ft'], block['weight_lb'], row['limit_mach'], row['kcas'])
        for kcas, want, have in zip(row['kcas'], row['min'], times):
            rows.append(('Idle deceleration', f"{row['alt_ft']} ft, from {kcas} KCAS", want, have, max(0.1, 0.1 * want)))
        rows.append(('Idle deceleration', f"{row['alt_ft']} ft, from limit Mach", row['limit_min'], total, max(0.1, 0.1 * row['limit_min'])))
    block = targets['climb']
    for row in block['rows']:
        altitudes = block['alt_ft'][:len(row['min'])]
        times = model.climb_times(row['weight_lb'], block['cas_kt'], block['mach'], altitudes, row['fuel_lb'])
        for alt, want, have in zip(altitudes, row['min'], times):
            rows.append(('Climb time', f"{row['weight_lb']} lb, to {alt} ft", want, have, max(0.1, 0.1 * want)))
    block = targets['service_ceiling']
    for row in block['rows']:
        h = row['alt_ft'] * FT_TO_M
        weight = (row['initial_weight_lb'] - row['fuel_lb']) * LB_TO_KG * G
        excess, V = model.specific_excess(max_thrust(p, block['mach'], h), block['mach'], h, weight)
        # The ceiling is where excess power is 100 ft/min. Near it, 1,000 ft of altitude is worth about 1 m/s of that.
        rows.append(('Excess power at the ceiling', f"{row['initial_weight_lb']} lb at start", 0.508, excess * V, 1.0))
    for row in targets['max_level_speed']['thrust_limited']:
        h = row['alt_ft'] * FT_TO_M
        mach = mach_from_cas(row['kcas'], h)
        excess, V = model.specific_excess(max_thrust(p, mach, h), mach, h, row['weight_lb'] * LB_TO_KG * G)
        rows.append(('Top speed, excess power at the limit', f"{row['weight_lb']} lb, {row['alt_ft']} ft, {row['kcas']} KCAS",
                     0.0, excess * V / 0.3048 * 60.0, 300.0))
    for row in targets['max_level_speed']['reaches_limit_mach']:
        h = row['alt_ft'] * FT_TO_M
        excess, V = model.specific_excess(max_thrust(p, row['mach'], h), row['mach'], h, row['weight_lb'] * LB_TO_KG * G)
        rows.append(('Top speed, must reach limit Mach', f"{row['weight_lb']} lb, {row['alt_ft']} ft, Mach {row['mach']}",
                     0.0, excess * V / 0.3048 * 60.0, REACH_MARGIN_FPM))
    block = targets['sustained_turn']
    for row in block['rows']:
        h = row['alt_ft'] * FT_TO_M
        for mach, want in zip(block['mach'], row['g']):
            if want is not None:
                have = model.sustained_g(mach, h, block['weight_lb'] * LB_TO_KG * G)
                rows.append(('Sustained turn', f"{row['alt_ft']} ft, Mach {mach}", want, have, 0.15))
    return rows


def unpack(x):
    p = dict(zip(DRAG_NAMES, x[:len(DRAG_NAMES)]))
    p['table'] = np.reshape(x[len(DRAG_NAMES):], (len(TABLE_ALT_FT), len(TABLE_MACH))) * 1000.0
    return p


def pack(constants):
    return np.concatenate([[constants[name] for name in DRAG_NAMES], np.ravel(constants['thrust_kn'])])


def errors_in_tolerances(x, targets, cna, alpha0, gaps):
    rows = performance_rows(Model(unpack(x), cna, alpha0), targets)
    errors = []
    for test, condition, want, have, tolerance in rows:
        error = (have + gaps.get((test, condition), 0.0) - want) / tolerance
        # Only a shortfall counts at the Mach limit, since the chart follows the limit and spare power there is fine.
        errors.append(min(error - 1.0, 0.0) if test == 'Top speed, must reach limit Mach' else error)
    return np.array(errors)


def residuals(x, targets, cna, alpha0, gaps):
    errors = errors_in_tolerances(x, targets, cna, alpha0, gaps)
    shaped = (np.sign(errors) * (np.maximum(np.abs(errors) - INSIDE, 0.0) + EDGE_WEIGHT * np.maximum(np.abs(errors) - EDGE, 0.0))
              + 0.15 * errors)
    log_thrust = np.log(x[len(DRAG_NAMES):].reshape(len(TABLE_ALT_FT), len(TABLE_MACH)))
    # Thrust has no reason to change slope sharply between table points. The Mach spacing isn't even, so this compares slopes.
    mach_slope = np.diff(log_thrust, axis=1) / np.diff(TABLE_MACH_ARRAY) * 0.2
    return np.concatenate([shaped,
                           SMOOTHNESS * np.diff(log_thrust, 2, axis=0).ravel(),
                           SMOOTHNESS * np.diff(mach_slope, axis=1).ravel()])


def bench_gaps(targets, cna, alpha0, constants):
    """How far the last scorecard was from this model at the same constants, row by row."""
    scored = json.loads((HERE / 'results/scorecard.json').read_text(encoding='utf-8'))['rows']
    bench = {(row['group'], row['condition']): row['model'] for row in scored if row['model'] is not None}
    rows = performance_rows(Model(unpack(pack(constants)), cna, alpha0), targets)
    return {(test, condition): bench[(test, condition)] - have for test, condition, _, have, _ in rows
            if (test, condition) in bench}


def fit_fuel(targets, model):
    """Fuel per unit thrust, from the fuel used in the manual's tables:
    a + b x Mach + c x fraction of maximum thrust + d x altitude in units of 10 km.

    Idle flow is a floor in the EFM rather than an addition, so it doesn't enter this fit.
    """
    rows, values = [], []
    p = model.p
    hours = 1.0 / 9.81 / 3600.0

    def add_max_power(segments, fuel_lb):
        """segments: (Mach, altitude in m, seconds). All at maximum thrust, so the fraction is 1."""
        row = np.zeros(4)
        for mach, h, seconds in segments:
            amount = max_thrust(p, mach, h) * seconds * hours
            row += amount * np.array([1.0, mach, 1.0, h / 10000.0])
        rows.append(row)
        values.append(fuel_lb * LB_TO_KG)

    for table in targets['level_accel']['tables']:
        h = table['alt_ft'] * FT_TO_M
        for row in table['rows']:
            times = row['min']
            add_max_power([(mach_from_cas((table['kcas'][a] + table['kcas'][a - 1]) / 2.0, h), h, (times[a] - times[a - 1]) * 60.0)
                           for a in range(1, len(times))], row['fuel_lb'])
    block = targets['climb']
    for row in block['rows']:
        altitudes = [0.0] + block['alt_ft'][:len(row['min'])]
        times = [0.0] + row['min']
        segments = []
        for a in range(1, len(altitudes)):
            h = (altitudes[a] + altitudes[a - 1]) / 2.0 * FT_TO_M
            segments.append((min(mach_from_cas(block['cas_kt'], h), block['mach']), h, (times[a] - times[a - 1]) * 60.0))
        add_max_power(segments, row['fuel_lb'][-1])
    for row in targets['cruise_fuel_flow']['rows']:
        h = row['alt_ft'] * FT_TO_M
        mach = mach_from_cas(row['kcas'], h)
        weight = row['weight_lb'] * LB_TO_KG * G
        qs = 0.5 * isa(h)[2] * (mach * isa(h)[3]) ** 2 * S
        cn = weight / qs
        alpha = math.radians(model.alpha0 + cn / model.cna)
        cx = p['cd0'] + p['k1'] * cn + p['k'] * cn * cn + wave_drag(p, mach)
        thrust = (qs * cx + weight * math.tan(alpha)) / THRUST_ALIGNMENT
        rows.append(np.array([1.0, mach, thrust / max_thrust(p, mach, h), h / 10000.0]) * thrust / 9.81)
        values.append(row['lb_hr_engine'] * 2.0 * LB_TO_KG)
    rows, values = np.array(rows), np.array(values)
    weights = 1.0 / values
    # Only five rows give part-power flow, and their tolerance is the tightest, so they count for more.
    weights[-len(targets['cruise_fuel_flow']['rows']):] *= 2.0
    # Mach can't lower fuel per unit thrust, and altitude can't raise it, because the air gets colder. These are what jet engines do.
    solution = lsq_linear(rows * weights[:, None], values * weights,
                          bounds=([0.0, 0.0, 0.0, -np.inf], [np.inf, np.inf, np.inf, 0.0])).x
    errors = 100.0 * (rows @ solution - values) / values
    return solution, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bench', action='store_true', help='include the gap to the last scorecard, flown with fitted_constants.json')
    parser.add_argument('--evaluations', type=int, default=60)
    args = parser.parse_args()
    targets = json.loads((HERE / 'targets.json').read_text(encoding='utf-8'))
    start = json.loads((HERE / 'fitted_constants.json').read_text(encoding='utf-8'))
    cna, alpha0, _ = fit_lift(targets)
    gaps = bench_gaps(targets, cna, alpha0, start) if args.bench else {}
    x0 = pack(start)
    size = len(TABLE_ALT_FT) * len(TABLE_MACH)
    lower = DRAG_LOWER + [THRUST_LOWER_KN] * size
    upper = DRAG_UPPER + [THRUST_UPPER_KN] * size
    solved = least_squares(residuals, np.clip(x0, lower, upper), bounds=(lower, upper), args=(targets, cna, alpha0, gaps),
                           x_scale=np.maximum(np.abs(x0), 1e-3), diff_step=1e-3, max_nfev=args.evaluations)
    p = unpack(solved.x)
    model = Model(p, cna, alpha0)
    labels = performance_rows(model, targets)
    errors = errors_in_tolerances(solved.x, targets, cna, alpha0, gaps)
    print(f'Fit: {np.sum(np.abs(errors) <= 1.0)} of {len(errors)} points in tolerance, rms {np.sqrt(np.mean(errors * errors)):.2f} tolerances')
    for (test, condition, *_), error in zip(labels, errors):
        if abs(error) > 1.0:
            print(f'  {test}, {condition}: {error:+.2f} tolerances')
    print('\nDrag:')
    for name in DRAG_NAMES:
        print(f'  {name:14s} {p[name]:.6g}')
    print('\nThrust at maximum power, kN. Mach ' + ' '.join(f'{m:.2f}' for m in TABLE_MACH))
    for alt, row in zip(TABLE_ALT_FT, p['table'] / 1000.0):
        print(f'  {alt:6.0f} ft ' + ' '.join(f'{v:6.2f}' for v in row))
    fuel, fuel_errors = fit_fuel(targets, model)
    print(f'\nFuel: {fuel[0]:.4f} + {fuel[1]:.4f} x Mach + {fuel[2]:.4f} x thrust fraction {fuel[3]:+.4f} x altitude / 10 km, '
          f'kg per kgf per hour. Errors {fuel_errors.min():+.0f}% to {fuel_errors.max():+.0f}%')
    proposed = {name: float(p[name]) for name in DRAG_NAMES}
    proposed['thrust_kn'] = (p['table'] / 1000.0).round(3).tolist()
    proposed['fuel'] = [round(float(v), 4) for v in fuel]
    out = HERE / 'results/proposed_constants.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(proposed, indent=2) + '\n', encoding='utf-8')
    print(f'\nProposal written to {out}. After building it into the EFM, copy it over fitted_constants.json.')
    return proposed


if __name__ == '__main__':
    main()
