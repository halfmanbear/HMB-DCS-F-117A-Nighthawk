# IRADS brightness and contrast

IRADS now starts at 65% display brightness by day (08:00â€“17:00) and 16% at
night (19:00â€“06:00), with linear transitions from 06:00â€“08:00 and 17:00â€“19:00.
This uses local mission clock time, not calculated solar elevation. Contrast
starts at 80% by day and 96% at night, with the same twilight transitions. These are initial tuning values for in-game review.

| Action | Default keyboard binding |
| --- | --- |
| Brightness increase/decrease | Left Ctrl + Left Shift + Page Up/Page Down |
| Contrast increase/decrease | Left Ctrl + Left Alt + Page Up/Page Down |
| Reset for current mission time | Left Ctrl + Left Shift + Home |

Buttons and brightness/contrast axes are available under **F-117A IRADS** in
Controls. Brightness steps by 5 percentage points within 8â€“100%; contrast steps
by 5 points within 35â€“100%. Axis inputs map their full travel to these ranges.
Manual settings remain until reset or mission reload; changing sensor power,
page or mission clock does not override them.

Video contrast now uses DCS's built-in generic `set_contrast_raw` controller.
It sets the texture shader's power exponent:
the day preset is neutral (1.0), and the night preset uses 1.2 to darken midtones
while retaining highlights. The old grey contrast blend has been removed.
The controller takes a literal numeric argument, so 66 mutually exclusive video
quads select 1% contrast steps. Exactly one quad draws, sampling the same camera
target. Native renderer gain controls brightness separately; symbology follows
brightness only. The black alpha layer and symbology opacity remain as an
automatic fallback when native brightness cannot initialize.
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

For the verified CockpitBase SHA-256 recorded in `native/displays/README.md`,
the bridge registers each page's materials using the native renderer's
`read_from_state` / `brightness_sensitive_materials` facility. It checks that
all materials resolved before activation, then calls native `change_brightness`
for RGB gain. Camera video also calls native `set_mfd_shader_brightness`:
0.5 is neutral, and existing gain is translated to `0.5 + (gain-1)/1.6`, using
the installed MFD shader's negative brightness branch. This translation can
produce slightly negative native settings at the darkest gains; the native
setter accepts a float and the shader output is clamped. The resulting visual
match still requires review in DCS.

Native entry points are resolved by name. No vtables or engine binaries
are patched. A build mismatch, missing loader, missing page or unresolved
material leaves the existing dimming path active. Live discovered renderers
are reset to neutral before falling back following a missing page/material.

On success, `F117_NATIVE_BRIGHTNESS_ACTIVE=1` and legacy dimmer opacity becomes
zero. HUD/IRADS drawing opacity becomes one; their actual brightness handles
remain unchanged for manual controls. The mission-time defaults and keyboard
bindings above remain in effect. Log category `F117_BRIGHTNESS` reports
`native HUD/MFD renderer brightness active` or the fallback reason. Fully restart
DCS after replacing the DLL. Host tests run real DCS Lua 5.1 with instrumented
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
left display and IRADS brightness. Left MAP/HSD/VSD use left display brightness;
right formats use right brightness. IRADS image controls affect centre IRADS and
the left EO repeater, independently of MAP.

FOV buttons and the axis select only wide/narrow endpoints. Saved direct EFM zoom
bindings must be rebound to the current FOV commands; the installed EFM still
retains a legacy intermediate preset internally. Endpoint optical values have not
been recalibrated. See [README](../README.md#ocip-iii-displays).

Offline checks cover format exclusivity, power gating, native write-only element
properties, sensor-state isolation, FOV dispatch and brightness. Live imagery,
colour, stencil clipping, native baking and VR require an in-DCS mission check.
