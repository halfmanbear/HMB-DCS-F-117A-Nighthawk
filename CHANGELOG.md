# To do

Open work only. Remove an item when it is done. Entries marked **EFM** need a
matching EFM build.

## Check in DCS

- HUD: the OCIP conformal correction, and the IRADS cursor and 10 mrad lock box,
  have not been seen in DCS (`docs/displays/hud-ocip-design.md`).
- Moving map: the chart backend on the centre screen needs an in-DCS check. The
  last compositor run showed the chart but faint or missing labels; repeat it at
  `resolution=1024` (`docs/displays/compositor-diagnostics.md`).

- Designate Select, the HUD cursor, INS drift, MARK points and sensor updates are unit-tested only
  (`docs/systems/designate-select-ins.md`). Check in DCS: the HUD cursor movement and ground point, the map
  cursor and UPDT, the MARK and SNSR legends on the HSD and MAP (positions are unchecked on glass), the VSD
  ALIGN / INS UP advisory, and that the INS drift rate feels right (`INS.lua` constants).

## Navigation (the main gap)

All three displays show dashes for destination, range, TTG, course and DME until
these exist. Details, manual pages and sizes are in
`docs/systems/cockpit-and-manual-gaps.md` part 2.

1. Flight plan, waypoints and destination steering (DEST, CRS LINE, CRS SEL,
   MAN HDG), with track select and auto-sequencing.
2. CDU keypad functions that need data entry: altitude calibration, visual update and OAP entry with the
   offset select switch (SNSR always uses the current destination until then).
3. DEP buttons, submenus and keypad. The main menu is drawn; nothing is clickable.
   Autothrottle Mach, GS and AOA hold wait on this.
4. **EFM:** OCIP autopilot: CH1/DUAL/CH2, PITCH/ROLL no-reference lights, stick
   de-reference, paddle disconnect and coupled steering.
5. TACAN and ILS steering on the HUD, VSD and HSD.

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
- Lower priority: DMAP/PMAP moving map, EDIT and STATUS displays, degraded modes, VTR, FCS BIT and emergency procedures.
  See tier 3 of the gap list.

## Clickable cockpit (on hold)

Resume plan in `docs/systems/cockpit-and-manual-gaps.md` part 1. Start with one switch end
to end: `Switch_07` to nav lights. First confirm which object type the Blender EDM
exporter needs for `PNT_` click zones.
