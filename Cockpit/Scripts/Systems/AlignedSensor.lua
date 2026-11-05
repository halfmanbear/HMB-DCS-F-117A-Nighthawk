-- Display-side view of get_base_data() while the attitude, heading and air data
-- sources align after power-up (Systems/Electrical.lua publishes the errors).
-- Only display consumers use this; the EFM and weapons see true data.
local TWO_PI=2*math.pi
local function wrap(a) a=a%TWO_PI;if a<0 then a=a+TWO_PI end;return a end
return function(sensor,param)
    param=param or get_param_handle
    local pitch=param("F117_ALIGN_PITCH_ERR")
    local roll=param("F117_ALIGN_ROLL_ERR")
    local hdg=param("F117_ALIGN_HDG_ERR")
    local adc=param("F117_ADC_BLEND")
    local function blend() local b=adc:get();return b<0 and 0 or b>1 and 1 or b end
    -- Airspeeds from the EFM's air data. With wind set, DCS's own true airspeed is ground speed
    -- and its indicated airspeed reads high; without the EFM these fall back to DCS.
    local airValid=param("F117_AIR_DATA_VALID")
    local cas=param("F117_CAS_MPS")
    local tas=param("F117_TAS_MPS")
    local aligned={
        getPitch=function() return sensor.getPitch()+pitch:get() end,
        getRoll=function() return sensor.getRoll()+roll:get() end,
        -- getHeading is counter-clockwise; getMagneticHeading is clockwise.
        getHeading=function() return wrap(sensor.getHeading()-hdg:get()) end,
        getMagneticHeading=function() return wrap(sensor.getMagneticHeading()+hdg:get()) end,
        getBarometricAltitude=function() return sensor.getBarometricAltitude()*blend() end,
        getVerticalVelocity=function() return sensor.getVerticalVelocity()*blend() end,
        getIndicatedAirSpeed=function()
            if airValid:get()>.5 then return cas:get() end
            return sensor.getIndicatedAirSpeed()
        end,
        getTrueAirSpeed=function()
            if airValid:get()>.5 then return tas:get() end
            return sensor.getTrueAirSpeed()
        end,
    }
    return setmetatable(aligned,{__index=function(_,k) return sensor[k] end})
end
