-- F-117A Panel Gauges device
-- Reads simulation data via get_base_data() and pushes named parameters
-- consumed by mainpanel_init.lua "parameter" gauges.
-- Required because make_flyable does not auto-wire base_gauge_* to the panel.

dofile(LockOn_Options.script_path .. "command_defs.lua")

local update_time_step = 0.05
make_default_activity(update_time_step)

local sensor_data = get_base_data()
local RAD_TO_DEG  = 57.295779513

-- Parameters consumed by mainpanel_init.lua
local PANEL_PITCH    = get_param_handle("PANEL_PITCH")    -- degrees
local PANEL_BARO_ALT = get_param_handle("PANEL_BARO_ALT") -- metres, pre-cycled
local PANEL_IAS      = get_param_handle("PANEL_IAS")      -- m/s
local PANEL_AOA      = get_param_handle("PANEL_AOA")      -- radians
local PANEL_FUEL     = get_param_handle("PANEL_FUEL")     -- kg (0–8255)

-- BaroAlt cycle constant (1000 ft = 304.8 m per revolution)
local BARO_CYCLE = 304.8

function update(dt)
    PANEL_PITCH:set(sensor_data.getPitch() * RAD_TO_DEG)
    PANEL_IAS:set(sensor_data.getIndicatedAirSpeed())
    PANEL_AOA:set(sensor_data.getAngleOfAttack())

    local baro = sensor_data.getBarometricAltitude()
    PANEL_BARO_ALT:set(baro % BARO_CYCLE)

    PANEL_FUEL:set(sensor_data.getTotalFuelWeight())
end
