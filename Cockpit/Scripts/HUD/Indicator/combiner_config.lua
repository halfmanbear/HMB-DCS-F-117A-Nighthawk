-- Physical HUD aperture, shared by production and calibration indicators.
return {
    enabled = true,
    show_mask = false, -- temporary translucent glass-plane diagnostic
    inset_m = 0.002,   -- keep drawing just inside the measured glass edges
    offset_m = {0,0,0}, -- indicator-local corrections in physical metres
    -- Must match the HUD registration in device_init.lua.
    mount = {sx_l=0,sy_l=0.03,sz_l=0},
}
