# Native HUD and MFD presentation

The operational HUD and all three MFD overlays use the shared DCS stroke renderer: `ceSLineFont` text and `ceSMultiLine` lines. Filled backgrounds and stencil masks remain meshes. The mod-owned SVG glyphs are registered via `materials.lua` and `symbologyPaths`; no F-16 artwork or DLL dependency is required.

`Cockpit/Scripts/display_readability.lua` controls stroke thickness/fuzziness and text sizes. Defaults match the F-16 example's indicator shader settings: thickness 0.8, fuzziness 0.5, specular pass disabled on the HUD and enabled on MFD sources. Unlike the previous ribbon quads, stroke width is a shader setting rather than a physical polygon width. HUD readouts are approximately 7 mrad high. Side-MFD small/value text is 2.8/4.6 mm high, with explicit inter-character spacing. Colours retain the requested VSD sky #0310B2 and earth #A38C50.

## Display pipeline

All MFD pages currently draw directly to their cockpit screens. The native compositor is switched off with `enabled=false` in `Cockpit/Scripts/MFD/Indicator/render_config.lua`, so `dcs.log` shows this line on every mission start, which is expected:

```
F117_DISPLAYS (Main): native compositor disabled; direct drawing retained
```

It is off because turning it on produced a white centre image in DCS, even though the native setup reported success. That report comes from the comment in `render_config.lua`: no screenshot or log was kept, and the cause has not been investigated.

`bin/F117Displays.dll` still loads, because native brightness, charts and text parameters use it. Six indicators are registered: three MFD pages, the camera, the HUD and the chart source.

### Optional native compositor

Before re-enabling native baking, the opt-in [centre holder diagnostic](compositor-diagnostics.md)
can test a static colour card through the real holder with the compositor off.
Its `holder_test` switch defaults to false and adds one indicator when enabled.

When enabled, `bin/F117Displays.dll` owns three native `ccIndicatorBake` channels. It is loaded by the cockpit display device, independently of the flight model. Sources are found by unique page markers and their actual context indices. Each source is baked to its own named texture, and depth-tested holders present these textures on the calibrated apertures.

Enabling the config registers three additional holder indicators at cockpit creation. Sources initially draw directly and all holders are hidden. After all three native bakes initialize, source purposes switch to BAKE and `F117_LCD_READY` makes the holders visible. A missing module, an unsupported CockpitBase build or an initialization failure retains direct drawing.

To try it again:

1. Set `enabled=true` in `render_config.lua`, and update the check in `tests/test_native_displays.py` that expects it to be off.
2. Fully restart DCS, and look for `native MFD compositor active (VSD/HSD/IRADS)` in `dcs.log`.
3. Check all three screens by eye, because that message only means setup succeeded, not that the screens drew correctly.

The centre display has since changed from IRADS to the map, and the map page now carries the `F117_IRADS_SOURCE` marker. The compositor would therefore bake the map, which has not been tested.

The earlier Lua-only render_target + BAKE attempt produced black screens and has been replaced. This adapter initializes actual native baking objects and named channels. See [native compositor implementation and tests](../native/displays/README.md) for source selection, ownership, compatibility and runtime limits.

The compositor uses DCS's exposed target-resolution option with a 1024 fallback; render_config.lua can explicitly override it. Texture pixels remain separate from physical/angular layout units. No dependency on another aircraft's DLL or proprietary F-16 LCD effects are introduced. Its teardown, depth and VR behaviour in DCS have not been validated.

### HUD

The HUD remains a COLLIMATOR indicator, drawing vector text/lines directly through the unchanged finite glass stencil. It is not baked to an MFD texture, and the compositor setting doesn't affect it. HUD mounting, origin, angular gains, glass geometry and head-movement clipping were preserved byte-for-byte. Main-power, brightness and validity controllers remain active. Temporary calibration indicators are disabled by default.

## Designer and validation

Layout Studio still edits the original page files and positions. It now draws the mod's stroke glyph paths and line-segment indices, and shows an empty backdrop for live IRADS video. It does not emulate DCS shader softness, target compositing or VR projection. Generate the SVG and font mapping reproducibly with `python tools/generate_stroke_font.py`. The older bitmap generator writes a separate unused fallback definition and cannot replace the active stroke font.

Run `python -m unittest discover -s tests -p test_native_displays.py`, the existing layout/OCIP tests and `python tools/check_display_calibration.py`. These check glyph references, visible draw purposes, registration, camera/overlay separation, visibility, transforms and preserved optics. They cannot establish the render pass selected by DCS at runtime.

Fully restart DCS for resource and indicator-registration changes. Check the HUD and each MFD at the normal head position, then head movement and joystick occlusion. Check the latest dcs.log for missing F117_stroke_font, material or target errors. The existing autoexec.cfg already enables HUD_MFD_after_DLSS; it was left unchanged. Whether this engine option routes these indicators after DLSS still requires an in-game comparison.
