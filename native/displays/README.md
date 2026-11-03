> Current OCIP III routing: left VSD, centre green IRADS, right MAP. Left also
> selects grayscale EO, MAP and HSD; right selects HSD/VSD. The side source markers
> name physical CMDIs, regardless of selected format. Centre native baking now
> includes sensor video as well as symbols; target 0 remains its sole camera.
> Colour, native bake output, clipping and VR require an in-DCS check.

# F117Displays native compositor

This optional cockpit Lua extension owns three `CockpitBase::ccIndicatorBake`
instances. It uses the shared native baking machinery used by the F-16 LCD path,
with our own textures and Lua artwork. It does not depend on another aircraft's DLL, modify DCS,
replace the EFM, or reproduce F-16-specific LCD post effects. The HUD stays a
collimated stroke indicator with its existing finite glass mask.

`Systems/DisplayCompositor.lua` loads `bin/F117Displays.dll` from the display
device's cockpit lifecycle. Native code locates source pages by the unique
`F117_VSD_SOURCE`, `F117_HSD_SOURCE` and `F117_IRADS_SOURCE` elements. It obtains
their actual zero-based indices and owning contexts, rather than assuming an
indicator order. Native `addSource(index,width,height)` sets target pixel sizes.
The three named channels are `F117_LCD_LEFT`, `F117_LCD_RIGHT` and
`F117_LCD_CENTRE`. The centre page includes camera target 0 plus its Lua overlay.

A bake fills its square texture from the source indicator's extents, which default
to the connector spans, and the holder shows that texture on its own quad. If they
differ, the image stretches: a side display at its 107.4 x 90.5 mm connector frame
drew a circle over 10% too tall and cropped its top and bottom rows.
`source_mount` in `device_init.lua` sets each source's `sw`/`sh` so its extents
match the `half_width`/`half_height` in `render_config.lua`.

All source indicators initially retain normal drawing. Holders and the centre
page's composited video are gated by `F117_LCD_READY=0`. Only after all three
bakers initialize does the module change source purposes to BAKE and set READY
to one. Failure before that commit destroys any partial bakes and keeps direct
drawing. Lua userdata owns each mission's resources; its GC calls the native
destructors to unregister callbacks and release textures. No rendering work runs
in DllMain or ed_fm_simulate, and no native vtables are patched.

This is an initial implementation. Host tests verify ownership, source discovery,
transactional activation and failure behavior; they do not run the DCS renderer.
In-game texture production, colour/alpha, aspect, depth, mission teardown and VR
still need runtime validation. Readiness means native init succeeded, not that a
rendered frame has been visually verified. DLSS routing is not established by
these tests.

## Build and tests

Run `powershell -NoProfile -ExecutionPolicy Bypass -File native/displays/build.ps1`.
Requires the installed Visual Studio x64 C++ tools and the current DCS Lua DLL at
the path in the script. The build runs with `/W4 /WX`, stages outputs in
`tmp/native-displays`, runs a host against DCS Lua 5.1, then installs the adapter
into this mod's bin directory. The flight model DLL is not changed.

The host uses an instrumented native API to check success, reordered sources,
resolution, idempotence, partial failure rollback, late source retry and exact
destructor counts. It also loads the actual DLL export and tests graceful
fallback with CockpitBase absent. Python display tests cover the Lua bootstrap,
holder readiness gates, glyphs and unchanged HUD optics.

## Compatibility and testing in DCS

Use the [static centre holder test](../../docs/compositor-diagnostics.md) first
to isolate texture sampling and presentation from native baking. It needs no
DLL rebuild and is disabled by default.

Opaque native C++ allocation and context offsets are private APIs. The adapter
checks the loaded CockpitBase file's SHA-256 before using them:
`fb0a09be70627c7790dea1527cedfee43082bb8b112484d5c85be1d99d33de95`.
A different build retains direct drawing. Native exports are resolved by name.
The baker allocation size and context offsets are specific to this build.

To test the compositor, set `enabled=true` in
`Cockpit/Scripts/MFD/Indicator/render_config.lua` and fully restart DCS. While it
is off, dcs.log shows `native compositor disabled; direct drawing retained`. When
it is on, look for `F117_DISPLAYS` and the message
`native MFD compositor active (VSD/HSD/IRADS)`. Check all three screens, stick
occlusion, power, head movements, mission reload and VR. Capture a normal seated
screenshot to compare the baked source projection with the established layout.
Set `enabled=false` again and restart to return to direct drawing.
The module uses the exposed DCS target-resolution option, with a 1024 fallback;
`resolution=2048` in that config explicitly overrides it.

Release packages include the committed `bin/F117Displays.dll`, but the package
workflow does not build it. Commit a rebuilt copy when the native code changes.


## Native brightness (independent of compositor)

The same DLL also exports `luaopen_f117_brightness`. Shipping display pages
register their actual materials with this module; `Systems/NativeBrightness.lua`
updates native renderer gain for the HUD and all MFDs even while compositor
`enabled=false`. The module checks the same CockpitBase hash, discovers current
indicators by page markers, and uses the parser embedded at +1144. Registration
uses native `read_from_state`; its material count is checked before activation.
Ordinary materials use `change_brightness`; the camera target additionally uses
`set_mfd_shader_brightness` with a neutral value of 0.5 and gain conversion.

Material names are held by the module, because DCS closes a page's Lua state
straight after loading it; a later page load replaces them. That closure also
releases the page's `package.loadlib` handle, and pages load before the display
device, so the module pins the DLL until DCS exits. Fully restart DCS to replace
it. Current indicator
pointers are rediscovered each update, not retained for subsequent native calls.
Missing sources/materials reset discovered renderers to neutral before Lua
re-enables the old dimmers, and the logged status names the blocking page. The
compositor remains disabled; this export does not change its readiness, purposes
or resources.

The build now also runs `test_brightness.cpp` against DCS Lua, covering material
capture/deduplication, source order, all five gains, video conversion, idempotent
configuration, missing source fallback, failed material resolution, retry, page
state closure
and the actual DLL export. See `docs/irads-image-controls.md` for controls
and runtime verification limits.


## Text parameters

`NativeParameters.h` adds `luaopen_f117_params`, used through
`Systems/TextParameter.lua`. Lua `handle:set()` stores any string that reads as a
number (`25`, `007`, `1E5`) as a number, and a `%s` element then crashes DCS in
`sprintf`. `ed_cockpit_update_parameter_with_string` always stores text. Use it
for any `%s` value that could look numeric, and never mix `handle:set()` writes on
the same parameter. If the export is unavailable, numeric-looking text gains a
`W` prefix so it still stays text. `test_parameters.cpp` runs against real DCS Lua
with an instrumented parameter store.

## Generic chart producer

`NativeCharts.h` adds `luaopen_f117_charts` to the existing adapter. It updates
only the uniquely marked, version-checked generic chart device registered by
this mod. It is not a Hornet/F-15E device transplant. The build now also runs
`test_charts.cpp` against real DCS Lua; those checks do not render map pixels.
See [native map investigation](../../docs/native-map-rendering.md) for layouts,
live-check requirements and rollback.
