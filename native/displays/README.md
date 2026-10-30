# F117Displays native compositor

This optional cockpit Lua extension owns three `CockpitBase::ccIndicatorBake`
instances. It uses the shared native baking machinery used by the F-16 LCD path,
with our own textures and Lua artwork. It does not depend on F16C.dll, modify DCS,
replace the EFM, or reproduce F-16-specific LCD post effects. The HUD stays a
collimated stroke indicator with its existing finite glass mask.

`Systems/DisplayCompositor.lua` loads `bin/F117Displays.dll` from the display
device's cockpit lifecycle. Native code locates source pages by the unique
`F117_VSD_SOURCE`, `F117_HSD_SOURCE` and `F117_IRADS_SOURCE` elements. It obtains
their actual zero-based indices and owning contexts, rather than assuming an
indicator order. Native `addSource(index,width,height)` sets target pixel sizes.
The three named channels are `F117_LCD_LEFT`, `F117_LCD_RIGHT` and
`F117_LCD_CENTRE`. The centre page includes camera target 0 plus its Lua overlay.

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

## Compatibility and first DCS test

Opaque native C++ allocation and context offsets are private APIs. The adapter
checks the loaded CockpitBase file's SHA-256 before using them:
`fb0a09be70627c7790dea1527cedfee43082bb8b112484d5c85be1d99d33de95`.
A different build retains direct drawing. Native exports are resolved by name.
The baker allocation is 0x1D0 bytes, confirmed by the native vector deleting
destructor stride; context indicators/children are at +0xB0/+0x130 in this build.

Fully restart DCS. Look for `F117_DISPLAYS` in dcs.log and the message
`native MFD compositor active (VSD/HSD/IRADS)`. Check all three screens, stick
occlusion, power, head movements, mission reload and VR. Capture a normal seated
screenshot to compare the baked source projection with the established layout.
If needed, set `enabled=false` in
`Cockpit/Scripts/MFD/Indicator/render_config.lua` and restart for direct drawing.
The module uses the exposed DCS target-resolution option, with a 1024 fallback;
`resolution=2048` in that config explicitly overrides it.

The release packager currently ships only the EFM DLL. Shipping this adapter in a
release will also require adding its native build/test and artifact to packaging.
The currently installed adapter is a local development build.
