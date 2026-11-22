# IRADS scene-dependent exposure

## Behavior

Scene-dependent exposure can change the FLIR picture even when cockpit gain
and level controls remain stationary. Changes in exposure can also change
apparent contrast. In-game comparison is still required to establish the
visible effect across representative scenes.

The mod's `IRADS_ImageControls.lua` publishes presentation brightness and
contrast. Mission clock presets run at initialization; they do not continuously
retune the manual settings. `set_contrast_raw` applies a power exponent when
sampling the finished video texture. These presentation controls cannot recover
information already compressed or clipped upstream. IR Level currently controls
display luminance, and IR Gain controls the sampling power curve.

## Compatibility requirements

Any exposure override must affect IRADS only. Shared FLIR shader changes are
outside the scope of this feature. No exposure override is currently installed.

Prefer documented, aircraft-specific controls. Validate supported capabilities
before enabling an override, and retain normal rendering when those capabilities
are unavailable. Compatibility must be checked after simulator updates.

Automatic/manual sensor gain and level controls do not by themselves establish
control over scene-dependent exposure. An aircraft-specific exposure-disable
setting has not yet been verified.

## Validation

Hold gain and level fixed while slewing between ground, sky/horizon and scenes
containing hot objects. Repeat across fields of view, the centre display and left
EO repeater, and day/night conditions. Compare the same scenes before changing
manual tuning ranges. Scene temperature, atmosphere and display presentation
must also be considered when assessing the result.
