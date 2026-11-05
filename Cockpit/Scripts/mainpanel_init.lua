-- Cockpit model and the panel gauges that move its arguments. The header sets only
-- what the stock F-16C, FA-18C and TF-51D cockpits set; DCS defaults cover the rest.
-- Every argument below exists in Cockpit_F-117.edm except 153 (see control_stick.lua).

shape_name = "Cockpit_F-117" -- Cockpit/Shape/Cockpit_F-117.edm
draw_pilot = false
external_model_canopy_arg = 38 -- canopy argument on the exterior model

local base = LoRegisterPanelControls()

-- A gauge reads a cockpit parameter, or a stock base_gauge_* controller, and
-- maps it piecewise-linearly from input to output onto a model argument.
local function gauge(arg, input, output, source)
    local g
    if source:find("^base_gauge_") then
        g = CreateGauge()
        g.arg_number = arg
        g.input = input
        g.output = output
        g.controller = base[source]
    else
        g = CreateGauge("parameter")
        g.arg_number = arg
        g.input = input
        g.output = output
        g.parameter_name = source
    end
    return g
end

local FT = 0.3048 -- m
local KT = 1852 / 3600 -- m/s

CanopyPos  = gauge(181, {0, 100}, {0, 100}, "base_gauge_CanopyPos")
FloodLight = gauge(180, {0, 100}, {0, 100}, "FLOOD_LGT")       -- lights_system.lua
HideStick  = gauge(153, {0, 1}, {0, 1}, "HIDE_STICK")          -- control_stick.lua

-- Gauges.lua sets the PANEL_* parameters.
ADIPitch = gauge(1004, {-140, 140}, {-100, 100}, "PANEL_PITCH")
BaroAlt  = gauge(1005, {0, 1000 * FT}, {0, 1}, "PANEL_BARO_ALT") -- Gauges.lua wraps altitude every 1000 ft
indispeed = gauge(1006, {0, 200 * KT, 400 * KT, 600 * KT}, {0, 0.333, 0.6666, 1}, "PANEL_IAS")
AoAGauge = gauge(1007, {math.rad(-10), math.rad(10), math.rad(20)}, {-1, 0.5, 1}, "PANEL_AOA")
FuelGauge = gauge(22, {0, 8255}, {0, 1}, "PANEL_FUEL")

-- Radar altimeter dial: altitude in feet against needle position.
local RADAR_ALT_FT  = {0, 100, 200, 300, 400, 600, 800, 1000, 2000, 3000, 4000}
local RADAR_ALT_ARG = {0, 0.095, 0.206, 0.317, 0.46, 0.572, 0.683, 0.746, 0.841, 0.920, 1}
local radar_alt_m = {}
for i = 1, #RADAR_ALT_FT do
    radar_alt_m[i] = RADAR_ALT_FT[i] * FT
end
RadarAlt = gauge(523, radar_alt_m, RADAR_ALT_ARG, "base_gauge_RadarAltitude")

need_to_be_closed = true -- the panel needs nothing from this state after loading
