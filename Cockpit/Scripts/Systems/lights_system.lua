-- Exterior and cockpit lighting. Each switch toggles one light; the light's state
-- drives a draw argument on the exterior model. Also turns the beacon and makes
-- the platypus exhaust glow follow engine rpm.
dofile(LockOn_Options.script_path.."command_defs.lua")

local STEP = 0.05 -- s
make_default_activity(STEP)

local device = GetSelf()
local base_data = get_base_data()
local flood_level = get_param_handle("FLOOD_LGT") -- cockpit flood light, mainpanel_init arg 180

-- name = {toggle command, exterior draw argument}
local LIGHTS = {
    landing = {Keys.LdgLight, 190},
    nav     = {Keys.NavLight, 191},
    taxi    = {Keys.TaxiLgt, 192},
    beacon  = {Keys.BcnLgt, 193},
    flood   = {Keys.FloodLight, 194},
    panel   = {Keys.PanelLight, 195},
    meme    = {Keys.MemeLgt, 1000},
}

-- Lights that are on at spawn. Any light not listed starts off. An unknown spawn
-- type is treated as a hot start on the ground.
local ON_AT_SPAWN = {
    GROUND_HOT  = {landing = true, nav = true, taxi = true, beacon = true, panel = true},
    AIR_HOT     = {landing = true, nav = true, beacon = true, panel = true},
    GROUND_COLD = {},
}

local light_on = {}
local light_for_command = {}
for name, light in pairs(LIGHTS) do
    light_on[name] = false
    light_for_command[light[1]] = name
    device:listen_command(light[1])
end

local sound_host, click -- keep the host referenced, or its sounds go with it

function post_initialize()
    sound_host = create_sound_host("LIGHT_SWITCHES", "3D", 0, 2.0, 0)
    click = sound_host:create_sound("Aircrafts/F-117/Cockpit/Click")
    local spawn = ON_AT_SPAWN[LockOn_Options.init_conditions.birth_place] or ON_AT_SPAWN.GROUND_HOT
    for name in pairs(LIGHTS) do
        light_on[name] = spawn[name] == true
    end
end

function SetCommand(command)
    local name = light_for_command[command]
    if name then
        light_on[name] = not light_on[name]
        if click then click:play_once() end
    end
end

-- The beacon turns at 85 rpm. Argument 1001 is its rotation phase, 0 to 1, and
-- reads 0 while the beacon is off. The phase keeps turning either way.
local BEACON_RPM = 85
local beacon_phase = 0.5

-- Platypus heat glow, draw arguments 1002 (left) and 1003 (right). The slot tiles heat and
-- cool slowly, so the glow follows engine rpm through a lag. Nothing shows below 60 % rpm,
-- a trace at ground idle, and full glow at military power. The lights' brightness and
-- colour are set in lights_data in F-117-NightHawk.lua.
local GLOW_RPM_START = 0.60 -- rpm fraction: get_base_data reports 0 to 1 for this EFM
local GLOW_TIME_CONSTANT = 6.0 -- s
local glow = {0, 0}

local function glow_target(rpm)
    local x = math.max(0, math.min(1, ((rpm or 0) - GLOW_RPM_START) / (1 - GLOW_RPM_START)))
    return x * x
end

local function update_platypus_glow()
    local k = STEP / (GLOW_TIME_CONSTANT + STEP)
    local rpm = {base_data:getEngineLeftRPM(), base_data:getEngineRightRPM()}
    for i = 1, 2 do
        glow[i] = glow[i] + (glow_target(rpm[i]) - glow[i]) * k
        set_aircraft_draw_argument_value(1001 + i, glow[i])
    end
end

-- Inlet fan, draw arguments 324 (left) and 325 (right). Each is a rotation phase, 0 to 1,
-- one full turn per unit, and wraps like the beacon's. The turn rate follows engine rpm.
-- The device runs at 1/STEP = 20 Hz, so the fan would strobe once it passes half a blade
-- spacing per step: 17 blades is 10.6 degrees, about 35 rev/min. The rate is capped just
-- under that, which makes full power a slow, steady turn rather than a flicker.
local TURBINE_FULL_RPM = 30 -- fan rev/min shown at full engine rpm
local turbine_phase = {0, 0}

local function update_turbines()
    local rpm = {base_data:getEngineLeftRPM(), base_data:getEngineRightRPM()}
    for i = 1, 2 do
        local fraction = math.max(0, math.min(1, rpm[i] or 0))
        turbine_phase[i] = (turbine_phase[i] + STEP * fraction * TURBINE_FULL_RPM / 60) % 1
        set_aircraft_draw_argument_value(323 + i, turbine_phase[i])
    end
end

local function level(on)
    return on and 1 or 0
end

function update()
    update_platypus_glow()
    update_turbines()
    beacon_phase = (beacon_phase + STEP * BEACON_RPM / 60) % 1
    for name, light in pairs(LIGHTS) do
        set_aircraft_draw_argument_value(light[2], level(light_on[name]))
    end
    set_aircraft_draw_argument_value(1001, light_on.beacon and beacon_phase or 0)
    flood_level:set(level(light_on.flood))
end

need_to_be_closed = false -- update() runs every step, so the state stays open
