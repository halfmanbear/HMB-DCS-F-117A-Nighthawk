dofile(LockOn_Options.script_path.."command_defs.lua")
dofile(LockOn_Options.script_path .. "devices.lua")
dev = GetSelf()
local update_time_step = 0.001 --update will be called 1000 times per second
make_default_activity(update_time_step)
local sensor_data = get_base_data()

-- Conversions

local RAD_TO_DEGREE  = 57.29577951308233


--hud indicator params
local CURR_IAS  = get_param_handle("CURR_IAS")        --Airspeed.
local MACH_A          = get_param_handle("MACH_A")
local MACH_B          = get_param_handle("MACH_B")        

local HUD_MACH = 0

local HUD_IAS = 0
local HUD_GS = 0

local OverSpeedBlink = 0
-- Direction related params

local PITCH_HUD  = get_param_handle("PITCH_HUD")

local ROLL_HUD  = get_param_handle("ROLL_HUD")

local HEADING_HUD = get_param_handle("HEADING_HUD")

local ALTITUDE_HUD = get_param_handle("ALTITUDE_HUD")
local headingMode = get_param_handle("headingMode")


local VELVEC_HUD_Y  = get_param_handle("VELVEC_HUD_Y")
local VELVEC_HUD_X  = get_param_handle("VELVEC_HUD_X")

local VV_LimitedLower = get_param_handle("VV_LimitedLower")
local VV_LimitedUpper = get_param_handle("VV_LimitedUpper")

local VVI_HUD   = get_param_handle("VVI_HUD")   -- fpm, rounded to nearest 10, unclamped (digital readout)
local VVI_SCALE = get_param_handle("VVI_SCALE")  -- fpm, clamped +1000/-2000 (pointer position)
local GS_HUD    = get_param_handle("GS_HUD")     -- ground speed in knots




-- System indications
local AT = get_param_handle("AUTOTHROTTLE_ONOFF")
AT:set(0)        -- 0 = off 1 = on
local AT_MODE = get_param_handle("AUTOTHROTTLE_MODE")
AT_MODE:set(0)        -- 0 = off, 0.5 = 12, 1 = 14

local Autothrottle_mode = 12

local ALT_HOLD = get_param_handle("ALT_HOLD")
local GPS_ALTITUDE_FEET = get_param_handle("GPS_ALTITUDE_FEET")

dev:listen_command(10064) -- Toggle autothrottle
dev:listen_command(10065) -- Toggle AoA 12/14

dev:listen_command(389) -- on Alt hold
dev:listen_command(408) -- off Alt hold




function post_initialize()

        -- F-117 has no modelled electrical system; power is always on at spawn.
        get_param_handle("mainpower"):set(1)

        local F117_Type = get_aircraft_type()
        get_param_handle("F117_TYPE"):set(3)

        -- currentPhase gates most HUD symbology (requires range 6.9–8.9).
        -- 8 = normal flight; F-117 would update this dynamically but F-117 stays in normal flight.
        get_param_handle("currentPhase"):set(8)

end

function SetCommand(command,value)        
   -- Auto throttle                        
        if command == 10064 then
                if AT:get() == 1 then
                        AT:set(0)
                else
                        AT:set(1)
                end
        elseif command == 10065 then
                if Autothrottle_mode == 12  then
                        Autothrottle_mode = 14
                else
                        Autothrottle_mode = 12
                end
        end


        if command == 389 then
                ALT_HOLD:set(1)
        end        

        if command == 408 then
                ALT_HOLD:set(0)
        end
end        

function update()

        ROLL_HUD:set(sensor_data.getRoll())

        PITCH_HUD:set(sensor_data.getPitch())


 local VelVec_x = math.rad(sensor_data.getAngleOfSlide())
 local VelVec_y = -sensor_data.getAngleOfAttack() 

        VELVEC_HUD_Y:set(VelVec_y * (1.08))

        if VelVec_x > -0.247 and VelVec_x < 0.247 then
                VELVEC_HUD_X:set(VelVec_x)        
        end

        if VELVEC_HUD_Y:get() < -0.26 then
                VV_LimitedLower:set(1)
        elseif VELVEC_HUD_Y:get() > 0.125 then
                VV_LimitedUpper:set(1)
        else 
                VV_LimitedLower:set(0)
                VV_LimitedUpper:set(0)
        end


        if headingMode:get() == 1 then
                HEADING_HUD:set(360 - (sensor_data.getHeading() * RAD_TO_DEGREE))
        else        
                HEADING_HUD:set((sensor_data.getMagneticHeading() * RAD_TO_DEGREE))
        end

	if get_param_handle("masterMode"):get() > 1 then
		get_param_handle("altitudeDeclutt"):set(1)
	else
		get_param_handle("altitudeDeclutt"):set(0)
	end

        if get_param_handle("ALTITUDE_MODE"):get() == 1 then        -- 1 = barometric, 2 = Radar
                ALTITUDE_HUD:set(sensor_data.getBarometricAltitude() * 3.2808399)
        elseif get_param_handle("ALTITUDE_MODE"):get() == 2 then
                local Hud_Ralt = sensor_data.getRadarAltitude() * 3.2808399

                if (Hud_Ralt > 5249.4) and (Hud_Ralt < 5249.6) then        
                        ALTITUDE_HUD:set(GPS_ALTITUDE_FEET:get() - get_param_handle("TERRAIN_ALT"):get()) 
                        get_param_handle("RadarAltAvail"):set(0)
                else

                        ALTITUDE_HUD:set(Hud_Ralt)
                        get_param_handle("RadarAltAvail"):set(1)
                end
        end


-- Speeds =================================================================================================================================
        HUD_IAS = sensor_data.getIndicatedAirSpeed() * 1.94384449                 -- m/s to kts
        local self_vel_l,self_vel_v,self_vel_h = sensor_data.getSelfAirspeed()                -- Prereq for ground speed in kts
        HUD_GS = math.sqrt(self_vel_h^2 + self_vel_l^2)*1.94384449
-- Below 50 kts use ground speed reading instead
        if HUD_IAS < 50 then
                CURR_IAS:set(HUD_GS)
        else
                CURR_IAS:set(HUD_IAS)
        end



        HUD_MACH = sensor_data.getMachNumber()

        if HUD_MACH < 0.995 then
                HUD_MACH = HUD_MACH *100
        end

        MACH_A:set(sensor_data.getMachNumber())

        MACH_B:set(HUD_MACH)

        GS_HUD:set(HUD_GS)

        local vvi_fpm = sensor_data.getVerticalVelocity() * 196.850394  -- m/s to fpm
        VVI_HUD:set(math.floor(vvi_fpm / 10) * 10)                      -- round to nearest 10 fpm
        VVI_SCALE:set(math.max(-2000, math.min(1000, vvi_fpm)))          -- clamped for pointer

-- Takeoff phase, tells you when to rotate        


        if (get_param_handle("CURRENT_PHASE_TGR"):get() == 1) or (get_param_handle("CURRENT_PHASE_ROT"):get() == 1) or (get_param_handle("CURRENT_PHASE_STATIONARY"):get() == 1) or (get_param_handle("CURRENT_PHASE_PARKED"):get() == 1) or (get_param_handle("CURRENT_PHASE_TAXI"):get() == 1) or (get_param_handle("CURRENT_PHASE_TD"):get() == 1) or (get_param_handle("CURRENT_PHASE_LR"):get() == 1) then        
                local TakeOffSpeed = CURR_IAS:get()
                local TakeOffOverspeed = 0

                if TakeOffSpeed > 150 then                -- limit movement of rotation que
                        TakeOffSpeed = 150

                        TakeOffOverspeed = 1                

                elseif TakeOffSpeed < 150 then        
                        TakeOffOverspeed = 0
                end

                if TakeOffOverspeed == 1 then
                        if OverSpeedBlink < 1 then
                                OverSpeedBlink = OverSpeedBlink + update_time_step

                        else
                                OverSpeedBlink = 0
                        end


                end

                get_param_handle("TO_SPEED"):set(TakeOffSpeed)

                if get_param_handle("CURRENT_PHASE_TGR"):get() == 1 then
                        get_param_handle("TO_OVERSPEED"):set(OverSpeedBlink)
                else
                        get_param_handle("TO_OVERSPEED"):set(0)
                end
        else                
                get_param_handle("TO_OVERSPEED"):set(0)

        end

-- Auto Throttle ==========================================================================================================================
        if (AT:get() == 1) and ((get_param_handle("CURRENT_PHASE_LO"):get() > 0.0) or (get_param_handle("CURRENT_PHASE_PAL"):get() > 0.0)) then
                if Autothrottle_mode == 12 then
                        AT_MODE:set(0.5)
                elseif Autothrottle_mode == 14 then
                        AT_MODE:set(1)
                end
        elseif (get_param_handle("CURRENT_PHASE_LO"):get() < 1.0) or (get_param_handle("CURRENT_PHASE_PAL"):get() < 1.0) or (AT:get() < 0.5 ) then
                AT_MODE:set(0)
        end
end

need_to_be_closed = false