-- Display power, staggered display boot and display data alignment.
-- Battery (stock Electric Power Switch) gates everything; the APU, an engine
-- generator or external ground power then powers the bus. Pages gate on the
-- numeric params published here. Also the ground crew's power and air carts.
dofile(LockOn_Options.script_path.."command_defs.lua")
local update_time_step=0.05
make_default_activity(update_time_step)
local dev=GetSelf()
local sensor=get_base_data()
local PowerBus=dofile(LockOn_Options.script_path.."Systems/PowerBus.lua")
local DisplayBoot=dofile(LockOn_Options.script_path.."Systems/DisplayBoot.lua")
local Alignment=dofile(LockOn_Options.script_path.."Systems/Alignment.lua")

local bus=PowerBus.new()
local alignment=Alignment.new()
local powered_time=nil -- seconds since bus power-up; nil while unpowered
local aligned=false    -- hot/air start: aligned and operational from spawn
local HOT_GRACE=2      -- seconds a hot start holds the generators online before RPM is trusted
local hot_grace=0

local mainpower=get_param_handle("mainpower")
local battery_param=get_param_handle("F117_BATTERY")
local apu_param=get_param_handle("F117_APU_STATE")
local gen_param=get_param_handle("F117_GEN_ONLINE")
-- The EFM owns the main engine starts (their starters run on APU, air cart or
-- crossbleed air) and publishes each engine's start phase (0 off, 1 motoring,
-- 2 light-off, 3 accelerating, 4 running), a count of starts refused for want of
-- start air, and weight on wheels.
local start_phase={L=get_param_handle("F117_ENGINE_START_L"),R=get_param_handle("F117_ENGINE_START_R")}
local start_rejected=get_param_handle("F117_ENGINE_START_REJECTED")
local wow=get_param_handle("F117_WOW")
local last_phase,last_rejected={},nil
-- Ground carts: external electrical power and start air, on the ground and stopped.
local ground_power_param=get_param_handle("F117_GROUND_POWER")
local ground_air_param=get_param_handle("F117_GROUND_AIR")
local ground={power=false,air=false}
local CART_CONNECT_SPEED=1     -- m/s: the crew only connect a cart to a stopped aircraft
local CART_PULL_OFF_SPEED=2    -- m/s: taxiing away pulls the leads and hoses off
local align={pitch=get_param_handle("F117_ALIGN_PITCH_ERR"),roll=get_param_handle("F117_ALIGN_ROLL_ERR"),
    hdg=get_param_handle("F117_ALIGN_HDG_ERR"),adc=get_param_handle("F117_ADC_BLEND")}
local displays={}
for _,name in ipairs(DisplayBoot.DISPLAYS) do
    -- F117_PWR_<D>: boot state 0-3. F117_ON_<D>: 1 when operational, for format gates.
    displays[name]={state=get_param_handle("F117_PWR_"..name),on=get_param_handle("F117_ON_"..name),
        stage=get_param_handle("F117_BOOT_STAGE_"..name),
        progress=get_param_handle("F117_BOOT_PROGRESS_"..name),fade=get_param_handle("F117_FADE_"..name)}
end

dev:listen_command(Keys.PowerOnOff)
dev:listen_command(Keys.APUToggle)
dev:listen_command(Keys.GroundPowerToggle)
dev:listen_command(Keys.GroundAirToggle)

local function message(text)
    if print_message_to_user then print_message_to_user(text) end
end

-- Cockpit base data reports the EFM's N2 as a 0-1 fraction (0.60 at ground
-- idle, checked in DCS on 3 November 2026); PowerBus works in percent.
local function rpm()
    local l=sensor.getEngineLeftRPM and sensor.getEngineLeftRPM() or 0
    local r=sensor.getEngineRightRPM and sensor.getEngineRightRPM() or 0
    return (tonumber(l) or 0)*100,(tonumber(r) or 0)*100
end

-- Start messages stand in for the START ENGD lights until the cockpit is clickable.
local function report_engine_start()
    local rejected=start_rejected:get()
    if last_rejected and rejected>last_rejected then message("ENGINE START NEEDS START AIR - APU OR AIR CART") end
    last_rejected=rejected
    for _,side in ipairs({"R","L"}) do
        local phase,last=start_phase[side]:get(),last_phase[side]
        if last then
            if phase==1 and last~=1 then message(side.." ENGINE START - STARTER ENGAGED")
            elseif phase==4 and last>=1 and last<=3 then message(side.." STARTER DISENGAGED") end
        end
        last_phase[side]=phase
    end
end

local function ground_speed()
    if not sensor.getSelfVelocity then return 0 end
    local vx,_,vz=sensor.getSelfVelocity()
    return math.sqrt((tonumber(vx) or 0)^2+(tonumber(vz) or 0)^2)
end

local function on_ground_and_stopped(speed)
    return wow:get()>.5 and ground_speed()<speed
end

local CARTS={power={name="GROUND POWER"},air={name="GROUND AIR"}}
local function toggle_cart(kind)
    if ground[kind] then
        ground[kind]=false
        message(CARTS[kind].name.." DISCONNECTED")
    elseif on_ground_and_stopped(CART_CONNECT_SPEED) then
        ground[kind]=true
        message(CARTS[kind].name.." CONNECTED")
    else
        message(CARTS[kind].name.." NEEDS THE AIRCRAFT STOPPED ON THE GROUND")
    end
end

local function update_carts()
    if (ground.power or ground.air) and not on_ground_and_stopped(CART_PULL_OFF_SPEED) then
        for kind,cart in pairs(CARTS) do
            if ground[kind] then ground[kind]=false;message(cart.name.." DISCONNECTED") end
        end
    end
    bus.ground_power=ground.power
end

local function publish()
    local powered=bus.powered()
    mainpower:set(powered and 1 or 0)
    battery_param:set(bus.battery and 1 or 0)
    apu_param:set(bus.apu)
    gen_param:set(bus.gen_online and 1 or 0)
    ground_power_param:set(ground.power and 1 or 0)
    ground_air_param:set(ground.air and 1 or 0)
    for name,p in pairs(displays) do
        local v=aligned and powered and DisplayBoot.operational() or DisplayBoot.evaluate(name,powered_time)
        p.state:set(v.state);p.on:set(v.state==DisplayBoot.OPERATIONAL and 1 or 0)
        p.stage:set(v.stage);p.progress:set(v.progress);p.fade:set(v.fade)
    end
    local e=alignment.evaluate((not aligned) and (powered_time or 0) or nil)
    align.pitch:set(e.pitch);align.roll:set(e.roll);align.hdg:set(e.hdg);align.adc:set(e.adc)
end

function post_initialize()
    local birth=LockOn_Options.init_conditions and LockOn_Options.init_conditions.birth_place
    local hot=birth=="GROUND_HOT" or birth=="AIR_HOT"
    bus.set_battery(hot)
    aligned=hot
    bus.update(0,rpm())
    -- A hot start's engines are already at idle; hold the bus up in case
    -- engine RPM is not reported on the first frames.
    hot_grace=hot and HOT_GRACE or 0
    if hot then bus.gen_online=true end
    powered_time=bus.powered() and 0 or nil
    alignment.seed()
    publish()
    report_engine_start()
end

function SetCommand(command,value)
    if command==Keys.PowerOnOff then
        bus.toggle_battery()
        message(bus.battery and "BATTERY ON" or "BATTERY OFF")
    elseif command==Keys.APUToggle then
        local before=bus.apu
        bus.toggle_apu()
        if bus.apu==PowerBus.APU_STARTING then message("APU START")
        elseif before~=PowerBus.APU_OFF then message("APU OFF")
        else message("APU START NEEDS BATTERY") end
    elseif command==Keys.GroundPowerToggle then
        toggle_cart("power")
        bus.ground_power=ground.power
    elseif command==Keys.GroundAirToggle then
        toggle_cart("air")
    end
end

function update()
    -- Switch commands change the bus between updates; compare against the
    -- state this update last saw, not the state after SetCommand.
    local was=powered_time~=nil
    update_carts()
    bus.update(update_time_step,rpm())
    if hot_grace>0 then hot_grace=hot_grace-update_time_step;bus.gen_online=true end
    local now=bus.powered()
    if now and not was then
        powered_time=0
        aligned=false
        alignment.seed()
    elseif now then
        powered_time=powered_time+update_time_step
    else
        powered_time=nil
        aligned=false
    end
    publish()
    report_engine_start()
end

need_to_be_closed=false
