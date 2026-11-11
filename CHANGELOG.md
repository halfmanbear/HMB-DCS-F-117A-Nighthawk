# To do

Open work only. Remove an item when it is done. Entries marked **EFM** need a
matching EFM build.

## Check in DCS

- HUD: the OCIP conformal correction, and the IRADS cursor and 10 mrad lock box,
  have not been seen in DCS (`docs/displays/hud-ocip-design.md`).
- Moving map: the chart backend on the centre screen needs an in-DCS check. The
  last compositor run showed the chart but faint or missing labels; repeat it at
  `resolution=1024` (`docs/displays/compositor-diagnostics.md`).

## Navigation (the main gap)

All three displays show dashes for destination, range, TTG, course and DME until
these exist. Details, manual pages and sizes are in
`docs/systems/cockpit-and-manual-gaps.md` part 2.

1. Flight plan, waypoints and destination steering (DEST, CRS LINE, CRS SEL,
   MAN HDG), with track select and auto-sequencing.
2. DEP buttons, submenus and keypad. The main menu is drawn; nothing is clickable.
   Autothrottle Mach, GS and AOA hold wait on this.
3. **EFM:** OCIP autopilot: CH1/DUAL/CH2, PITCH/ROLL no-reference lights, stick
   de-reference, paddle disconnect and coupled steering.
4. TACAN and ILS steering on the HUD, VSD and HSD.

## Cockpit and displays

- HUD declutter switch (NORM, DCLTR1, DCLTR2).
- CMDI format switching (HSD, MAP, STAT, SMD, DFRM).
- FAAD pitch ladder and FAAD backup mode on the sensor display.
- VSD extras: MEA and velocity-vector switches, pitch-ladder selector, FMS status
  letters, altitude and airspeed carets, ARS readout.
- Pre-planned modes HNAV, VNAV, SNAV, TOT and TOP.
- Out-of-corridor warning and MEA breakaway cue (after navigation).
- Master caution, annunciator panel and equipment failure alerts.
- Nosewheel steering paddle switch (free swivel).
- Lower priority: DMAP/PMAP moving map, EDIT and STATUS displays, position
  updates and MARK points, degraded modes, VTR, FCS BIT and emergency procedures.
  See tier 3 of the gap list.

## Clickable cockpit (on hold)

Resume plan in `docs/systems/cockpit-and-manual-gaps.md` part 1. Start with one switch end
to end: `Switch_07` to nav lights. First confirm which object type the Blender EDM
exporter needs for `PNT_` click zones.
