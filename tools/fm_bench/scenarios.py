"""One flight test per function. Each flies the EFM once or more and returns measured values."""
import math

from sim import DT, FT_TO_M, G, LB_TO_KG, RAD, Pilot, isa, mach_from_cas

SPIN_UP_S = 8.0  # Engine and flight controls settle at a fixed speed before a timed run starts.


def _level(sim, weight_lb, alt_ft, mach, seconds=SPIN_UP_S, throttle=1.0, gear_down=False):
    """Start at a fixed speed in level flight and let everything settle."""
    h = alt_ft * FT_TO_M
    sim.start(weight_lb, h, mach, throttle=throttle, gear_down=gear_down, freeze_speed=True)
    pilot = Pilot(sim)
    pilot.hold_alt = h
    pilot.fly(seconds)
    return pilot


def _average(pilot, seconds, *fields):
    sim = pilot.sim
    totals = [0.0] * len(fields)
    count = [0]

    def add(_):
        for i, field in enumerate(fields):
            totals[i] += getattr(sim, field)
        count[0] += 1

    pilot.fly(seconds, add)
    return [total / count[0] for total in totals]


def _release_speed(sim):
    """Start the timed part of a run: speed free, fuel burning, clock at zero."""
    sim.freeze_speed = False
    sim.efm.unlimited_fuel(False)
    sim.fuel_used = 0.0
    sim.t = 0.0


def level_accel(sim, alt_ft, weight_lb, kcas, timeout_s):
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas[0], alt_ft * FT_TO_M))
    _release_speed(sim)
    times = [0.0] + [None] * (len(kcas) - 1)
    next_point = [1]

    def watch(s):
        while next_point[0] < len(kcas) and s.cas >= kcas[next_point[0]]:
            times[next_point[0]] = s.t / 60.0
            next_point[0] += 1
        return next_point[0] >= len(kcas)

    pilot.fly(timeout_s, watch)
    return {'min': times, 'fuel_lb': sim.fuel_used / LB_TO_KG, 'end_kcas': sim.cas}


def idle_decel(sim, alt_ft, weight_lb, limit_mach, kcas):
    pilot = _level(sim, weight_lb, alt_ft, limit_mach, throttle=0.0)
    _release_speed(sim)
    points = sorted(kcas, reverse=True)
    crossings = {}
    start_cas = sim.cas

    def watch(s):
        for point in points:
            if point not in crossings and s.cas <= point:
                crossings[point] = s.t
        return s.cas <= 200.0

    pilot.fly(600.0, watch)
    end = sim.t
    return {'min': [None if k > start_cas else (end - crossings.get(k, 0.0)) / 60.0 for k in kcas],
            'limit_min': end / 60.0}


def climb(sim, weight_lb, cas_kt, mach, alt_ft, timeout_s):
    h0 = 50.0 * FT_TO_M
    pilot = _level(sim, weight_lb, 50.0, mach_from_cas(cas_kt, h0))
    _release_speed(sim)

    def schedule(h):
        _, _, _, sound = isa(h)
        return min(mach_from_cas(cas_kt, h), mach) * sound

    pilot.speed_schedule = schedule
    times = [None] * len(alt_ft)
    fuel = [None] * len(alt_ft)
    next_point = [0]

    def watch(s):
        while next_point[0] < len(alt_ft) and s.h >= alt_ft[next_point[0]] * FT_TO_M:
            times[next_point[0]] = s.t / 60.0
            fuel[next_point[0]] = s.fuel_used / LB_TO_KG
            next_point[0] += 1
        return next_point[0] >= len(alt_ft)

    pilot.fly(timeout_s, watch)
    return {'min': times, 'fuel_lb': fuel}


def excess_power(sim, weight_lb, alt_ft, mach, seconds=14.0):
    pilot = _level(sim, weight_lb, alt_ft, mach, seconds=seconds)
    ps, alpha, thrust = _average(pilot, 4.0, 'ps', 'alpha', 'thrust')
    return {'ps': ps, 'alpha': alpha, 'thrust': thrust}


def service_ceiling(sim, weight_lb, mach, guess_ft):
    """Altitude where excess power falls to 100 ft/min."""
    target = 100.0 * FT_TO_M / 60.0
    h0, h1 = guess_ft, guess_ft - 3000.0
    p0 = excess_power(sim, weight_lb, h0, mach)['ps'] - target
    p1 = excess_power(sim, weight_lb, h1, mach)['ps'] - target
    for _ in range(4):
        if abs(p1 - p0) < 1e-6:
            break
        h2 = max(0.0, min(50000.0, h1 - p1 * (h1 - h0) / (p1 - p0)))
        h0, p0 = h1, p1
        h1, p1 = h2, excess_power(sim, weight_lb, h2, mach)['ps'] - target
        if abs(p1) < 0.1:
            break
    return {'alt_ft': h1}


def _turn_point(sim, weight_lb, alt_ft, mach, g):
    """Excess power in a steady turn. The pilot flies the load factor and keeps the turn level with bank, because
    holding altitude with the stick doesn't settle in a steep bank."""
    pilot = _level(sim, weight_lb, alt_ft, mach, seconds=6.0)
    if g > 1.0001:
        started = sim.t

        def fly_turn(s):
            nz = 1.0 + (g - 1.0) * min((s.t - started) / 3.0, 1.0)
            pilot.nz_cmd = nz
            pilot.bank = math.degrees(math.acos(1.0 / nz)) + max(-5.0, min(5.0, s.vs))

        pilot.fly(16.0, fly_turn)
        ps, nz, alpha = _average(pilot, 4.0, 'ps', 'nz', 'alpha')
    else:
        pilot.fly(16.0)
        ps, nz, alpha = _average(pilot, 4.0, 'ps', 'nz', 'alpha')
    return nz, ps, alpha


def sustained_turn(sim, weight_lb, alt_ft, mach, guess_g):
    """Load factor where a level turn at fixed Mach uses all the excess power."""
    n0, p0, _ = _turn_point(sim, weight_lb, alt_ft, mach, 1.0)
    n1, p1, alpha = _turn_point(sim, weight_lb, alt_ft, mach, max(guess_g, 1.3))
    if p0 <= 0.0:
        # It can't hold 1 g. The same straight line, run below 1 g, shows by how much.
        squared = n0 * n0 - p0 * (n1 * n1 - n0 * n0) / (p1 - p0)
        return {'g': math.sqrt(max(squared, 0.0)), 'ps_1g': p0, 'alpha': alpha}
    for _ in range(4):
        # Excess power falls almost linearly with load factor squared.
        if abs(p1 - p0) < 1e-6:
            break
        squared = n1 * n1 - p1 * (n1 * n1 - n0 * n0) / (p1 - p0)
        n2 = math.sqrt(max(squared, 1.0))
        n0, p0 = n1, p1
        n1, p1, alpha = _turn_point(sim, weight_lb, alt_ft, mach, n2)
        if abs(p1) < 1.0:
            break
    squared = n1 * n1 - p1 * (n1 * n1 - n0 * n0) / (p1 - p0) if abs(p1 - p0) > 1e-6 else n1 * n1
    return {'g': math.sqrt(max(squared, 1.0)), 'ps_1g': None, 'alpha': alpha}


def trim_aoa(sim, weight_lb, kcas, alt_ft, gear_down):
    h = alt_ft * FT_TO_M
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas, h), seconds=30.0 if gear_down else 12.0,
                   gear_down=gear_down)
    alpha, nz, thrust = _average(pilot, 3.0, 'alpha', 'nz', 'thrust')
    return {'aoa': alpha, 'nz': nz}


def steady_fuel_flow(sim, weight_lb, kcas, alt_ft):
    """Fuel flow in level flight at a fixed speed, with the throttle solved for zero excess power."""
    h = alt_ft * FT_TO_M
    mach = mach_from_cas(kcas, h)
    low, high = 0.0, 1.0
    for _ in range(9):
        middle = (low + high) / 2.0
        pilot = _level(sim, weight_lb, alt_ft, mach, seconds=10.0, throttle=middle)
        ps, thrust = _average(pilot, 2.0, 'ps', 'thrust')
        if abs(ps) < 0.02:
            break
        if ps > 0.0:
            high = middle
        else:
            low = middle
    sim.efm.unlimited_fuel(False)
    sim.fuel_used = 0.0
    before = sim.t
    pilot.fly(4.0)
    return {'fuel_kg_s': sim.fuel_used / (sim.t - before), 'thrust_n': thrust}


def roll_rate(sim, weight_lb, kcas, alt_ft, side):
    h = alt_ft * FT_TO_M
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas, h), seconds=8.0, throttle=0.8)
    pilot.pitch_axis = 0.0  # Stick free in pitch, which is how the manual's 1 g figure would be flown.
    pilot.roll_axis = side
    peak = [0.0]
    alpha_peak = [0.0]
    turned = [0.0]
    last = [sim.roll]

    def watch(s):
        peak[0] = max(peak[0], abs(s.p) / RAD)
        alpha_peak[0] = max(alpha_peak[0], s.alpha)
        change = (s.roll - last[0] + 180.0) % 360.0 - 180.0
        turned[0] += abs(change)
        last[0] = s.roll
        return turned[0] >= 360.0

    finished = pilot.fly(20.0, watch)
    return {'dps': peak[0], 'completed': finished, 'alpha_peak': alpha_peak[0]}


def ground_bumps(sim, weight_lb=46000.0, kcas=150.0, alt_ft=1000.0):
    """Shake the roll rate and load factor at 5 Hz, as a runway does, with the wheels reported on and off the ground.

    The bench has no gear, so this checks the flight controls' response only. Returns the swing in roll and
    pitch moment (kN m) from the shaking, and the roll moment from full stick with the wheels down.
    """
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas, alt_ft * FT_TO_M), seconds=4.0, gear_down=True)
    pilot.pitch_axis = 0.0
    pilot.roll_axis = 0.0

    def shake(on_ground, seconds=1.0):
        rolls, pitches = [], []
        for i in range(int(seconds / DT)):
            wave = math.sin(2.0 * math.pi * 5.0 * i * DT)
            sim.efm.wheel_contact(on_ground)
            sim.p = 6.0 * RAD * wave
            sim.q = 0.0
            sim.ay = 0.3 * G * wave
            pilot.update()
            sim.step()
            mx, _, mz = sim.efm.moments()
            rolls.append(mx / 1000.0)
            pitches.append(mz / 1000.0)
        return max(rolls) - min(rolls), max(pitches) - min(pitches)

    air_roll, air_pitch = shake(False)
    shake(True, 0.6)
    ground_roll, ground_pitch = shake(True)
    pilot.roll_axis = 1.0
    moments = []
    for _ in range(int(0.5 / DT)):
        sim.efm.wheel_contact(True)
        sim.p = sim.q = sim.r = 0.0
        pilot.update()
        sim.step()
        moments.append(abs(sim.efm.moments()[0]) / 1000.0)
    pilot.roll_axis = 0.0
    shake(False, 0.6)
    after_roll, after_pitch = shake(False)
    return {'air_roll': air_roll, 'air_pitch': air_pitch, 'ground_roll': ground_roll, 'ground_pitch': ground_pitch,
            'ground_stick_roll': max(moments), 'after_roll': after_roll, 'after_pitch': after_pitch}


def roll_stop(sim, weight_lb, kcas, alt_ft, side):
    """Full stick for 3 seconds, then let go: how far the roll rate reverses and whether it settles."""
    h = alt_ft * FT_TO_M
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas, h), seconds=8.0, throttle=0.8)
    pilot.pitch_axis = 0.0
    pilot.roll_axis = side
    pilot.fly(3.0)
    pilot.roll_axis = 0.0
    rates = []

    def watch(s):
        rates.append(side * s.p / RAD)

    pilot.fly(3.0, watch)
    late = rates[int(1.0 / DT):]
    return {'reversal': max(0.0, -min(rates)), 'late_swing': max(late) - min(late)}


def sideslip(sim, weight_lb, kcas, alt_ft, side):
    h = alt_ft * FT_TO_M
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas, h), seconds=6.0)
    pilot.yaw_axis = side
    pilot.fly(12.0)
    beta, roll = _average(pilot, 3.0, 'beta', 'roll')
    return {'deg': beta, 'bank': roll}


def pedal_step(sim, weight_lb, kcas, alt_ft, side):
    """Half pedal for 6 seconds, then let go: how far the sideslip overshoots, in percent of the steady value.

    TO 1F-117A-1 page 6-1 says the flight controls give "essentially dead-beat damping in all three axes".
    """
    h = alt_ft * FT_TO_M
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas, h), seconds=6.0)
    pilot.yaw_axis = 0.5 * side
    held = []
    pilot.fly(6.0, lambda s: held.append(s.beta))
    steady = sum(held[-int(0.9 / DT):]) / int(0.9 / DT)
    pilot.yaw_axis = 0.0
    released = []
    pilot.fly(6.0, lambda s: released.append(s.beta))
    sign = 1.0 if steady > 0.0 else -1.0
    return {'step': 100.0 * (max(sign * b for b in held) - abs(steady)) / abs(steady),
            'release': 100.0 * max(0.0, max(-sign * b for b in released)) / abs(steady)}


def load_factor(sim, weight_lb, kcas, alt_ft):
    h = alt_ft * FT_TO_M
    pilot = _level(sim, weight_lb, alt_ft, mach_from_cas(kcas, h), seconds=6.0)
    pilot.pitch_axis = 1.0
    peak = [0.0]

    def watch(s):
        peak[0] = max(peak[0], s.nz)

    pilot.fly(5.0, watch)
    return {'g': peak[0], 'alpha': sim.alpha}


def aoa_limit(sim, weight_lb, mach, alt_ft, gear_down):
    pilot = _level(sim, weight_lb, alt_ft, mach, seconds=20.0 if gear_down else 6.0, gear_down=gear_down)
    pilot.pitch_axis = 1.0
    peak = [0.0]

    def watch(s):
        peak[0] = max(peak[0], s.alpha)

    pilot.fly(6.0, watch)
    alpha, nz = _average(pilot, 2.0, 'alpha', 'nz')
    swing = []

    def collect(s):
        swing.append(s.nz)

    pilot.fly(1.0, collect)
    return {'aoa': alpha, 'peak': peak[0], 'nz': nz, 'nz_swing': max(swing) - min(swing)}


def reach_limit_mach(sim, weight_lb, alt_ft, mach):
    return excess_power(sim, weight_lb, alt_ft, mach)


def thrust_limited(sim, weight_lb, alt_ft, kcas):
    return excess_power(sim, weight_lb, alt_ft, mach_from_cas(kcas, alt_ft * FT_TO_M))
