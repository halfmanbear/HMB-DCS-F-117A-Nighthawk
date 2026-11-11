# Native display rendering

Design notes for the F-117 display pipeline. The pages use DCS's shared cockpit
renderer with this mod's own artwork and Lua layouts. No F-16 artwork is copied.

## Design points

- **Indicator type:** MFD registrations use COMMON explicitly. A missing type already behaved as COMMON, so this is cleanup rather than a rendering fix.
- **Layouts:** cockpit drawing stays in Lua pages and resources. Moving layouts into the EFM is neither needed nor wanted.
- **Fonts:** core HUD/MFD text uses stroke fonts (`ceSLineFont`). Increasing bitmap raster dimensions alone does not reproduce stroke rendering.
- **Lines:** stroke lines use `ceSMultiLine` with thickness and fuzziness. `ceMeshPoly` widths are geometry widths and gain no stroke shader controls.
- **Render targets:** a Lua page can configure a target, but assigning a target ID alone does not produce LCD-style baking.
- **Resolution:** target pixel size, glyph raster size, physical/angular layout units and final output resolution are separate. 1024 is not a universal coordinate system.
- **Post-effects:** an after-posteffects pass exists, but that does not show DLSS routes through it. Do not force every page into it.
- **DLSS option:** `HUD_MFD_after_DLSS` belongs in `autoexec.cfg`; nothing supports a per-page copy. Runtime eligibility remains unresolved.

## Implementation history

**Bitmap font (retired).** The broken `ceUITTF` experiment was replaced with a `ceTexPolyFont`-compatible DDS atlas.

**Stroke port (2026-10-30).** Operational bitmap fonts were replaced with mod-owned `ceSLineFont` SVG glyphs, and procedural ribbon quads with `ceSMultiLine` primitives. HUD optics were unchanged. See display-readability.md for configuration, routing and validation limits.

**Lua-only baking (failed, 2026-10-30).** A `render_target` + BAKE source/holder attempt produced black MFDs in DCS, because baking needs preconfigured sources that Lua could not provide. The holders were unregistered and direct drawing restored. The IRADS camera kept target 0 and its direct overlay.

**Native adapter (2026-10-30).** `F117Displays.dll` constructs and owns three `ccIndicatorBake` objects, calls `addSource` and `init`, and only then switches source draw purposes and enables holders. `addSource`'s second and third integers are pixel width and height, and source indices are zero-based. The DLL is pinned to a tested CockpitBase SHA-256, resolves exports by name and uses Lua userdata for cleanup. Host tests pass with DCS Lua 5.1 and instrumented API calls, including actual DLL loading. They do not establish DCS render output, MT teardown safety or DLSS routing. See native/displays/README.md.


