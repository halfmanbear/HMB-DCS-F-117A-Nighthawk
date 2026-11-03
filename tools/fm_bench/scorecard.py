#!/usr/bin/env python3
"""Fly the built EFM through the flight manual's test conditions and score it against them.

    python tools/fm_bench/scorecard.py
    python tools/fm_bench/scorecard.py --only turn,accel --inertia 40000,260000,225000

Results go to tools/fm_bench/results/: scorecard.md, scorecard.csv and scorecard.json.
"""
import argparse
import csv
import json
import os
import shutil
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import efm as efm_module  # noqa: E402
import scenarios  # noqa: E402
from sim import Sim  # noqa: E402

RESULTS = HERE / 'results'
_sim = None


def read_inertia():
    """Roll, yaw and pitch inertia from the mod's FM/config.lua, as DCS reads them."""
    from lupa import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute((efm_module.MOD_ROOT / 'FM/config.lua').read_text(encoding='utf-8'))
    values = lua.globals().FM.moment_of_inertia
    return values[1], values[2], values[3]


def _start_worker(dll, inertia, root):
    global _sim
    work = Path(tempfile.mkdtemp(dir=root))
    _sim = Sim(efm_module.Efm(dll, work), inertia)


def _run(job):
    name, kwargs = job
    return getattr(scenarios, name)(_sim, **kwargs)


def build_jobs(targets, groups):
    """Each job is (key, scenario, arguments). The key finds the target again when results come back."""
    jobs = []
    if 'accel' in groups:
        for table in targets['level_accel']['tables']:
            for row in table['rows']:
                jobs.append((('accel', table['alt_ft'], row['weight_lb']), 'level_accel', dict(
                    alt_ft=table['alt_ft'], weight_lb=row['weight_lb'], kcas=table['kcas'],
                    timeout_s=row['min'][-1] * 60.0 * 3.0 + 60.0)))
    if 'decel' in groups:
        block = targets['idle_decel']
        for row in block['rows']:
            jobs.append((('decel', row['alt_ft']), 'idle_decel', dict(
                alt_ft=row['alt_ft'], weight_lb=block['weight_lb'], limit_mach=row['limit_mach'], kcas=row['kcas'])))
    if 'climb' in groups:
        block = targets['climb']
        for row in block['rows']:
            altitudes = block['alt_ft'][:len(row['min'])]
            jobs.append((('climb', row['weight_lb']), 'climb', dict(
                weight_lb=row['weight_lb'], cas_kt=block['cas_kt'], mach=block['mach'], alt_ft=altitudes,
                timeout_s=row['min'][-1] * 60.0 * 3.0 + 120.0)))
    if 'ceiling' in groups:
        block = targets['service_ceiling']
        for row in block['rows']:
            jobs.append((('ceiling', row['initial_weight_lb']), 'service_ceiling', dict(
                weight_lb=row['initial_weight_lb'] - row['fuel_lb'], mach=block['mach'], guess_ft=row['alt_ft'])))
    if 'turn' in groups:
        block = targets['sustained_turn']
        for row in block['rows']:
            for mach, g in zip(block['mach'], row['g']):
                if g is not None:
                    jobs.append((('turn', row['alt_ft'], mach), 'sustained_turn', dict(
                        weight_lb=block['weight_lb'], alt_ft=row['alt_ft'], mach=mach, guess_g=g)))
    if 'vmax' in groups:
        block = targets['max_level_speed']
        for row in block['thrust_limited']:
            jobs.append((('vmax_thrust', row['weight_lb'], row['alt_ft'], row['kcas']), 'thrust_limited', dict(
                weight_lb=row['weight_lb'], alt_ft=row['alt_ft'], kcas=row['kcas'])))
        for row in block['reaches_limit_mach']:
            jobs.append((('vmax_limit', row['weight_lb'], row['alt_ft'], row['mach']), 'reach_limit_mach', dict(
                weight_lb=row['weight_lb'], alt_ft=row['alt_ft'], mach=row['mach'])))
    if 'aoa' in groups:
        for row in targets['trim_aoa']['rows']:
            jobs.append((('aoa', row['weight_lb'], row['kcas'], row['alt_ft'], row['gear_down']), 'trim_aoa', dict(
                weight_lb=row['weight_lb'], kcas=row['kcas'], alt_ft=row['alt_ft'], gear_down=row['gear_down'])))
    if 'fuelflow' in groups:
        for row in targets['cruise_fuel_flow']['rows']:
            jobs.append((('fuelflow', row['weight_lb'], row['kcas'], row['alt_ft']), 'steady_fuel_flow', dict(
                weight_lb=row['weight_lb'], kcas=row['kcas'], alt_ft=row['alt_ft'])))
    if 'roll' in groups:
        block = targets['roll_rate']
        for row in block['rows']:
            for side in (1.0, -1.0):
                jobs.append((('roll', row['kcas'], side), 'roll_rate', dict(
                    weight_lb=block['weight_lb'], kcas=row['kcas'], alt_ft=block['alt_ft'], side=side)))
                jobs.append((('roll_stop', row['kcas'], side), 'roll_stop', dict(
                    weight_lb=block['weight_lb'], kcas=row['kcas'], alt_ft=block['alt_ft'], side=side)))
    if 'sideslip' in groups:
        block = targets['sideslip']
        for row in block['rows']:
            for side in (1.0, -1.0):
                jobs.append((('sideslip', row['kcas'], side), 'sideslip', dict(
                    weight_lb=block['weight_lb'], kcas=row['kcas'], alt_ft=block['alt_ft'], side=side)))
    if 'g' in groups:
        block = targets['load_factor']
        for row in block['rows']:
            jobs.append((('g', row['kcas']), 'load_factor', dict(
                weight_lb=block['weight_lb'], kcas=row['kcas'], alt_ft=block['alt_ft'])))
    if 'limit' in groups:
        block = targets['aoa_limit']
        for row in block['rows']:
            jobs.append((('limit', row['mach'], row['gear_down']), 'aoa_limit', dict(
                weight_lb=block['weight_lb'], mach=row['mach'], alt_ft=row['alt_ft'], gear_down=row['gear_down'])))
    return jobs


def _row(group, condition, unit, target, model, tolerance):
    """One compared value. The tolerance is how close a chart reading or printed figure can be trusted."""
    error = None if model is None else model - target
    return {'group': group, 'condition': condition, 'unit': unit, 'target': target, 'model': model,
            'error': error, 'percent': None if error is None or target == 0 else 100.0 * error / abs(target),
            'ok': error is not None and abs(error) <= tolerance}


def score(targets, results, groups):
    rows = []
    if 'accel' in groups:
        for table in targets['level_accel']['tables']:
            for row in table['rows']:
                got = results[('accel', table['alt_ft'], row['weight_lb'])]
                where = f"{table['alt_ft']} ft, {row['weight_lb']} lb"
                for kcas, want, have in zip(table['kcas'][1:], row['min'][1:], got['min'][1:]):
                    rows.append(_row('Level acceleration', f"{where}, to {kcas} KCAS", 'min', want, have,
                                     max(0.1, 0.1 * want)))
                rows.append(_row('Fuel in acceleration', where, 'lb', row['fuel_lb'], got['fuel_lb'] if got['min'][-1] else None,
                                 0.12 * row['fuel_lb']))
    if 'decel' in groups:
        for row in targets['idle_decel']['rows']:
            got = results[('decel', row['alt_ft'])]
            where = f"{row['alt_ft']} ft"
            for kcas, want, have in zip(row['kcas'], row['min'], got['min']):
                rows.append(_row('Idle deceleration', f"{where}, from {kcas} KCAS", 'min', want, have, max(0.1, 0.1 * want)))
            rows.append(_row('Idle deceleration', f"{where}, from limit Mach", 'min', row['limit_min'], got['limit_min'],
                             max(0.1, 0.1 * row['limit_min'])))
    if 'climb' in groups:
        block = targets['climb']
        for row in block['rows']:
            got = results[('climb', row['weight_lb'])]
            for alt, want, have in zip(block['alt_ft'], row['min'], got['min']):
                rows.append(_row('Climb time', f"{row['weight_lb']} lb, to {alt} ft", 'min', want, have, max(0.1, 0.1 * want)))
            for alt, want, have in zip(block['alt_ft'], row['fuel_lb'], got['fuel_lb']):
                rows.append(_row('Fuel in climb', f"{row['weight_lb']} lb, to {alt} ft", 'lb', want, have, 0.12 * want))
    if 'ceiling' in groups:
        for row in targets['service_ceiling']['rows']:
            got = results[('ceiling', row['initial_weight_lb'])]
            rows.append(_row('Service ceiling', f"{row['initial_weight_lb']} lb at start", 'ft', row['alt_ft'], got['alt_ft'], 1000.0))
    if 'turn' in groups:
        block = targets['sustained_turn']
        for row in block['rows']:
            for mach, want in zip(block['mach'], row['g']):
                if want is not None:
                    got = results[('turn', row['alt_ft'], mach)]
                    rows.append(_row('Sustained turn', f"{row['alt_ft']} ft, Mach {mach}", 'g', want, got['g'], 0.15))
    if 'vmax' in groups:
        block = targets['max_level_speed']
        for row in block['thrust_limited']:
            got = results[('vmax_thrust', row['weight_lb'], row['alt_ft'], row['kcas'])]
            rows.append(_row('Top speed, excess power at the limit', f"{row['weight_lb']} lb, {row['alt_ft']} ft, {row['kcas']} KCAS",
                             'ft/min', 0.0, got['ps'] / 0.3048 * 60.0, 300.0))
        for row in block['reaches_limit_mach']:
            got = results[('vmax_limit', row['weight_lb'], row['alt_ft'], row['mach'])]
            ok_value = got['ps'] / 0.3048 * 60.0
            item = _row('Top speed, must reach limit Mach', f"{row['weight_lb']} lb, {row['alt_ft']} ft, Mach {row['mach']}",
                        'ft/min', 0.0, ok_value, 0.0)
            item['ok'] = ok_value >= 0.0
            rows.append(item)
    if 'aoa' in groups:
        for row in targets['trim_aoa']['rows']:
            got = results[('aoa', row['weight_lb'], row['kcas'], row['alt_ft'], row['gear_down'])]
            gear = 'gear down' if row['gear_down'] else 'gear up'
            rows.append(_row('Angle of attack in level flight', f"{row['weight_lb']} lb, {row['kcas']} KCAS, {row['alt_ft']} ft, {gear}",
                             'deg', row['aoa'], got['aoa'], 0.5))
    if 'fuelflow' in groups:
        for row in targets['cruise_fuel_flow']['rows']:
            got = results[('fuelflow', row['weight_lb'], row['kcas'], row['alt_ft'])]
            flow = got['fuel_kg_s'] * 3600.0 / 0.45359237 / 2.0
            rows.append(_row('Cruise fuel flow', f"{row['weight_lb']} lb, {row['kcas']} KCAS, {row['alt_ft']} ft",
                             'lb/hr/engine', row['lb_hr_engine'], flow, 0.1 * row['lb_hr_engine']))
    if 'roll' in groups:
        for row in targets['roll_rate']['rows']:
            for side, label in ((1.0, 'right'), (-1.0, 'left')):
                got = results[('roll', row['kcas'], side)]
                rows.append(_row('Roll rate', f"{row['kcas']} KCAS, {label}", 'deg/s', row['dps'], got['dps'], 0.1 * row['dps']))
                got = results[('roll_stop', row['kcas'], side)]
                # The manual gives no figures for these. They check that the roll stops cleanly when the stick is released.
                rows.append(_row('Roll rate reversal after release', f"{row['kcas']} KCAS, {label}", 'deg/s', 0.0, got['reversal'], 5.0))
                rows.append(_row('Roll rate swing, 1 to 3 s after release', f"{row['kcas']} KCAS, {label}", 'deg/s', 0.0, got['late_swing'], 2.0))
    if 'sideslip' in groups:
        for row in targets['sideslip']['rows']:
            for side, label in ((1.0, 'one way'), (-1.0, 'other way')):
                got = results[('sideslip', row['kcas'], side)]
                rows.append(_row('Full-pedal sideslip', f"{row['kcas']} KCAS, {label}", 'deg', row['deg'], abs(got['deg']), 1.0))
    if 'g' in groups:
        for row in targets['load_factor']['rows']:
            got = results[('g', row['kcas'])]
            rows.append(_row('Full aft stick', f"{row['kcas']} KCAS", 'g', row['g'], got['g'], 0.3))
    if 'limit' in groups:
        for row in targets['aoa_limit']['rows']:
            got = results[('limit', row['mach'], row['gear_down'])]
            gear = 'gear down' if row['gear_down'] else 'gear up'
            rows.append(_row('Angle of attack limit', f"Mach {row['mach']}, {gear}", 'deg', row['aoa'], got['aoa'], 0.7))
            # The manual says the limit is reached with little or no overshoot.
            rows.append(_row('Overshoot past the AOA limit', f"Mach {row['mach']}, {gear}", 'deg', 0.0, max(0.0, got['peak'] - row['aoa']), 1.5))
            rows.append(_row('Load factor swing at the AOA limit', f"Mach {row['mach']}, {gear}", 'g', 0.0, got['nz_swing'], 0.4))
    return rows


def write_outputs(rows, meta):
    RESULTS.mkdir(exist_ok=True)
    groups = []
    for row in rows:
        if row['group'] not in groups:
            groups.append(row['group'])
    lines = ['# Flight model scorecard', '', f"EFM `{meta['dll']}`", f"Inertia (roll, yaw, pitch): {meta['inertia']}", '',
             '| Test | In tolerance | Mean error | Mean bias |', '|---|---|---|---|']
    for group in groups:
        members = [r for r in rows if r['group'] == group]
        have = [r for r in members if r['percent'] is not None]
        missed = len(members) - len([r for r in members if r['model'] is not None])
        mean_abs = sum(abs(r['percent']) for r in have) / len(have) if have else float('nan')
        mean_bias = sum(r['percent'] for r in have) / len(have) if have else float('nan')
        note = f" ({missed} not reached)" if missed else ''
        passed = sum(1 for r in members if r['ok'])
        size = f"{mean_abs:.0f}% | {mean_bias:+.0f}%" if have else "target is zero, see below | "
        lines.append(f"| {group} | {passed} of {len(members)}{note} | {size} |")
    for group in groups:
        lines += ['', f'## {group}', '', '| Condition | Manual | Model | Error | |', '|---|---|---|---|---|']
        for r in [r for r in rows if r['group'] == group]:
            model = 'not reached' if r['model'] is None else f"{r['model']:.2f}"
            error = '' if r['error'] is None else f"{r['error']:+.2f} {r['unit']}"
            lines.append(f"| {r['condition']} | {r['target']:g} | {model} | {error} | {'ok' if r['ok'] else 'off'} |")
    (RESULTS / 'scorecard.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    with open(RESULTS / 'scorecard.csv', 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (RESULTS / 'scorecard.json').write_text(json.dumps({'meta': meta, 'rows': rows}, indent=1), encoding='utf-8')
    return lines


def main():
    all_groups = ['accel', 'decel', 'climb', 'ceiling', 'turn', 'vmax', 'aoa', 'fuelflow', 'roll', 'sideslip', 'g', 'limit']
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dll', type=Path, help='EFM DLL to test (default: the build the mod uses)')
    parser.add_argument('--only', default=','.join(all_groups), help=f"tests to run, from: {','.join(all_groups)}")
    parser.add_argument('--inertia', help='roll,yaw,pitch inertia in kg m2 (default: FM/config.lua)')
    parser.add_argument('--workers', type=int, default=max(1, min(16, (os.cpu_count() or 2) - 2)))
    args = parser.parse_args()

    groups = args.only.split(',')
    unknown = set(groups) - set(all_groups)
    if unknown:
        parser.error(f"unknown tests: {', '.join(sorted(unknown))}")
    dll = args.dll or efm_module.default_dll()
    inertia = tuple(float(v) for v in args.inertia.split(',')) if args.inertia else read_inertia()
    efm_module.build_stub()
    targets = json.loads((HERE / 'targets.json').read_text(encoding='utf-8'))
    jobs = build_jobs(targets, groups)

    started = time.perf_counter()
    root = tempfile.mkdtemp(prefix='fm_bench_')
    results = {}
    failures = []
    try:
        with ProcessPoolExecutor(args.workers, initializer=_start_worker, initargs=(dll, inertia, root)) as pool:
            pending = {pool.submit(_run, (name, kwargs)): key for key, name, kwargs in jobs}
            for future in as_completed(pending):
                key = pending[future]
                try:
                    results[key] = future.result()
                except Exception as error:  # A diverged test shouldn't lose the rest of the scorecard.
                    failures.append((key, repr(error)))
                print(f'\r{len(results) + len(failures)} of {len(jobs)} tests flown', end='', flush=True, file=sys.stderr)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(file=sys.stderr)
    print(f'{len(jobs)} tests flown in {time.perf_counter() - started:.0f} s')
    for key, error in failures:
        print('FAILED', key, error)
    if failures:
        raise SystemExit(1)

    rows = score(targets, results, groups)
    lines = write_outputs(rows, {'dll': str(dll), 'inertia': list(inertia)})
    table_end = next((i for i, line in enumerate(lines) if line.startswith('## ')), len(lines))
    print('\n'.join(lines[:table_end]))
    print(f'Details: {RESULTS / "scorecard.md"}')


if __name__ == '__main__':
    main()
