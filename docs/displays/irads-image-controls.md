# IRADS brightness and contrast

The upstream DCS FLIR image has scene-dependent exposure before these controls
are applied. See [the auto-exposure investigation](irads-auto-exposure.md) for
the behavior notes and aircraft-specific compatibility requirements. No exposure
override is installed by the mod.

IR Level has one consistent internal video-multiplier range of 0.025-0.80 in
day and night. Its normalized control position `u` maps to
`brightness = 0.025 + 0.775*u*u`. Forty button steps cover the full control
travel; axes are continuous. This gives fine adjustment in the sensitive low
range and enough upper travel for settled daytime ground imagery. The L bar
shows control travel, not the internal multiplier. G retains its existing
35-100% contrast range and linear indication.

IRADS now starts at 60% internal video brightness by day (08:00-17:00) and 6.5% at
night (19:00-06:00), with linear transitions from 06:00-08:00 and 17:00-19:00.
These are provisional DCS presentation defaults, not measured real IRADS
settings. The reference recordings guide tonal balance (deep blacks, readable
midtones, isolated highlights); their L/G positions cannot calibrate DCS values.
This uses local mission clock time, not calculated solar elevation. Contrast
starts at 80% by day and 96% at night, with the same twilight transitions. These are initial tuning values for in-game review.

The centre camera image clips to solid green at full material colour. Its material colour,
`irads_video_colour` in `display_readability.lua`, therefore holds the video at
green 90 of 255 on top of that control. Symbols and the left EO repeater are unaffected.

| Action | Default keyboard binding |
| --- | --- |
| IR Level increase/decrease (brightness) | Left Ctrl + Left Shift + Page Up/Page Down |
| IR Gain increase/decrease (contrast) | Left Ctrl + Left Alt + Page Up/Page Down |

These use the stock I-251 brightness and contrast commands, listed in Controls under
Throttle Grip / HOTAS / **F-117A IRADS** as IR Level and IR Gain, with matching axes.
There is no reset command. Level steps by 2.5% of normalized control travel;
contrast steps by 5 points within 35-100%. Axes map their full travel to these ranges.
Manual settings remain until mission reload; changing sensor power,
page or mission clock does not override them.

Video contrast now uses DCS's built-in generic `set_contrast_raw` controller.
It sets the texture shader's power exponent:
the day preset is neutral (1.0), and the night preset uses 1.2 to darken midtones
while retaining highlights. The old grey contrast blend has been removed.
The controller takes a literal numeric argument, so 66 mutually exclusive video
quads select 1% contrast steps. Exactly one quad draws, sampling the same camera
target. IR Level scales video and symbology. Centre symbology also follows the existing centre
display brightness control (`CDBrightness`), with the display's day/night startup
brightness and power fade. The left EO repeater applies the lower of left-display brightness and Level
to both image and markings. Gain continues to control video contrast. Image-only black dim layers stay active in both native and fallback modes.
Symbol opacity remains the fallback when native brightness cannot initialize.
No extra camera texture or native compositor is introduced. Restart DCS to load
new default input profiles; verify visual levels in a daytime and night mission.

The left/right VSD and HSD now use native renderer RGB gain, preserving
opaque artwork and depth/stencil clipping. Their final black dimming layers
are enabled only for fallback. They start at 12% luminance at night
and full luminance by day, with the same twilight ramps. Their existing
brightness parameters remain manually adjustable.

## Native brightness bridge

`bin/F117Displays.dll` now exports `luaopen_f117_brightness`, independently of
its optional compositor export. This path does not create bakers, change draw
purposes, or change display geometry. Each page captures its actual material
names at `Add`, including colors created by Layout Studio. The module keeps those
names, because DCS closes a page's Lua state straight after loading it. The display
device locates all five current indicators by unique
markers on each update: HUD, VSD, HSD, IRADS symbology and IRADS video.

Once the checks in `native/displays/README.md` pass, the bridge registers each page's materials using the native renderer's
`read_from_state` / `brightness_sensitive_materials` facility. It checks that
all materials resolved before activation, then calls native `change_brightness`
for RGB gain. The camera material and native video shader stay neutral (gain 1, shader setting
0.5). Image-only black layers apply Level before the markings are drawn. Live
checks showed that raw `mfd0` copies did not respond to opacity as RGB gain or
to the separate native shader setting; mesh dimming does. This keeps the same
Level behavior in direct drawing, baked centre output and fallback.

Native entry points are resolved by name. No vtables or engine binaries
are patched. A build mismatch, missing loader, missing page or unresolved
material leaves the existing dimming path active. Live discovered renderers
are reset to neutral before falling back following a missing page/material.

On success, `F117_NATIVE_BRIGHTNESS_ACTIVE=1` and whole-display fallback
dimmers become zero; the image-only IRADS/EO dim layers stay active. HUD/IRADS symbol drawing opacity becomes one; their actual brightness handles
remain unchanged for manual controls. Direct centre video quads are excluded from
the native symbol-material registration. Independent black layers dim the centre
and EO images beneath their markings, with symbols following Level through native gain or fallback opacity,
without changing upstream DCS exposure.
The mission-time defaults and keyboard
bindings above remain in effect. Log category `F117_BRIGHTNESS` reports
`native HUD/MFD/DEP renderer brightness active` or the fallback reason. Fully restart
DCS after changing these pages. This implementation uses the existing DLL; no
native interface change is required. Host tests run real DCS Lua 5.1 with instrumented
renderer APIs; they verify the handover and lifecycle, not live rendered pixels.

## OCIP III display selection

The left CMDI starts in colour VSD; the centre shows green IRADS and the right
CMDI starts in colour MAP. Ctrl+Shift+E toggles left EO/VSD. Keyboard and joystick
profiles expose Left CMDI Select VSD / EO / MAP / HSD and Right CMDI Select
MAP / HSD / VSD under F-117A Displays. These are mod controls.

Left EO repeats the existing `mfd0` camera texture in grayscale, with a fitted
sensor overlay. It creates no second sensor or camera render target. Centre video
and symbols use green materials. The native compositor includes centre video and
symbols together; the standalone target-zero camera remains the only source.
Each side has one native brightness registration for all its formats.

Selecting formats preserves sensor power, pointing, FOV and designation. EO with
the sensor off leaves its video area black. Left EO luminance is the lower of
left display and IRADS brightness; its symbols follow the same level.
Left MAP/HSD/VSD use left display brightness;
right formats use right brightness. IRADS image controls affect centre IRADS and
the left EO repeater, independently of MAP.

FOV buttons and the axis select only wide/narrow endpoints. Saved direct EFM zoom
bindings must be rebound to the current FOV commands; the installed EFM still
retains a legacy intermediate preset internally. Endpoint optical values have not
been recalibrated. See [README](../../README.md#ocip-iii-displays).

Offline checks cover format exclusivity, power gating, native write-only element
properties, sensor-state isolation, FOV dispatch and brightness. Live imagery,
colour, stencil clipping, native baking and VR require an in-DCS mission check.

## Screenshot calibration

For the next visual review, with DCS closed, use
`python tools/missions/irads_level_shots.py --run --variant both --transitions`.
This uses the production Level mapping and limits, with no range override. Each
variant captures its default and six nearby/reference internal values (0.05,
0.065, 0.10, 0.40, 0.60, 0.80), each looking at ground, sky, newly reacquired
ground (0.25-second dwell), and settled ground (one-second dwell). The early
capture follows LOS acquisition and is not an instantaneous exposure trace.
These are 28 captures per variant, saved under `<variant>/transitions/`.
Use `--levels .05 .6` for a shorter two-level check plus the startup default.
The final live check used this 12-frame sequence in each lighting condition.

Both test modes add a corridor of industrial structures and moving unarmed
trucks, including trucks positioned near actual roads. DCS generates their
thermal appearance. Object visibility, temperature contrast and exposure timing
still require review in DCS; the offline tests do not validate those pixels.

With DCS closed, run `python tools/missions/irads_level_shots.py --run --variant day`
or use `--variant night`. The runner temporarily extends IR Level to 0-1,
holds the sight on the ground, and captures the startup default followed by all
41 values at increments of 0.025. Gain remains at its day/night preset.
Each capture settles for one second; allow about one to four minutes including
screenshot time per variant. Progress is printed every five seconds, and a step
that cannot settle fails after 30 seconds. Results and actual settings are saved under
`tools/missions/results/irads_level/<variant>/`.

The runner installs `Cockpit/Scripts/Systems/IRADS_LevelCalibration.local.lua`
before launching DCS and removes it on exit, including handled errors and Ctrl+C.
Normal operation retains the 0.025-0.80 range. If the Python process is forcibly
killed, close DCS and delete that temporary file before flying normally or
rerunning the test. Building or opening the mission alone does not extend the range.

## Sensor display symbols

The symbol layout follows TO 1F-117A-1 Figure 4-17 and the recorded frames in
`docs/reference/CockpitImages/IRADS`: a grid of 30 columns by 15 rows, with the
top row (ALT, range, TTI or TTG) and bottom row (target latitude and longitude, or
the gray scale with no target) on black bands outside the picture.

- Range reads `LR` in feet while the laser fires, `ER` in feet while designated
  without it, and `R` in nautical miles to the INS destination otherwise.
- Time reads `TTI` from release until the designation is dropped, holding at 00:00
  after impact. Otherwise it reads `TTG` to the release point while designated, or
  to the INS destination.
- The letters over the reticle are the laser mode: `A` armed, `AF` firing, `AX`
  designated but not firing.
- `L` shows normalized nonlinear Level control travel; `G` shows the existing
  normalized contrast control. These are presentation proxies for real thermal
  controls, not calibrated thermal level/gain measurements.
- The lower-right area is reserved for I BIT/P BIT sensor failure messages
  (Figure 4-17, item 17); weapon release-fault captions are not drawn there.
  `RDY` remains at the upper left when release is ready. EFM release gates and
  status publication are unchanged.
