# Centre holder diagnostic

The direct-drawing baseline log, reference screenshot and config are saved
locally in `tmp/compositor-baseline-20261101/`. The screenshot is supplied as an
appearance reference; its filename date differs from the log date. It is not a
capture of a compositor run.

## Test 1: static texture through the real centre holder

In `Cockpit/Scripts/MFD/Indicator/render_config.lua`, leave `enabled=false` and
set `holder_test=true`. Fully exit and restart DCS, then load the same mission
with main power on. This adds only the centre holder and supplies a static TGA
instead of the native named texture. It uses the existing holder geometry,
depth, stencil, UVs, material colour and power gate. The original sources still
draw behind it; the left EO, right HSD and HUD should retain baseline behaviour.
The test does not call the native compositor. Other native display services
remain active.

Expected log message:

```
F117_DISPLAYS (Main): centre holder static-texture test active; native compositor disabled; direct sources retained
```

Expected centre image: red upper left, green upper right, blue lower left,
yellow lower right, a white outer border, black centre cross and a small white
square inside the red corner. The aperture may clip the border. Save a normal
seated screenshot and the new `dcs.log` before another run overwrites it.

| Result | What it establishes / next check |
| --- | --- |
| Correct coloured card | Static texture sampling and the holder presentation path work in this run. Next isolate native texture production and named-channel binding. |
| White card | Failure reproduces without a baker. Check the TGA lookup and material binding first; retain missing-texture log messages. |
| Map remains visible, card absent | Check the diagnostic log, main power, holder registration, depth and stencil. Absence alone does not identify which failed. |
| Card flickers or is partly hidden | Investigate source/holder depth and stencil interaction before testing baking. |
| Colours flipped or rotated | Resolve texture origin/UV orientation before comparing baked output. |

Set `holder_test=false` and restart DCS to restore the baseline. Diagnostic
switches should be false for normal use. If `enabled=true`, native compositing takes precedence and
the static test is ignored; do not enable both for this experiment.

The TGA is reproducible with `python tools/cockpit/generate_holder_test.py`. No DLL
rebuild is required for this test. Local tests validate registration, gates,
material selection and the absence of native compositor calls, not DCS pixels.

## After the static test passes

### Observed result: 2026-11-01 17:52

The screenshot shows the four quadrants in the expected orientation,
the white marker at upper left, the black cross and aperture clipping. Left EO,
right HSD and HUD remain visible. At 17:51:55.281 the captured log reports
`centre holder static-texture test active; native compositor disabled; direct sources retained`.
No missing `holder_test.tga` texture message was found. The existing missing
`green` texture message remains. Local evidence is retained in
`tmp/compositor-holder-test-20261101-175208/` (log, screenshot and config).

This establishes static texture sampling and holder presentation in that run.
It does not establish native named-texture binding, bake output, colour accuracy,
VR or head-movement behaviour. The next experiment below remains necessary.

## Test 2: centre-only native bake

The updated adapter supports `start(resolution,1)` for a centre-only diagnostic.
Rebuild it with `native/displays/build.ps1` before this test. Fully exit DCS
after installing the DLL: page brightness registration pins the module until
process exit.

In `render_config.lua`, set:

```lua
enabled=false,
holder_test=false,
bake_test=true,
bake_test_source="pattern",
```

Restart DCS and load the same mission with main power on. The centre map is
temporarily replaced with a texture-free mesh pattern: red/green above,
blue/yellow below, a black cross and white marker at upper left. This source
has no camera or chart texture and no outer white border. The holder now uses
the native named texture `F117_LCD_CENTRE`, retaining the tested presentation
settings. The diagnostic uses `F117_LCD_TEST_READY`; ordinary compositor
readiness stays zero. Left EO, right HSD and HUD keep their direct paths.

Look for these messages, including the second message's actual context, index
and resolution values:

```
centre native bake test requested; ordinary three-screen compositor disabled
centre native bake test active: marker=F117_BAKE_TEST_SOURCE context=... index=... texture=F117_LCD_CENTRE resolution=...; pixels unverified
```

The initial pattern draws directly until native setup succeeds. Therefore a
visible pattern without the `active` message does not validate native baking.
On success the adapter creates exactly one baker, switches only the dedicated
centre source to BAKE, then enables its holder. Init failure leaves that source
drawing directly and the holder hidden. The host checks centre-only discovery,
activation, rollback, retry conditions, idempotence and rejection of a mode
change within one owner. It does not render DCS pixels.

Save a screenshot and `dcs.log`. With the `active` message present:

| Result | Next investigation |
| --- | --- |
| Pattern visible | Native production and named-texture sampling work for this simple source. Restore the map in a separate experiment. |
| White output | Static holder already worked; isolate native channel binding versus bake output next. Do not infer which from white alone. |
| Black/absent/malformed output | Investigate source projection, bake scheduling and target binding, retaining the exact logged source details. |

Set all three switches false and restart to restore the normal map/direct path.
The generic chart device remains registered during the test, but the mesh
pattern does not sample its texture.

### Observed result: 2026-11-01 17:58

The log confirms centre native bake activation at 17:57:59.459 with marker
`F117_BAKE_TEST_SOURCE`, context `00007FFF8C41B5F0`, zero-based source index 1,
texture `F117_LCD_CENTRE` and resolution 256. The screenshot shows the
four-colour mesh pattern, black cross and upper-left white marker. Its colours
look darker than the static-texture test; colour accuracy is not established.
No missing `F117_LCD_CENTRE` texture message was found. Evidence is retained
locally in `tmp/compositor-bake-test-20261101-175811/`. Adapter SHA-256:
`3AFF2B16FFF0605A0EF8C12D2FC3337B16B07DA4272065DC180EA472803BE10E`.

Together, screenshot and activation log support successful simple-source native
baking and named-texture presentation in this run. The historical white output
has not been reproduced. Map/chart sampling and three-channel activation remain
untested by this experiment. Next isolate the real map in the same centre-only
path before trying all three channels.

## Test 3: real map through the centre-only bake

Keep `enabled=false`, `holder_test=false` and `bake_test=true`, but set
`bake_test_source="map"`. Fully restart DCS and load the same mission. This
retains the normal map page, adding the diagnostic marker to it. The same
single-channel adapter and `F117_LCD_CENTRE` holder now bake the map rather than
the texture-free pattern. No further DLL rebuild is needed after Test 2.
Resolution still follows the same DCS option; Test 2 used 256, so softness at
that size should be assessed separately from white output.

Look for `centre native bake test source=map`, followed by
`centre native bake test active: marker=F117_BAKE_TEST_SOURCE ...`.
Both matter: the map draws directly until native activation succeeds. Save
the screenshot and log. Check the map outline, text and sampled chart image;
also compare left EO, right HSD and HUD with the baseline. The chart can finish
camera alignment after bake activation, so allow it time to appear.

If white output appears only with this source, the failure is associated with
the real page or its sampled content rather than the simple-source native path.
Next separate map meshes/strokes from chart-texture sampling. If the full map
works, test three-channel activation separately. Return all diagnostic switches
to false and restart to restore direct drawing.

### Observed result: 2026-11-01 18:13 (1024 resolution)

The captured log confirms map-bake activation at 18:12:37.215 with resolution
1024. The screenshot still lacks centre labels, although chart content and
some line outlines are visible. Raising resolution alone did not restore text.
Evidence: `tmp/compositor-map-test-20261101-181300/`.

The next controlled experiment sets `bake_test_specular=false` with the map
diagnostic still active at 1024. This changes only the centre map indicator's
`shaderLineUseSpecularPass` setting; the direct path, pattern source and side
indicators retain their original setting. Look for
`centre map bake stroke specular pass=false` followed by native activation.
This is an experiment, not an established fix. Set the option true to repeat
the previous pass selection.

### Observed result: 2026-11-01 18:16 (specular pass disabled)

The log explicitly reports `centre map bake stroke specular pass=false`, then
native activation at 18:16:18.312 with resolution 1024. The screenshot still
shows chart content and line outlines without centre labels. This setting
change did not restore text. Evidence is retained locally in
`tmp/compositor-map-test-20261101-181630/`.

Both fixed labels and readouts are absent in the supplied map screenshots;
this is not evidence of only a text-parameter update problem. Next isolate a
fixed `ceStringPoly` label using the same `ceSLineFont` alongside a simple
`ceSMultiLine` glyph in a minimal bake source, without chart sampling or text
controllers. Compare direct and baked drawing before changing font settings.
The current evidence does not establish the underlying text-rendering cause.

## Test 4: fixed font text versus line glyphs

Set `bake_test_source="text"`, retaining `enabled=false`, `holder_test=false`,
`bake_test=true`, `resolution=1024`, `bake_test_specular=false` and
`bake_test_direct=false`. Fully restart DCS. No DLL rebuild is needed.

The centre now has a dark background with three rows, all reading `TEST 123`:

1. Upper row: large fixed `ceStringPoly` text using the normal `ceSLineFont`.
2. Middle row: independent `ceSMultiLine` glyphs.
3. Lower row: fixed font text at the map readout size.

A white mesh bar below the rows provides a non-text reference. There are no
chart textures, text parameters or per-label visibility controllers. Main power
still gates the source. Brightness registration retains the centre marker.

The log must identify `source=text`, specular pass false and native activation
at 1024. Capture the screen and log. If line glyphs/bar appear without either
font row, the problem reproduces on fixed font text without the map. If large
font text appears but the map-size row does not, investigate text size/scaling
separately. If both font rows appear, return to map-specific settings.

To compare the identical source without baking, set `bake_test_direct=true`
and restart. This leaves the source drawing directly, the holder hidden and
both readiness flags zero. The log reports `direct comparison active; native
bake not started`. The adapter is not loaded by the compositor in this mode;
other native services can still load it. Capture the same view before drawing
conclusions about font support in the bake pass.

### Observed result: 2026-11-01 18:21 (text source baked)

The log confirms `source=text`, specular pass false and native activation at
18:21:38.898 with resolution 1024. The screenshot shows the middle line-drawn
`TEST 123` and mesh reference bar; the upper and lower font-text rows are not
visible. The failure therefore reproduces without chart sampling, dynamic text
parameters or map-specific visibility controllers. A direct drawing comparison
of this identical source is still required before attributing it to baking.
Evidence: `tmp/compositor-text-test-20261101-182149/`.

### Observed result: 2026-11-01 18:24 (same text source direct)

At 18:24:02.600 the log confirms `centre diagnostic source=text direct
comparison active; native bake not started`. Both the upper large-font and
lower map-size font rows are visible in the supplied screenshot, along with
the middle line glyphs and reference bar. Evidence is retained locally in
`tmp/compositor-text-direct-20261101-182413/`.

Compared with the baked run, this isolates an observed failure of
`ceStringPoly` text using this `ceSLineFont` in the current native bake path.
It does not establish whether the cause is a missing text render pass, native
configuration, or another renderer requirement. Resolution and specular-pass
changes tested so far did not restore text. The historical white centre image
is a separate symptom and has not been reproduced in these experiments.

A practical integration option is to bake background/chart content while
retaining font text in a direct overlay. Alternatively, investigate the native
text-rendering path before enabling a compositor that captures complete pages.
Neither approach is implemented by this diagnostic comparison.

### Native cause identified: wrong stroke-text element class (2026-11-01)

The pages paired a `ceSLineFont` with `ceStringPoly`. This can draw directly,
but it bypasses the indicator stroke-parameter override required for baking.
The correction uses `ceStringSLine` for the operational stroke-font pages
(HUD, VSD, HSD, EO overlay and map) and the isolated text test. Bitmap calibration
text retains `ceStringPoly`. The layout editor and calibration checks now
recognize both classes, and regression checks reject the old pairing.

`ceStringSLine` applies the indicator's stroke-parameter scaling when
`shaderLineParamsUpdatable=true`. A `ceStringPoly` using `ceSLineFont` keeps the
font's own values, so its strokes are not scaled during baking.

This explains why enlarging glyphs or target resolution did not fix the missing
strokes. The earlier indicator specular-toggle experiment did not test the old
font's separate specular flag. No engine binary patch, renderer hook, or
direct-text overlay workaround is required for this correction.

Validation before enabling the next diagnostic: all 98 mod tests, all 11
packaging tests and the calibration checker pass. DCS visual confirmation of
the correction is still pending. The next run is prepared with centre-only
`source="map"`, native baking at 1024, direct comparison disabled and the
previous `specular=false` setting retained. The log identifies
`text class=ceStringSLine`. Expect the chart plus top/bottom menu labels, GS/CRS
readouts and range text. Check that these update and dim normally as well.
The original historical all-white image remains unreproduced; this finding
addresses the reproducible missing-label failure.

### Observed result: 2026-11-01 18:02

The captured log reports `source=map` and centre-only activation at
18:02:05.772, marker `F117_BAKE_TEST_SOURCE`, source index 1, texture
`F117_LCD_CENTRE`, resolution 256. The chart camera aligns at 18:02:11.116.
The screenshot shows the chart and some outlines, with centre labels absent or
much less visible than the direct baseline. There is no white centre image.
No missing compositor texture or font message was found in the targeted log
search. Local evidence: `tmp/compositor-map-test-20261101-180234/`.

This is partial success: sampled chart content reaches the baked holder, but
overlay readability has regressed. Do not describe the real map as fully
validated. Next repeat at an explicit `resolution=1024`, leaving the source and
channel configuration unchanged. If labels remain absent, isolate the stroke
renderer/specular-pass settings in the bake path separately. Neither possible
cause is established by this screenshot and log.
