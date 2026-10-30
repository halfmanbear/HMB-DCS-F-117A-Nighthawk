# Native HUD and MFD presentation

The operational HUD and all three MFD overlays use the shared DCS stroke renderer: `ceSLineFont` text and `ceSMultiLine` lines. Filled backgrounds and stencil masks remain meshes. The mod-owned SVG glyphs are registered via `materials.lua` and `symbologyPaths`; no F-16 artwork or DLL dependency is required.

`Cockpit/Scripts/display_readability.lua` controls stroke thickness/fuzziness and text sizes. Defaults match the F-16 example's indicator shader settings: thickness 0.8, fuzziness 0.5, specular pass disabled on the HUD and enabled on MFD sources. Unlike the previous ribbon quads, stroke width is a shader setting rather than a physical polygon width. HUD readouts are approximately 7 mrad high. Side-MFD small/value text is 2.8/4.6 mm high, with explicit inter-character spacing. Colours retain the requested VSD sky #0310B2 and earth #A38C50.

## Display pipeline

`bin/F117Displays.dll` now owns three native `ccIndicatorBake` channels. It is loaded by the cockpit display device, independently of the flight model. Sources are found by unique page markers and their actual context indices. Each source is baked to its own named texture; depth-tested holders present these textures on the calibrated apertures. The centre source includes the existing IRADS camera target 0 plus its overlay.

Sources initially draw directly and all holders are hidden. After all three native bakes initialize, source purposes switch to BAKE and F117_LCD_READY enables the holders. Missing module, unsupported CockpitBase build or initialization failure retains direct drawing. There are eight registered indicators (five sources/camera/HUD and three initially hidden holders). Set `enabled=false` in MFD/Indicator/render_config.lua to use the five-indicator direct path.

The earlier Lua-only render_target + BAKE attempt produced black screens and has been replaced. This adapter initializes actual native baking objects and named channels. See [native compositor implementation and tests](../native/displays/README.md) for source selection, ownership, compatibility and runtime limits.

The HUD remains a COLLIMATOR indicator, drawing vector text/lines directly through the unchanged finite glass stencil. It is not baked to an MFD texture. HUD mounting, origin, angular gains, glass geometry and head-movement clipping were preserved byte-for-byte. Main-power, brightness and validity controllers remain active. Temporary calibration indicators are disabled by default.

The compositor uses DCS's exposed target-resolution option with a 1024 fallback; render_config.lua can explicitly override it. Texture pixels remain separate from physical/angular layout units. No F16C.dll dependency or proprietary F-16 LCD effects are introduced. The adapter is built and installed locally; DCS rendering and teardown validation are pending.

## Designer and validation

Layout Studio still edits the original page files and positions. It now draws the mod's stroke glyph paths and line-segment indices, and shows an empty backdrop for live IRADS video. It does not emulate DCS shader softness, target compositing or VR projection. Generate the SVG and font mapping reproducibly with `python tools/generate_stroke_font.py`. The older bitmap generator writes a separate unused fallback definition and cannot replace the active stroke font.

Run `python -m unittest discover -s tests -p test_native_displays.py`, the existing layout/OCIP tests and `python tools/check_display_calibration.py`. These check glyph references, visible draw purposes, registration, camera/overlay separation, visibility, transforms and preserved optics. They cannot establish the render pass selected by DCS at runtime.

Fully restart DCS for resource and indicator-registration changes. Check the HUD and each MFD at the normal head position, then head movement and joystick occlusion. Check the latest dcs.log for missing F117_stroke_font, material or target errors. The existing autoexec.cfg already enables HUD_MFD_after_DLSS; it was left unchanged. Whether this engine option routes these indicators/holders after DLSS still requires an in-game comparison.
