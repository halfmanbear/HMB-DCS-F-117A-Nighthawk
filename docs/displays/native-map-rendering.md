# Native map-rendering investigation

Inspected the installed FA-18C cockpit Lua on 30 October 2026 and the common
chart backend on 31 October 2026. These are
implementation findings from that installation, not evidence that the F-117
used Hornet display software or that Hornet native classes are portable.

## What the Hornet scripts establish

Paths below are relative to
`E:/Eagle Dynamics/DCS World/Mods/aircraft/FA-18C/Cockpit/Scripts/`.

| File | Observed implementation |
|---|---|
| `devices.lua` | Identifies DIGITAL_MAP_COMPUTER as CP-1802/ASQ-196. |
| `device_init.lua:331` | Creates `F18::avDigitalMapComputer_ASQ196_F18`, with ELEC and MuxManager links; its Lua initialization filename is empty. |
| `device_init.lua:840` | Registers the AMPCD through `F18::ccAMPCD_F18`. The AMPCD device also links to DMC, mission computers and other Hornet systems. |
| `Multipurpose_Display_Group/Common/indicator/Pages/MPD/HSI/HSI_DIGITAL_MAP.lua:3` | Calls `AddVideoSignalRender_MPD_FullScreen` gated by native controller `MPD_HSI_DigitalMapShow`. |
| `Multipurpose_Display_Group/Common/indicator/Pages/MPD/SA/SA_DIGITAL_MAP.lua:3` | Uses the same helper, gated by `MPD_SA_MapShow`. |
| `Multipurpose_Display_Group/Common/indicator/Pages/MPD/MPD_page_defs.lua:298` | Creates a fullscreen ceTexPoly, selecting `render_target_` plus `GetRenderTarget()+1`. Sets input_space_SRGB=true and additive_alpha=true. |
| `Multipurpose_Display_Group/Common/indicator/Common_init.lua` | Composes the map background with separate outlined and main DMC symbology subsets. |
| `Multipurpose_Display_Group/Common/indicator/Pages/MPD/HSI/HSI_MAIN.lua:49` | Explicitly notes the digital-map camera depends on the decentered position and that MDG must receive a consistent value via mux. |

The inspected implementation is identified as ASQ-196, not TAMMAC. The Lua
shows how a generated image is displayed and overlaid; it does not expose a
terrain tile reader, terrain shading algorithm or standalone map-camera API.
`GetRenderTarget()` selects an existing target in its native indicator context;
calling or copying that expression does not create a map image.

## Implemented F-117 adaptation

`Cockpit/Scripts/MFD/Indicator/Map/Map_source.lua` supplies a small, independent
texture adapter. The map page draws in this order:

1. Existing opaque measured aperture backing.
2. Optional map-source texture in the navigation window (122 x 98 mm).
3. F-117 legends, planned route/threats, aircraft reference and IRADS cursor.
4. Existing display dimming layer, with native brightness registration retained.

The texture uses ceTexPoly, UVs covering 0..1, input_space_SRGB=true and the
existing depth/clip settings, with additive alpha as stock Hornet and F-16 video
uses. `Map/Charts/page.lua` writes the target's alpha only, as the stock kneeboard
map page does, because normal blending would otherwise draw the chart fully
transparent.

The generic DCS chart backend is now implemented experimentally and enabled in
`Map/Charts/config.lua`. It registers an isolated avKneeboard/ccKneeboard pair
at target 5, sampled through its texture `mfd5`. The third `indicators` parameter
is one-based (DCS stores it minus one), so `device_init.lua` passes 6 for target 5. `Map/render_source.lua` selects
that source. Set `Charts/config.lua` to `enabled=false` and reload the mission for
the previous background-only fallback. The image adapter rejects `mfd0` because it
belongs to IRADS, and any `render_target_N` because that `MFD` material receives
brightness and contrast only on the target's own indicator and otherwise draws
flat grey. Target 3 (parameter 4) is left for standard
kneeboards; other modules' target assignments are not treated as portable.
Configuration changes require a mission reload.

The source image appears only when configured, navigation is valid, and the
producer reports `F117_MAP_SOURCE_READY > 0.5`. Mission initialization resets
readiness to zero. Missing/unready/invalid sources retain the opaque background
and `MAP DATA NOT LOADED` message; normal route overlays remain available.
A Lua readiness flag is not GPU completion or proof of correct imagery.

## Producer contract

`Systems/MovingMap.lua` publishes the following numeric parameters during its
normal update. The producer must consume a coherent current snapshot and
keep its imagery aligned with that snapshot. It must clear readiness when
unavailable, stale or unable to honor a changed database/view. The native producer checks the previous requested camera view, but there is
no GPU frame acknowledgement or pixel-content/stale-texture detector yet.

| Parameter suffix after `F117_MAP_` | Meaning |
|---|---|
| `VIEW_VALID` | 1 only with valid aircraft world position and heading. |
| `VIEW_CENTER_X`, `VIEW_CENTER_Z` | DCS world metres at the centre of the texture; x north, z east. Includes manual pan and decentering. |
| `VIEW_UP_RAD` | Clockwise angle from world north to screen up; north-up is 0. |
| `VIEW_SCALE` | Display metres per world metre, shared with overlay projection. |
| `VIEW_WIDTH_M`, `VIEW_HEIGHT_M` | World coverage of the texture rectangle, in metres. |
| `DATABASE` | 1 DMAP, 2 PMAP. These are this mod's protocol values. |
| `BACKGROUND_DECLUTTER` | Selected mod background setting, 0..3. |
| `REFERENCE_ELEVATION` | Selected mod reference-elevation mode, 0 or 1. |
| `ELEVATION_FT` | Selected elevation in feet. |
| `SOURCE_READY` | Written by the producer; initialized to 0 by MovingMap. |
| `SOURCE_VISIBLE` | Written by MovingMap; final configured/valid/ready gate. Do not write from the producer. |

For map-up angle a, screen-right in world north/east coordinates is
`(-sin(a), cos(a))`; screen-up is `(cos(a), sin(a))`. Texture top corresponds
to screen-up. Full-height map scale remains the existing mod convention,
not a newly verified Harris range definition.

Publishing the actual view centre avoids the Hornet comment's failure case:
shifting only the aircraft/route overlay while leaving the geographic image
centred on a different world point. The same rule applies to manual panning.

## Verification and next boundary

Offline tests exercise opt-in/default behavior, rejection of the IRADS source,
readiness and invalid-navigation gating, initialization reset, texture bounds,
sRGB/alpha properties, layer ordering, and north-up/track-up/decentered/panned
view geometry. Existing map and cockpit regressions also pass.

The common chart investigation below replaces the earlier missing-producer
stage. No Hornet or F-15E classes are instantiated. Native pixels still require
in-DCS verification; host tests cannot establish raster coverage or refresh.


## Common DCS chart backend (31 October 2026)

The F-15E backup's `Scripts/DMS_init.lua` uses the common chart-page schema
(scale, chart, rotation, x, z). Its native avTSD_Map is aircraft-specific, but
`Scripts/Aircrafts/_Common/Cockpit/KNEEBOARD/declare_kneeboard_device.lua` in DCS
registers the generic avKneeboard/ccKneeboard pair. The common indicator creates
its map page with `GetSelf():Add_Map_Page`. The adapter relies on this layout:

- avKneeboard stores 48-byte map records with scale at +0, chart +8, rotation
  +16 and world x/z at +24/+32. Its avMovingMap secondary base consumes those
  values to construct the chart camera.
- ccKneeboard uses terrain chart screen condition 9 when use_lat_lon=false.
  Its screen parameters carry the selected chart level to the renderer.
- ccMovingMap registers Lua create_chart/set_render_to_texture helpers in its
  own page environment. These are not ordinary global Lua device methods.
- Chart camera horizontal half-span is the map record's scale. This is a
  native camera convention, separate from the mod's selectable range semantics.

These layouts are specific to the pinned CockpitBase build, SHA-256
`fb0a09be70627c7790dea1527cedffee43082bb8b112484d5c85be1d99d33de95`.
They are not an official SDK.

### Installed implementation

- New MAP_CHARTS device ID is appended, preserving existing device IDs. Its
  single native map page is initialized at aircraft start position. No custom
  kneeboard images, clipboard border, route, threat or text overlay is included
  in the producer image. F-117 overlays are drawn by the existing central page.
- The source indicator is appended after existing indicators. It requests
  render target 5 with purpose 100 only; the version-checked adapter removes
  direct/UI purposes from this source if a generic kneeboard toggle adds them.
  The normal kneeboard and the IRADS source are not selected by the adapter.
- `Systems/ChartLevels.lua` follows common kneeboard level selection:
  Caucasus uses 2 below 20 NM, 3 through 40 NM, then 6; other theatres use
  2 below 20, 4 through 40, 5 through 80, then 6. This adapts the F-15E's
  fixed 2/3/6 choices to the installed common DCS script's theatre distinction.
- `Systems/ChartBackend.lua` passes the shared view centre, clockwise map-up,
  world coverage and chart level to `luaopen_f117_charts` in F117Displays.dll.
- `native/displays/NativeCharts.h` accepts only the pinned CockpitBase hash and
  exported generic-class identities. It discovers the unique source marker
  through the cockpit context, checks its owning avKneeboard type, single map
  record and single page-index layout, and updates only that private record.
  It also sets the owned source aspect and enables its chart requests when the
  floating kneeboard UI is hidden. No vtable replacement or executable patching
  is used. Native objects remain DCS-owned; no native pointer is cached across
  calls as an object to dereference during cleanup.
- The adapter waits until the native camera reflects the previous requested
  position and orthographic bounds. Zoom/orientation changes or substantial
  pans clear readiness until the camera catches up. This is camera evidence,
  not proof of a rendered frame or correct texture pixels.
- Unsupported native versions, missing modules, missing source markers,
  invalid navigation and mismatched object layouts leave the fallback active.
  External explicitly configured texture producers keep ownership of their
  readiness flag; the generic producer does not overwrite that flag.

This backend displays **the installed theatre's DCS charts**. Syria, for
example, has `Mods/terrains/Syria/RasterCharts/rasterCharts.zip`; the native
renderer selects and reads chart data rather than this mod extracting tiles.
No terrain assets are copied or redistributed. No Google/OpenStreetMap network
service, Harris STARS files or satellite feed is used by this implementation.
Actual chart availability and appearance can vary with theatre and scale.

Both PMAP/DMAP selections currently share this chart underlay. BGD/reference
height settings remain UI state; no Harris elevation shading, cultural-layer
filtering or independent DMAP data interpretation is implemented. Map/IRADS brightness
controls retain their existing operation.

### Validation and live check

The native build runs compositor, brightness and chart host executables using
DCS's real Lua 5.1 DLL. Chart tests exercise map writes, matching-camera wait,
zoom changes, invalid numbers/levels and rejection of foreign or multi-record
kneeboard objects. Python tests cover generic registration, off-switch rollback,
theatre levels, readiness/errors and external source isolation, alongside the
existing map geometry and cockpit regressions. None starts the DCS renderer.

Item 1 was confirmed in DCS on 2026-10-31 (Caucasus, 25 NM, north-up): the chart
is upright and not mirrored. The remaining items are still to be checked.

On the next mission reload, verify:

1. A theatre chart appears behind the central F-117 symbols; left EO still
   updates normally. If unavailable, MAP DATA NOT LOADED remains visible.
2. Range, track-up/north-up, decentering and manual pan keep map features and
   overlaid locations together, including while flying and after switching views.
3. Night brightness and the rounded display aperture remain correct, with no
   separate floating chart window on kneeboard toggles.
4. `F117_CHARTS` messages in dcs.log show source discovery and camera alignment.
   A camera that remains pending logs its condition, world position and volume
   every 200 backend updates (about ten seconds at the current device rate).

If the chart is white, stale, misregistered or affects normal kneeboard use,
set `Cockpit/Scripts/MFD/Indicator/Map/Charts/config.lua` enabled=false and reload.
This is the rollback switch; the F-117 symbols and left EO remain independent.
The pre-chart adapter binary is retained locally at
`tmp/native-map/F117Displays.before-charts.dll` for development rollback.

## CMDI fill area (3 November 2026)

The MAP page is only shown on the CMDIs, but it is authored at centre-screen size and
drawn at about 0.58 by `CMDI_formats.lua`. Its chart image used to be a fixed
0.122 x 0.098 window, so on a CMDI it covered roughly two thirds of the glass, and its
text was about 40% of the VSD/HSD text height.

`Map/Map_window.lua` now measures the fill area from the measured side glass divided by
that scale. The aperture (stencil), the chart image, the route clip, the "inside the
window" test and the chart camera extents (`F117_MAP_VIEW_WIDTH_M/HEIGHT_M`) all use it,
so the chart fills the whole glass behind the symbology. The ground scale is unchanged:
`F117_MAP_VIEW_SCALE` still derives from `.106 / (range * 1852)`, so symbols, routes and
the range readout keep their positions; the chart simply shows more terrain around them.
Static labels are stretched to the window edges and the map text has a 1.4x gain
(`MAP_TEXT_GAIN`). Verify the picture and its registration in DCS; the offline editor has
no chart pixels.

The chart adapter sets the camera's source aspect from the requested view (height / width)
each update. A fixed aspect from the old window never matched the full-glass view, so the
camera was never reported ready and the map stayed on "MAP DATA NOT LOADED". `dcs.log`
showed this as a repeating `chart condition=9 ... volume=` line whose vertical span did not
equal the requested height. The previous adapter is kept at
`tmp/native-displays-backup/F117Displays.before-aspect.dll`.
