"""Six-degree-of-freedom integrator and scripted pilot around the EFM.

Axes match DCS: body X forward, Y up, Z right; world X north, Y up, Z east. Positive rates are
roll right (X), yaw left (Y) and pitch up (Z). DCS does this integration in the sim, so results
here are close to DCS rather than identical to it, and there is no ground or gear contact model.
"""
import math

from efm import CMD_GEAR_DOWN, CMD_PITCH_AXIS, CMD_ROLL_AXIS, CMD_THROTTLE_AXIS, CMD_YAW_AXIS

G = 9.81
DT = 0.006
LB_TO_KG = 0.45359237
FT_TO_M = 0.3048
KT_TO_MPS = 0.514444
SEA_LEVEL_PRESSURE = 101325.0
SEA_LEVEL_SOUND = 340.294
RAD = math.pi / 180.0
FUEL_KG = 5000.0  # Enough for every test. The tests set the gross weight, so this doesn't change it.

# Stick shaping in the EFM's FlightControls.cpp. The pilot inverts it to ask for a load factor or roll rate.
PULL_FORCE_SCALE = 180.0
PUSH_FORCE_SCALE = 80.0
ROLL_FORCE_SCALE = 75.0
ROLL_FORCE_DEADBAND = 3.0
ROLL_PARABOLIC_GAIN = 150.0 / 72.0 ** 2  # A mid-range value: the EFM schedules this with speed, and the pilot's loop absorbs the rest.


def isa(h_m):
    """International Standard Atmosphere: temperature K, pressure Pa, density kg/m3, speed of sound m/s."""
    if h_m < 11000.0:
        t = 288.15 - 0.0065 * h_m
        p = SEA_LEVEL_PRESSURE * (t / 288.15) ** 5.25588
    else:
        t = 216.65
        p = 22632.1 * math.exp(-(h_m - 11000.0) / 6341.62)
    return t, p, p / (287.058 * t), math.sqrt(1.4 * 287.058 * t)


def mach_from_cas(cas_kt, h_m):
    _, p, _, _ = isa(h_m)
    ratio = cas_kt * KT_TO_MPS / SEA_LEVEL_SOUND
    qc = SEA_LEVEL_PRESSURE * ((1.0 + 0.2 * ratio * ratio) ** 3.5 - 1.0)
    return math.sqrt(5.0 * ((qc / p + 1.0) ** (2.0 / 7.0) - 1.0))


def cas_from_mach(mach, h_m):
    _, p, _, _ = isa(h_m)
    qc = p * ((1.0 + 0.2 * mach * mach) ** 3.5 - 1.0)
    return SEA_LEVEL_SOUND * math.sqrt(5.0 * ((qc / SEA_LEVEL_PRESSURE + 1.0) ** (2.0 / 7.0) - 1.0)) / KT_TO_MPS


def pitch_axis_for_nz_delta(delta):
    """Stick axis value that makes the EFM's pitch law add `delta` g to its command."""
    if delta >= 0.0:
        force = (delta + 0.128) / 0.016 if delta < 0.4 else (delta + 1.811) / 0.067
        return min(force / PULL_FORCE_SCALE, 1.0)
    pull = -delta
    force = (pull + 0.128) / 0.016 if pull < 0.4 else (pull + 2.128) / 0.0766
    return max(-force / PUSH_FORCE_SCALE, -1.0)


def roll_axis_for_rate(rate_dps):
    """Stick axis value that commands `rate_dps` from the EFM's roll law."""
    if abs(rate_dps) < 0.05:
        return 0.0
    force = ROLL_FORCE_DEADBAND + math.sqrt(abs(rate_dps) / ROLL_PARABOLIC_GAIN)
    return math.copysign(min(force / ROLL_FORCE_SCALE, 1.0), rate_dps)


class Sim:
    def __init__(self, efm, inertia):
        self.efm = efm
        self.ix, self.iy, self.iz = inertia

    def start(self, weight_lb, h_m, mach, alpha_deg=None, gear_down=False, throttle=1.0, burn_fuel=False,
              freeze_speed=False):
        efm = self.efm
        efm.restart()
        # As in DCS, the aircraft starts without its fuel and the EFM reports the fuel mass.
        self.mass = weight_lb * LB_TO_KG - FUEL_KG
        self.fuel_used = 0.0
        self.freeze_speed = freeze_speed
        efm.set_fuel(FUEL_KG)
        efm.unlimited_fuel(not burn_fuel)
        self.mass += efm.mass_change()
        self.h = h_m
        self.px = self.pz = 0.0
        _, _, rho, sound = isa(h_m)
        self.V = mach * sound
        if alpha_deg is None:
            # First guess from a lift slope of 0.05 per degree. The flight controls correct it within seconds.
            alpha_deg = self.mass * G / (0.5 * rho * self.V ** 2 * 84.77) / 0.05
        alpha = min(alpha_deg, 15.0) * RAD
        self.vx, self.vy, self.vz = self.V * math.cos(alpha), -self.V * math.sin(alpha), 0.0
        self.p = self.r = self.q = 0.0  # Body rates about X, Y and Z.
        half = alpha / 2.0
        self.qw, self.qx, self.qy, self.qz = math.cos(half), 0.0, 0.0, math.sin(half)
        self.ax = self.ay = self.az = 0.0
        self.fx = self.fy = self.fz = 0.0
        self.nz = 1.0
        self.thrust = 0.0
        self.ps = 0.0
        self.t = 0.0
        self.alpha = alpha / RAD
        self.beta = 0.0
        self.pitch = self.alpha
        self.roll = 0.0
        self.vs = 0.0
        self.set_throttle(throttle)
        if gear_down:
            efm.command(CMD_GEAR_DOWN, 1.0)

    def set_throttle(self, fraction):
        self.efm.command(CMD_THROTTLE_AXIS, 1.0 - 2.0 * fraction)

    @property
    def mach(self):
        return self.V / isa(self.h)[3]

    @property
    def cas(self):
        return cas_from_mach(self.mach, self.h)

    def step(self):
        efm = self.efm
        qw, qx, qy, qz = self.qw, self.qx, self.qy, self.qz
        # Body axes in world coordinates: the columns of the rotation matrix.
        xx = 1 - 2 * (qy * qy + qz * qz); xy = 2 * (qx * qy + qw * qz); xz = 2 * (qx * qz - qw * qy)
        yx = 2 * (qx * qy - qw * qz); yy = 1 - 2 * (qx * qx + qz * qz); yz = 2 * (qy * qz + qw * qx)
        zx = 2 * (qx * qz + qw * qy); zy = 2 * (qy * qz - qw * qx); zz = 1 - 2 * (qx * qx + qy * qy)
        vx, vy, vz = self.vx, self.vy, self.vz
        p, r, q = self.p, self.r, self.q
        V = math.sqrt(vx * vx + vy * vy + vz * vz)
        alpha = math.atan2(-vy, vx)
        beta = math.asin(max(-1.0, min(1.0, vz / V)))
        pitch = math.asin(max(-1.0, min(1.0, xy)))
        roll = math.atan2(-zy, yy)
        yaw = math.atan2(-xz, xx)
        wx = xx * vx + yx * vy + zx * vz
        wy = xy * vx + yy * vy + zy * vz
        wz = xz * vx + yz * vy + zz * vz

        t, pr, rho, sound = isa(self.h)
        efm.set_atmosphere(self.h, t, sound, rho, pr, 0.0, 0.0, 0.0)
        efm.set_mass_state(self.mass, 0.0, 0.0, 0.0, self.ix, self.iy, self.iz)
        efm.set_state(xx * self.ax + yx * self.ay + zx * self.az,
                      xy * self.ax + yy * self.ay + zy * self.az,
                      xz * self.ax + yz * self.ay + zz * self.az,
                      wx, wy, wz, self.px, self.h, self.pz,
                      0.0, 0.0, 0.0,
                      xx * p + yx * r + zx * q, xy * p + yy * r + zy * q, xz * p + yz * r + zz * q,
                      qx, qy, qz, qw)
        efm.set_state_body(self.ax, self.ay, self.az, vx, vy, vz, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                           p, r, q, yaw, pitch, roll, alpha, beta)
        efm.simulate(DT)
        fx, fy, fz = efm.forces()
        mx, my, mz = efm.moments()
        change = efm.mass_change()
        self.mass += change
        self.fuel_used -= change
        m = self.mass

        # Inertial acceleration in body axes without gravity felt, which is what DCS reports to the EFM.
        ax = fx / m - G * xy
        ay = fy / m - G * yy
        az = fz / m - G * zy
        vdot = (ax * vx + ay * vy + az * vz) / V
        self.ps = V * vdot / G + wy

        # Rigid body equations. There's no product of inertia because the mod sets Ixy to 0.
        dvx = ax - (r * vz - q * vy)
        dvy = ay - (q * vx - p * vz)
        dvz = az - (p * vy - r * vx)
        vx += dvx * DT
        vy += dvy * DT
        vz += dvz * DT
        if self.freeze_speed:
            scale = V / math.sqrt(vx * vx + vy * vy + vz * vz)
            vx *= scale
            vy *= scale
            vz *= scale
        dp = (mx - (self.iz - self.iy) * r * q) / self.ix
        dr = (my - (self.ix - self.iz) * q * p) / self.iy
        dq = (mz - (self.iy - self.ix) * p * r) / self.iz
        p += dp * DT
        r += dr * DT
        q += dq * DT
        half = 0.5 * DT
        nw = qw - half * (qx * p + qy * r + qz * q)
        nx = qx + half * (qw * p + qy * q - qz * r)
        ny = qy + half * (qw * r + qz * p - qx * q)
        nz = qz + half * (qw * q + qx * r - qy * p)
        norm = 1.0 / math.sqrt(nw * nw + nx * nx + ny * ny + nz * nz)
        self.qw, self.qx, self.qy, self.qz = nw * norm, nx * norm, ny * norm, nz * norm
        self.vx, self.vy, self.vz = vx, vy, vz
        self.p, self.r, self.q = p, r, q
        self.ax, self.ay, self.az = ax, ay, az
        self.fx, self.fy, self.fz = fx, fy, fz
        self.h += wy * DT
        self.px += wx * DT
        self.pz += wz * DT
        self.vs = wy
        self.V = V
        self.alpha = alpha / RAD
        self.beta = beta / RAD
        self.pitch = pitch / RAD
        self.roll = roll / RAD
        self.nz = fy / (m * G)
        self.thrust = efm.thrust()
        self.t += DT
        if not math.isfinite(self.h + V + p):
            raise FloatingPointError('state became non-finite')


class Pilot:
    """Flies the EFM through its stick axes, the way a player's joystick does."""

    def __init__(self, sim):
        self.sim = sim
        self.hold_alt = None
        self.bank = 0.0
        self.nz_cmd = None
        self.speed_schedule = None
        self.roll_axis = None
        self.yaw_axis = 0.0
        self.pitch_axis = None
        self.trim = 0.0
        self.nz_filtered = 1.0
        self.gamma_cmd = 0.0
        self.bank_integral = 0.0

    def _desired_nz(self):
        sim = self.sim
        attitude = math.cos(sim.roll * RAD) * math.cos(sim.pitch * RAD)
        if self.nz_cmd is not None:
            return self.nz_cmd, attitude
        if self.speed_schedule is not None:
            # Climb on a speed schedule: fly the flight path angle the excess power allows, corrected by speed error.
            error = (sim.V - self.speed_schedule(sim.h)) / max(sim.V, 1.0)
            target = math.asin(max(-0.9, min(0.9, sim.ps / max(sim.V, 1.0)))) + 2.0 * error
            self.gamma_cmd += (target - self.gamma_cmd) * min(1.0, 0.5 * 0.006)
            gamma = math.asin(max(-1.0, min(1.0, sim.vs / max(sim.V, 1.0))))
            accel = sim.V * 0.6 * (self.gamma_cmd + 0.8 * error - gamma)
            return (math.cos(gamma) + accel / G) / max(math.cos(sim.roll * RAD), 0.3), attitude
        vertical = max(-3.0, min(3.0, 0.25 * (self.hold_alt - sim.h) - 0.9 * sim.vs))
        return (1.0 + vertical / G) / max(attitude, 0.15), attitude

    def update(self):
        sim = self.sim
        efm = sim.efm
        if self.pitch_axis is not None:
            efm.command(CMD_PITCH_AXIS, self.pitch_axis)
        else:
            desired, attitude = self._desired_nz()
            desired = max(-1.5, min(6.5, desired))
            self.nz_filtered += (sim.nz - self.nz_filtered) * min(1.0, 8.0 * 0.006)
            self.trim = max(-3.0, min(3.0, self.trim + 0.5 * (desired - self.nz_filtered) * 0.006))
            efm.command(CMD_PITCH_AXIS, pitch_axis_for_nz_delta(desired - attitude + self.trim))
        if self.roll_axis is not None:
            efm.command(CMD_ROLL_AXIS, self.roll_axis)
        else:
            # The roll law droops at low commanded rates, so the bank hold needs its own integrator.
            error = self.bank - sim.roll
            self.bank_integral = max(-30.0, min(30.0, self.bank_integral + 0.6 * error * 0.006))
            rate = max(-40.0, min(40.0, 2.5 * error + self.bank_integral))
            efm.command(CMD_ROLL_AXIS, roll_axis_for_rate(rate))
        efm.command(CMD_YAW_AXIS, self.yaw_axis)

    def fly(self, seconds, watch=None):
        """Fly for `seconds`. `watch` gets the sim each step and can stop the run by returning True."""
        sim = self.sim
        for _ in range(int(seconds / 0.006)):
            self.update()
            sim.step()
            if watch is not None and watch(sim):
                return True
        return False
