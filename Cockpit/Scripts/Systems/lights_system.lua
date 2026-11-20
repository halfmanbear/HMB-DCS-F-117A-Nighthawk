-- Exterior and cockpit lighting. Each switch toggles one light; the light's state
-- drives a draw argument on the exterior model. Also turns the beacon and makes
-- the platypus exhaust glow follow engine rpm.
dofile(LockOn_Options.script_path.."command_defs.lua")

local STEP = 0.05 -- s
make_default_activity(STEP)

local device = GetSelf()
local base_data = get_base_data()
local flood_level = get_param_handle("FLOOD_LGT") -- cockpit flood light, mainpanel_init arg 180
local panel_level = get_param_handle("PANEL_LGT") -- cockpit backlights, arg 196
local beam_power = {landing=get_param_handle("F117_LIGHT_LANDING"),taxi=get_param_handle("F117_LIGHT_TAXI")}
local irads_housing_target = get_param_handle("F117_IRADS_HOUSING_TARGET")
local irads_housing = 0
local light_ready = get_param_handle("F117_LIGHT_CONTROL_READY")
local mainpower = get_param_handle("mainpower") -- engine generator or ground power

-- name = {toggle command, exterior draw argument}
local LIGHTS = {
    landing = {native_commands.LANDING_LIGHT, 190},
    nav     = {native_commands.NAV_LIGHTS, 191},
    taxi    = {native_commands.TAXI_LIGHT, 192},
    beacon  = {native_commands.BEACON_LIGHT, 193},
    flood   = {Keys.FloodLight, 194},
    panel   = {native_commands.COCKPIT_LIGHT, 195},
}

-- Switch selections at spawn; panel output still requires bus power.
-- Any light not listed starts off. An unknown spawn
-- type is treated as a hot start on the ground.
local ON_AT_SPAWN = {
    GROUND_HOT  = {landing = true, nav = true, taxi = true, beacon = true, panel = true},
    AIR_HOT     = {landing = true, nav = true, beacon = true, panel = true},
    GROUND_COLD = {panel = true},
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
    panel_level:set(0)
    flood_level:set(0)
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
    -- 903 is the model's single pitch/stow animation. The EFM computes its
    -- target from the real sensor LOS; keep a finite mechanical travel rate.
    local target = math.max(0, math.min(1, irads_housing_target:get()))
    local travel = 60 / 129.44 * STEP -- 60 degrees per second
    irads_housing = irads_housing + math.max(-travel, math.min(travel, target-irads_housing))
    set_aircraft_draw_argument_value(903, irads_housing)
    beacon_phase = (beacon_phase + STEP * BEACON_RPM / 60) % 1
    for name, light in pairs(LIGHTS) do
        local powered = name ~= "panel" or mainpower:get() > 0.5
        -- Gear-mounted beams must be dark throughout retraction and while stowed.
        if name == "landing" or name == "taxi" then
            local args = name == "taxi" and {0} or {3, 5}
            for _,arg in ipairs(args) do
                if get_aircraft_draw_argument_value(arg) < .99 then powered = false end
            end
        end
        local output = level(light_on[name] and powered)
        set_aircraft_draw_argument_value(light[2], output)
        if beam_power[name] then beam_power[name]:set(output) end
    end
    light_ready:set(1)
    set_aircraft_draw_argument_value(1001, light_on.beacon and beacon_phase or 0)
    -- Keep switch selections through a power loss. Battery alone does not supply
    -- normal AC panel lighting; Electrical.lua publishes the supplied bus.
    panel_level:set(level(light_on.panel and mainpower:get() > 0.5))
    flood_level:set(level(light_on.flood))
end

need_to_be_closed = false -- update() runs every step, so the state stays open
