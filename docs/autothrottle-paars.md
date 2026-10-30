# Autothrottle and PAARS

Source: TO 1F-117A-1A (OCIP supplement), PDF pages 15-20 and 52 (printed 4-2 to 4-7, 4-39),
Figure 4-3 (PAARS Response Map) and Figure 4-13 (VSD). Implemented in the EFM; the manual
describes behaviour, not control-law values, so the numbers below are simulator choices.

## Controls

| Control (manual) | Default key | Command | Behaviour |
|---|---|---|---|
| A/T engage switch | `J` | 10125 | Weight off wheels: CAS HOLD at current CAS. Press again to disengage. |
| A/T disengage button (inboard throttle) | `LCtrl+J` | 10126 | First press disengages and lights A/T DISC; second press extinguishes it. |
| Disengage paddle (stick) | `LAlt+9` | 408 | Disengages autopilot, autothrottle and PAARS; second press extinguishes A/T DISC. |
| ARS switch (stick) | `LAlt+3` | 10127 | PAARS on; press again to deselect. |

`LAlt+3` and `LAlt+9` match DCS's stock "Transition To Level Flight" and "Autopilot Disengage"
keys. All four are also in the joystick profile, unbound.

## Autothrottle

`EFM Source Code/Avionics/Autothrottle.h`

- **CAS HOLD only.** Mach, GS and AOA hold and CAS select are entered on the DEP, which does not
  exist yet. Target is clamped to the DEP keypad limits, 140-525 KCAS (Figure FO-3).
- CAS is computed from true airspeed and DCS static pressure/temperature (subsonic pitot relation).
- Disengages (lighting A/T DISC) on: engage switch, throttle button, paddle, touchdown, engines
  stopped, or pilot throttle input.
- **Hardware throttle:** a physical axis cannot be driven by the servo, so moving it more than 5%
  overpowers and disengages the A/T. After any other disengagement the lever stays where the
  servo left it until the axis moves 2% or more, then the axis takes over (no jump to idle).
  Keyboard throttle steps continue from the servo position.
- Lever servo rate 15%/s. Speed loop: P + filtered-acceleration damping, integral only within 5 kt.
- VSD shows the FMS command line `C 300 CAS` while engaged (manual 4-39, Figure 4-13 item 26).
- Not modelled: CH1/DUAL/CH2 channel selector and A/P SNGL CH light (no channel failures exist).

Cockpit parameters: `F117_AT_ENGAGED`, `F117_AT_DISC`, `F117_AT_CAS_COMMAND`.

## PAARS

`EFM Source Code/Avionics/Paars.h`; flight-control hook `set_recovery_nz_command` in
`FlightControls.cpp`.

- **Response map:** sector boundaries digitised from Figure 4-3. Each sector sets a load-factor
  command and a roll mode (roll upright, roll inverted, or zero roll rate):

| Sector | Region | Command |
|---|---|---|
| 7 | pitch ≥ 83° | pull 4 g, zero roll rate |
| 6 | pitch ≤ -70° | pull 4 g, zero roll rate |
| 1 | nose high, steep bank/inverted | pull 3 g, roll inverted |
| 2 | nose high, near upright | push (attitude law, ≥ 0 g), roll upright |
| 3 | near level, banked > 21° or inverted | hold flight path, roll upright |
| 4 | nose low (or level), bank < 90° | pull (attitude law, ≤ 4 g), roll upright |
| 5 | nose low, bank > 90° | push -1 g, roll upright |

- **End state:** wings level at +5° pitch (+9° gear down; the manual says gear retraction lowers
  pitch about 4°). PAARS stays engaged until deselected; the manual describes no automatic exit.
- **Pilot overpower:** PAARS feeds the existing FCS a g command and a roll-rate command; the
  pilot's stick adds on top, so the stick must be released for PAARS to fly the profile.
  The FCS AoA limiter still applies.
- **Throttle:** if the A/T is off, PAARS engages it in CAS HOLD at the current CAS (the manual's
  caution says PAARS moves the power levers). Deselecting ARS releases that A/T; an A/T the pilot
  engaged stays engaged. The paddle disengages everything.
- **Autopilot:** existing hold modes stay selected but do not act while PAARS flies.
- **Not functional** (refuses to engage, or disengages): A/R door open with |bank| < 45° and pitch
  -20° to +25°; weight on wheels with |bank| < 20° and pitch -10° to +15°.
- **VSD:** red `ARS <altitude>` (minimum pullout altitude, MSL, rounded down to the thousand);
  ICE, CONS, the data readout and the FMS command line blank (manual 4-21).
- **Minimum pullout altitude** is an estimate (the NIAC formula is not given): descent during the
  roll upright plus 1 s, then a 2.8 g pull to level. Tuned so that it is never optimistic in the
  regression simulation.
- Not modelled: both CMDIs reverting to the VSD (the right display has no format switching) and
  the DEP ARS readout (no DEP).

Cockpit parameters: `F117_ARS_ACTIVE`, `F117_ARS_MIN_ALT`.

## Tests

In the EFM repository:

```text
python tests/autothrottle_regression.py <out-dir>
python tests/paars_regression.py <out-dir>
```

- Autothrottle: compiled with the real engine model in a point-mass simulation at sea level and
  25,000 ft. Hold, 3° climb disturbance, speed changes (overshoot ≤ 1.8 kt), servo rate,
  saturation without wind-up, engage/disengage, A/T DISC and axis-override rules.
- PAARS: sector map against labelled points of Figure 4-3, inhibits, per-sector commands, and
  189 closed-loop recoveries (7 pitches × 9 banks × 3 speed/altitude starts) with the real A/T and
  engine model and an idealised FCS. All recover to wings level within 26 s. 22 high-altitude
  slow cases settle wings level below the target pitch because MIL thrust cannot hold the climb,
  as the manual warns for speeds below 200 KCAS.

## Needs checking in DCS

- A/T hold quality on the real aerodynamic model and engine (gains were tuned on a point-mass model).
- PAARS on the real FCS: sign of the roll-rate command, recoveries from inverted and vertical
  attitudes, behaviour at the AoA limiter.
- VSD readouts while engaged.
