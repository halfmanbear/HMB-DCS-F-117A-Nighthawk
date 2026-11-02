#!/usr/bin/env python3
"""Fit the EFM's lift, drag, thrust and fuel constants to the flight manual's performance data.

This uses a point-mass model with the same equations as the EFM, so it runs in seconds. It proposes
constants to put in the EFM; scorecard.py then checks them on the built DLL, flight controls included.

    python tools/fm_bench/fit_performance.py
"""
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

NAMES = ['cd0', 'k1', 'k', 'mcrit', 'wave1', 'wave2', 't0', 'lapse_h', 'lapse_curve', 'mach1', 'mach2', 'mach_alt',
         'idle_sl', 'idle_per_10km', 'q_limit', 'q_cut']
# The fit has several local minima, so it runs from each of these and keeps the best.
STARTS = [
    [0.012, 0.0, 0.02, 0.80, 0.05, 0.10, 90000.0, 9000.0, 0.0, -0.13, 0.0, 0.1, -1000.0, 5000.0, 30000.0, 0.5],
    [0.0117, -0.01, -0.06, 0.87, 0.001, 0.026, 62000.0, 10000.0, 0.25, 0.40, 0.29, -0.31, -2500.0, 8800.0, 18300.0, 0.165],
    [0.013986, -0.0273, 0.0723, 0.8998, 0.00943, 0.00104, 79501.0, 13896.0, 0.3, 0.001, 0.0244, -0.215, 217.0, 7704.0, 19581.0, 0.098],
    [0.015, -0.01, 0.003, 0.88, 0.1, 0.016, 74670.0, 13307.0, 0.3, 0.066, -0.038, -0.2, -2500.0, 8800.0, 19655.0, 0.149],
]
LOWER = [0.005, -0.06, -0.2, 0.55, 0.0, 0.0, 60000.0, 6000.0, -0.3, -1.0, -1.0, -0.5, -10000.0, 0.0, 15000.0, 0.0]
UPPER = [0.05, 0.06, 0.5, 0.90, 3.0, 5.0, 95000.0, 14000.0, 0.3, 0.5, 1.0, 1.0, 10000.0, 30000.0, 50000.0, 3.0]
MDIV = 0.85
CHORD = 6.422  # The EFM's mean chord (m).
CZQ = -30.0  # About what the EFM's Czq table gives between 0 and 15 degrees.


def wave_drag(p, mach):
    """Same shape as the EFM: two quadratic rises scaled to the range up to Mach 1.05."""
    drag = 0.0
    if mach > p['mcrit']:
        drag += p['wave1'] * ((min(mach, 1.05) - p['mcrit']) / (1.05 - p['mcrit'])) ** 2
    if mach > MDIV:
        drag += p['wave2'] * ((min(mach, 1.05) - MDIV) / (1.05 - MDIV)) ** 2
    return drag


def max_thrust(p, mach, h):
    h = min(h, 13716.0)
    mach = max(mach, 0.27)  # The EFM adds thrust below Mach 0.30 for takeoff. The in-flight data starts here.
    # h is in units of 10 km where it shapes the curve, which keeps these constants a readable size.
    tens = h / 10000.0
    thrust = (p['t0'] * math.exp(-h / p['lapse_h'] - p['lapse_curve'] * tens * tens)
              * (1.0 + p['mach1'] * mach + (p['mach2'] + p['mach_alt'] * tens) * mach * mach))
    # The engines lose thrust at high dynamic pressure, seen at low altitude near the Mach limit.
    t, pressure, rho, sound = isa(h)
    q = 0.5 * rho * (mach * sound) ** 2
    return thrust * max(0.3, 1.0 - p['q_cut'] * max(0.0, q - p['q_limit']) / p['q_limit'])


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

    def accel_times(self, alt_ft, weight_lb, kcas, fuel_lb, end_min):
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


def residuals(x, targets, cna, alpha0):
    p = dict(zip(NAMES, x))
    model = Model(p, cna, alpha0)
    out = []
    for table in targets['level_accel']['tables']:
        for row in table['rows']:
            times = model.accel_times(table['alt_ft'], row['weight_lb'], table['kcas'], row['fuel_lb'], row['min'][-1])
            for want, have in zip(row['min'][1:], times[1:]):
                out.append((have - want) / max(0.15 * want, 0.1))
    block = targets['idle_decel']
    for row in block['rows']:
        times, total = model.decel_times(row['alt_ft'], block['weight_lb'], row['limit_mach'], row['kcas'])
        for want, have in zip(row['min'] + [row['limit_min']], times + [total]):
            out.append((have - want) / max(0.15 * want, 0.1))
    block = targets['climb']
    for row in block['rows']:
        altitudes = block['alt_ft'][:len(row['min'])]
        times = model.climb_times(row['weight_lb'], block['cas_kt'], block['mach'], altitudes, row['fuel_lb'])
        for want, have in zip(row['min'], times):
            out.append((have - want) / max(0.15 * want, 0.1))
    block = targets['service_ceiling']
    for row in block['rows']:
        h = row['alt_ft'] * FT_TO_M
        weight = (row['initial_weight_lb'] - row['fuel_lb']) * LB_TO_KG * G
        excess, V = model.specific_excess(max_thrust(p, block['mach'], h), block['mach'], h, weight)
        out.append((excess * V - 0.508) / 1.0)
    # Top speed where thrust sets it: no excess power there.
    for row in targets['max_level_speed']['thrust_limited']:
        h = row['alt_ft'] * FT_TO_M
        mach = mach_from_cas(row['kcas'], h)
        excess, V = model.specific_excess(max_thrust(p, mach, h), mach, h, row['weight_lb'] * LB_TO_KG * G)
        out.append(excess * V / 1.5)
    # Below those points the chart follows the Mach limit, so the aircraft must be able to reach it.
    for row in targets['max_level_speed']['reaches_limit_mach']:
        h = row['alt_ft'] * FT_TO_M
        excess, V = model.specific_excess(max_thrust(p, row['mach'], h), row['mach'], h, row['weight_lb'] * LB_TO_KG * G)
        out.append(min(excess * V, 0.0) / 1.5)
    block = targets['sustained_turn']
    for row in block['rows']:
        h = row['alt_ft'] * FT_TO_M
        for mach, want in zip(block['mach'], row['g']):
            if want is not None:
                have = model.sustained_g(mach, h, block['weight_lb'] * LB_TO_KG * G)
                out.append((have - want) / 0.15)
    return np.array(out)


def fit_fuel(targets, model):
    """Fuel per unit thrust, from the fuel used in the manual's tables: a + b x Mach + c x fraction of maximum thrust.

    Idle flow is a floor in the EFM rather than an addition, so it doesn't enter this fit.
    """
    rows, values = [], []
    p = model.p
    for table in targets['level_accel']['tables']:
        h = table['alt_ft'] * FT_TO_M
        for row in table['rows']:
            # Mean thrust and Mach over the run, weighted by the time spent at each speed.
            times = row['min']
            thrust_time, mach_time = 0.0, 0.0  # All at maximum thrust, so the fraction is 1.
            for a in range(1, len(times)):
                mach = mach_from_cas((table['kcas'][a] + table['kcas'][a - 1]) / 2.0, h)
                dt = (times[a] - times[a - 1]) * 60.0
                thrust_time += max_thrust(p, mach, h) * dt
                mach_time += max_thrust(p, mach, h) * mach * dt
            rows.append([thrust_time / 9.81 / 3600.0, mach_time / 9.81 / 3600.0, thrust_time / 9.81 / 3600.0])
            values.append(row['fuel_lb'] * LB_TO_KG)
    for row in targets['cruise_fuel_flow']['rows']:
        h = row['alt_ft'] * FT_TO_M
        mach = mach_from_cas(row['kcas'], h)
        weight = row['weight_lb'] * LB_TO_KG * G
        qs = 0.5 * isa(h)[2] * (mach * isa(h)[3]) ** 2 * S
        cn = weight / qs
        alpha = math.radians(model.alpha0 + cn / model.cna)
        cx = p['cd0'] + p['k1'] * cn + p['k'] * cn * cn + wave_drag(p, mach)
        thrust = (qs * cx + weight * math.tan(alpha)) / THRUST_ALIGNMENT
        rows.append([thrust / 9.81, thrust / 9.81 * mach, thrust / 9.81 * thrust / max_thrust(p, mach, h)])
        values.append(row['lb_hr_engine'] * 2.0 * LB_TO_KG)
    rows, values = np.array(rows), np.array(values)
    weights = 1.0 / values
    # Mach can't lower fuel per unit thrust: the data alone would make it fall with Mach, which no jet engine does.
    solution = lsq_linear(rows * weights[:, None], values * weights, bounds=([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf])).x
    errors = 100.0 * (rows @ solution - values) / values
    return solution, errors


def main():
    targets = json.loads((HERE / 'targets.json').read_text(encoding='utf-8'))
    cna, alpha0, points = fit_lift(targets)
    print(f'Lift: CN = {cna:.4f} per deg x (AOA - {alpha0:.2f} deg)')
    for cn, aoa in points:
        print(f'  CN {cn:.3f}  manual {aoa:.1f}  line {alpha0 + cn / cna:.2f}')
    solved = min((least_squares(residuals, start, bounds=(LOWER, UPPER), args=(targets, cna, alpha0),
                                x_scale=[max(abs(v), 1e-3) for v in start], diff_step=1e-3, loss='soft_l1', max_nfev=200)
                  for start in STARTS), key=lambda result: result.cost)
    p = dict(zip(NAMES, solved.x))
    print('\nFitted constants:')
    for name, value in p.items():
        print(f'  {name:10s} {value:.5g}')
    print(f"  (fixed: Mdiv {MDIV})")
    raw = residuals(solved.x, targets, cna, alpha0)
    print(f'\nFit quality: {len(raw)} points, {100.0 * np.mean(np.abs(raw) <= 1.0):.0f}% in tolerance, '
          f'rms {np.sqrt(np.mean(raw * raw)):.2f} tolerances')
    model = Model(p, cna, alpha0)
    fuel, errors = fit_fuel(targets, model)
    print(f'\nFuel: {fuel[0]:.3f} + {fuel[1]:.3f} x Mach + {fuel[2]:.3f} x thrust fraction, kg per kgf per hour. Errors {errors.min():+.0f}% to {errors.max():+.0f}%')
    print('\nThrust at maximum power (kN):')
    print('  ft       M0.0   M0.3   M0.5   M0.7   M0.9')
    for alt in (0, 10000, 20000, 30000, 40000):
        print(f'  {alt:6d} ' + ' '.join(f'{max_thrust(p, m, alt * FT_TO_M) / 1000:6.1f}' for m in (0.0, 0.3, 0.5, 0.7, 0.9)))
    print('\nDrag coefficient at 1 g, 32,000 lb, 10,000 ft:')
    for m in (0.3, 0.5, 0.7, 0.8, 0.85, 0.9):
        h = 10000 * FT_TO_M
        qs = 0.5 * isa(h)[2] * (m * isa(h)[3]) ** 2 * S
        cn = 32000 * LB_TO_KG * G / qs
        alpha = math.radians(alpha0 + cn / cna)
        cx = p['cd0'] + p['k1'] * cn + p['k'] * cn * cn + wave_drag(p, m)
        cd = cx * math.cos(alpha) + cn * math.sin(alpha)
        print(f'  M{m:.2f}  CL {cn:.3f}  CD {cd:.4f}  L/D {cn / cd:.1f}')
    return p


if __name__ == '__main__':
    main()
