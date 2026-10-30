# Temporary HUD and MFD calibration

The calibration indicators are **enabled** in `Cockpit/Scripts/Calibration/config.lua`.
Exit and reload the aircraft/mission after changing the Lua files. A cockpit view
reset alone does not reload indicator definitions.

The four independent test pages are controlled at the end of `device_init.lua`.
Only centre calibration remains enabled. HUD calibration is disabled for the
new OCIP layout, and side calibration is disabled
because the colour VSD and basic HSD are now the default side displays. The existing HUD, IRADS
video and IRADS overlay remain present. Side pages use connector triples measured
in the cockpit Blender scene.

## First capture

1. Reload into a daylight mission, with a distant horizon visible.
2. Centre your head, hold cockpit zoom constant, and capture all four displays.
3. Capture a closer view of the three MFDs if their labels are unreadable.
4. Move your head sideways without turning it, then capture the HUD again.
5. Return to the original head position. With wings level, capture another HUD
   view after changing aircraft pitch by roughly 5 degrees. The P readout is in
   radians: a change of 0.0873 rad is 5 degrees. R is bank, also in radians.

Do not resize the production symbology until the test patterns are understood.

## What the patterns mean

**MFDs:** cyan axes, 10 mm ticks, a 40 x 40 mm square, an UP/+Y label and a +X
label to detect reversed axes. The amber outline is the measured Blender mesh
silhouette in the corresponding connector frame. Centre is approximately
175.0 x 148.2 mm; sides are approximately 104.1 x 95.3 mm. An oblique cockpit
view foreshortens a square, so do not force equal screenshot pixel dimensions.
Judge fit against the screen surface in that same view. The bezel may obscure
the mesh edge; that is useful evidence for defining a smaller safe drawing area.

**HUD:** cyan aircraft-fixed reference axes with 1 degree ticks and a test field
of +/-10 degrees horizontally and +/-7.5 degrees vertically. Inner brackets mark
+/-5 degrees; outer brackets mark the field limits. The pattern origin has an
initial downward offset of 50 mrad (about 2.86 degrees), based on the cockpit
capture. Tick spacing and angular gains remain unchanged. This is a visual fit
of the test pattern, not a physical glass mask or angular validation. The origin
labelled REF 0 is a connector-based reference, **not a calibrated aircraft
boresight**. This page uses `SetScale(MILLYRADIANS)`: 5 degrees = 87.266 mrad.
It shares the existing HUD's mounting correction and collimator distance factor,
but does not inherit its FOV coordinates, parent offsets or stencil masks.

The amber ATT 0 line uses the existing pitch and roll parameters: pitch is
translated at -1000 mrad/rad in the rotated frame. It is a small-angle attitude
diagnostic, not a full spherical horizon implementation. Compare it with a
distant horizon at modest pitch and bank; nearby terrain and the visible sea
horizon's geometric dip can introduce differences. Cyan reference marks should
stay aligned with distant scenery during head translation. Static mounting
alignment still needs to be established before ATT 0 can be treated as a horizon.

Both the cyan test HUD and green operational HUD now use a finite, cockpit-fixed
glass stencil from the measured Blender panes. Symbols remain collimated; as the
head moves, the visible part of the angular image changes at the glass boundary.
DCS projects the stencil for the viewpoint, including each VR eye; no scripted
head-position compensation or recentering is applied. In-game confirmation of
the exported connector pose and the DCS tilt/depth mapping is still required.
The cyan pattern remains independent of electrical/avionics mode gating.
Depth testing is enabled on the physical MFD elements so the joystick and other
cockpit geometry can obscure them. Only the collimated HUD disables depth testing,
following the stock HUD convention. Labels use the stock
`font_dejavu_lgc_sans_22` Unicode font from the common DCS pages.
Diagnostic labels are enlarged 2x for readability. Line widths are 1 mm on MFDs
and 1.2 mrad on the HUD; dimensional references are the line **centres**, so the
40 mm square is measured centre-to-centre, not outside-edge to outside-edge.

## Adjusting the test configuration

Use `Cockpit/Scripts/Calibration/config.lua`; reload the aircraft after each change.
Change one quantity at a time and retain the same view for comparisons.

| Setting | Meaning |
| --- | --- |
| `enabled` at top level | Master registration switch for all four tests |
| `hud/centre/left/right.enabled` | Enable one test independently |
| MFD `offset={x,y}` | Test pattern translation in indicator metres |
| MFD `scale_x/scale_y` | Diagnostic multipliers, initially 1 |
| HUD `mount` | Connector mounting corrections, same fields as `device_init.lua` |
| HUD `origin={x,y}` | Angular origin offset in milliradians |
| HUD `half_width_deg/half_height_deg` | Angular half extents of the static test field |
| HUD `scale_x/scale_y` | Angular pattern multipliers, initially 1 |
| HUD `pitch_gain/roll_gain` | Attitude test gains, initially -1000 and +1 |

For a coplanar MFD outline, multiply a scale by the desired extent divided by
the current extent, comparing both in the same view. Correct position before
scale. A rotated, reversed or missing pattern calls for checking the mounting
connectors rather than increasing its scale arbitrarily.

An angular ruler by itself cannot establish the HUD's true angular scale from
one screenshot. Use a known angular aircraft movement and the distant scene
as well as the pitch-driven line. Keep the production HUD gains separate until
the test projection agrees. These configuration values affect only the test pages.

If a side display stays completely blank, inspect `Saved Games/DCS/Logs/dcs.log`
for indicator errors and verify that the cockpit **EDM export** includes the
connector names below. Their presence in Blender alone does not prove export:

- Left: `MFD-PLASHKA-CENTER1`, `MFD-PLASHKA-DOWN1`, `MFD-PLASHKA-RIGHT1`.
- Right: `RADAR-PLASHKA-CENTER`, `RADAR-PLASHKA-DOWN`, `RADAR-PLASHKA-RIGHT`.

## Head movement and VR clipping

The accepted centred working profile is shared with Layout Studio through
`HUD/Indicator/layout_profile.lua`. The calibration config reads its angular
origin and extents there. The physical mask passed the user's head-shake tests
on 2026-10-29. On the next reload the operational HUD logs its actual scale ratio
under `F117_HUD_LAYOUT`; Studio uses it to express the 20 x 15 degree guide in
legacy FOV source units. That engine scale capture is necessary before relying
on the editor's numerical FOV bounds. It is separate from boresight validation.

Physical clipping is configured in `Cockpit/Scripts/HUD/Indicator/combiner_config.lua`.
The mask uses measured shapes, centres and approximately 36 degree tilts of both
panes, relative to the ILS connector triple. It compensates the registration's
30 mm upward mounting correction separately from the cyan angular origin offset.
The default 2 mm inset keeps the stencil inside the model edges. The shapes are a
union of the two glass apertures; a symbol can appear where either pane admits it.

After reloading, test centred, high, low, left and right head positions, then VR
if available. Symbols should disappear at the glass edge while their angular
alignment stays unchanged. Do not shrink the angular pattern for each head pose.
If an edge is misaligned, set `show_mask=true` for a translucent physical-plane
diagnostic, capture the same views, then turn it back off. Position, depth and
tilt must agree with the actual glass; a single angular offset cannot fix those.

`offset_m` adjusts the physical mask independently of the symbols; `inset_m`
adjusts the conservative border. `mount` must track the operational HUD mounting
corrections in `device_init.lua`. The calibration page uses its own configured
mount correction when building the same mask. Set `enabled=false` in
`combiner_config.lua` to restore the green HUD's original mask and leave the cyan
test HUD unclipped for diagnosis. This switch is separate from the master test
overlay switch. The original page is preserved as `HUD_legacy_base_page.lua`.

Regenerate the pane data with `python tools/generate_hud_combiner.py` after taking
new Blender measurements. The script records the connector locations read from
the live scene on 2026-10-29; remeasure those if the cockpit mounting is changed.
The offline editor does not emulate finite-depth masks, tilted 3D planes, head
translation or stereo projection. Disable its clipping preview to inspect the
complete angular layout while tuning the physical aperture in DCS.

## Remove the tests

Set the top-level `enabled = false` in `config.lua` and reload the mission.
This removes all enabled test indicator registrations. IRADS camera, IRADS
overlay, HUD, left VSD and right HSD remain.

## Offline verification

Run `python tools/check_display_calibration.py`. It checks Lua syntax, on/off
registration counts, unit modes, mesh indices, parent links and the 5 degree
pitch response. Reference PNGs are written into `tmp/calibration/`.
Pass `--refresh-outlines` to regenerate the static Lua outlines from
`tools/data/cockpit_display_geometry.json` after taking new Blender measurements.
Offline previews do not reproduce DCS projection, font metrics or EDM mounting.

The checker loads init scripts and page entries in separate Lua environments,
as required by DCS. Font stringdefs include `GetScale()` explicitly; geometry
coordinates are handled by `SetScale`. Omitting that font conversion on the
milliradian HUD produces enormous glyphs that can wash out the cockpit view.

## Native renderer migration

Calibration indicators are now disabled by default in Calibration/config.lua. The native compositor registers three readiness-gated holders alongside the five original indicators (eight total, or nine with the centre diagnostic enabled). Direct drawing remains the fallback until native initialization succeeds. Disabling render_config.lua enabled returns to five/six registrations. HUD mounting and finite-glass masks are unchanged. See display-readability.md.
