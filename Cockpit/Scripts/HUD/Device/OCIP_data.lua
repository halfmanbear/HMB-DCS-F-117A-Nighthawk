-- OCIP-specific readouts. Does not alter the existing HUD/VSD/HSD parameters.
-- Sensor angles are radians, speeds m/s, altitude metres, vertical speed m/s.
return function(sensor)
    local handles = {}
    local function set(name,value)
        if not handles[name] then handles[name]=get_param_handle("F117_OCIP_"..name) end
        handles[name]:set(value)
    end
    local previous_ias,approach=nil,false
    local function finite(v) return type(v)=="number" and v==v and math.abs(v)<1e12 end
    local ladder={}
    for degrees=-85,85,5 do
        local tag=degrees<0 and "N"..(-degrees) or "P"..degrees
        ladder[#ladder+1]={angle=math.rad(degrees),tag=tag}
    end
    return function(dt)
        local ias=sensor.getIndicatedAirSpeed()*1.94384449
        local rate=previous_ias and (ias-previous_ias)/dt or 0
        local step=math.abs(rate)>300 and 5 or 1
        set("CAS",math.floor(ias/step+.5)*step)
        -- Manual: approach bracket enters below 200 KCAS and leaves above 230.
        if ias<200 then approach=true elseif ias>230 then approach=false end
        set("APPROACH",approach and 1 or 0)
        previous_ias=ias
        local vvi=sensor.getVerticalVelocity()*196.850394
        step=math.abs(vvi)>2400 and 100 or 10
        set("ALT",math.floor(sensor.getBarometricAltitude()*3.2808399/step+.5)*step)
        set("VVI",math.floor(vvi/10+.5)*10)
        set("HEADING",(sensor.getMagneticHeading()*180/math.pi)%360)
        -- Native text_using_parameter expects a numeric printf argument.
        -- Keep this numeric even before the first indicator update.
        set("MACH",sensor.getMachNumber())
        set("AOA",sensor.getAngleOfAttack())
        local pitch,roll=sensor.getPitch(),sensor.getRoll()
        for _,bar in ipairs(ladder) do
            local delta=bar.angle-pitch
            local visible=math.abs(delta)<math.rad(80)
            set("LADDER_"..bar.tag,visible and math.tan(delta) or 0)
            set("LADDER_VALID_"..bar.tag,visible and 1 or 0)
        end
        -- DCS local world axes: X north, Y up, Z east. getHeading() is
        -- counter-clockwise; convert to clockwise geographic heading.
        -- Use velocity over the ground so wind/drift affects the marker.
        local vn,vu,ve
        if sensor.getSelfVelocity then vn,vu,ve=sensor.getSelfVelocity() end
        local valid=finite(vn) and finite(vu) and finite(ve)
        local x,y=0,0
        if valid then
            local h=-sensor.getHeading()
            local ch,sh,cp,sp=math.cos(h),math.sin(h),math.cos(pitch),math.sin(pitch)
            local cr,sr=math.cos(roll),math.sin(roll)
            local along=vn*ch+ve*sh
            local forward=along*cp+vu*sp
            local level_right=-vn*sh+ve*ch
            local level_up=vu*cp-along*sp
            local right=level_right*cr-level_up*sr
            local up=level_up*cr+level_right*sr
            valid=forward>1 and vn*vn+vu*vu+ve*ve>25
            if valid then x=right/forward;y=up/forward end
        end
        set("VV_X",x)
        set("VV_Y",y)
        set("VV_VALID",valid and 1 or 0)
        set("INS_VALID",valid and 1 or 0)

    end
end
