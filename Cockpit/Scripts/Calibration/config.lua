-- TEMPORARY calibration indicators. Reload the aircraft after any change.
-- Set enabled=false to remove calibration indicators; the VSD and HSD remain.
local layout = dofile(LockOn_Options.script_path.."HUD/Indicator/layout_profile.lua")
return {
    enabled = false,
    hud = {
        enabled = false,
        -- Same mounting correction as the existing HUD, in metres.
        mount = {sx_l=0, sy_l=0.03, sz_l=0, sh=0, sw=0, rz_l=0, rx_l=0, ry_l=0},
        -- Angular origin in milliradians, relative to the connector optical axis.
        -- Initial visual fit from the centred cockpit capture; not yet boresight-calibrated.
        origin = layout.origin_mrad,
        half_width_deg = layout.half_width_deg,
        half_height_deg = layout.half_height_deg,
        -- Diagnostic gains; leave at 1 until mounting and projection are checked.
        scale_x = 1,
        scale_y = 1,
        pitch_gain = -1000, -- PITCH_HUD is radians; layout is milliradians.
        roll_gain = 1,      -- ROLL_HUD and rotation controller both use radians.
    },
    centre = {enabled=true, offset={0,0}, scale_x=1, scale_y=1},
    left   = {enabled=false, offset={0,0}, scale_x=1, scale_y=1},
    right  = {enabled=false, offset={0,0}, scale_x=1, scale_y=1},
}
