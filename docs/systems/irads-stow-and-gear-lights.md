# IRADS stow and gear projector correction (19 November 2026)

The first forward-hold implementation replaced the rendered orientation without
resetting the native gimbal or slew cache. TDC input consequently restored the old
angles. Scan return now seeks home at a controlled rate. On arrival it resets both
platform motors (current and target), then clears/rebases the sensor slew cache.
The simulation and camera callbacks hold forward only after that arrival.

The light device publishes F117_LIGHT_LANDING and F117_LIGHT_TAXI after applying
the gear interlocks. The EFM sends those values through DCS's external-light power
API independently of IRADS power. It publishes the returned native power and logs
switch changes as `Gear projector:` for the next in-game check. The native child
indices used are 1 and 5 for Lua landing/taxi groups 2 and 6; visual verification
of the selected projectors remains required. Changing EDM draw arguments alone
was insufficient to establish native projector power.

The inherited command 328 keeps its ID and is labelled Landing Light ON/OFF.
Command 1398 remains Taxi Light ON/OFF. The saved WINWING throttle profile had both
JOY_BTN99 and JOY_BTN88 on command 1398. The extra JOY_BTN88 entry was removed;
the original profile is backed up at tmp/taxi-binding-before.diff.lua.

## Validation

The compiled regression executes production homing code with separate motor,
target and slew-cache state, checks gradual motion, forward hold in turns and the
first post-stow slew. Another compiled harness checks the production light-power
bridge, including independent on/off requests and absent cockpit handling.
Cockpit Lua tests exercise gear retraction outputs. DCS visual beam placement,
light-group selection and real native slew handoff still require a flight check.

## Exterior animation follow-up

Argument 903 now follows the native sensor's body-relative elevation while powered,
and returns to the authored stow key when unpowered. The lens normals and authored
quaternion keys give approximately +44.2 degrees at 0 and -85.24 degrees at 1;
forward aim therefore uses about 0.3415. This is one pitch axis; housing azimuth
cannot follow without adding another model animation. The Lua lighting device
limits travel to 60 degrees/second, driven by F117_IRADS_HOUSING_TARGET from the EFM.

Argument 39 is the model's authored head/upper-body yaw animation. It is now in
net_animation so DCS's native player head movement can synchronize to other clients.
The EFM leaves 39 untouched. No camera-command approximation or external-view camera
position is used as head tracking. Local tracking behavior remains an in-DCS check;
this configuration change does not add a separate head-pose source. The legacy
coupled-control arguments 9/10, which the current EFM does not drive, were removed
from synchronization to keep the DCS network list within 32 entries.

The taxi projector outer cone is reduced from 35 to 12 degrees, its inner cone
from 20 to 5 degrees, and its aim from -3 to -1.5 degrees. Startup no longer changes
the configured cone width. This should produce a defined forward ground footprint;
its final appearance still needs a night taxi check in DCS.
