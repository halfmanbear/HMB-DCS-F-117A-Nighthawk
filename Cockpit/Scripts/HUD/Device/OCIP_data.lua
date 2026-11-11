-- OCIP-specific readouts. Does not alter the existing HUD/VSD/HSD parameters.
-- Sensor angles are radians, speeds m/s, altitude metres, vertical speed m/s.
return function(sensor,options)
    local handles = {}
    local function set(name,value)
        if not handles[name] then handles[name]=get_param_handle("F117_OCIP_"..name) end
        handles[name]:set(value)
    end
    -- Average ground velocity in world space, then project with current attitude.
    -- Filtering screen coordinates would lag aircraft/head alignment in a turn.
    options=options or {}
    local filter_time=options.vv_filter_time or .25 -- seconds; 63% response in .25 s
    local filtered_n,filtered_u,filtered_e
    local previous_ias,approach=nil,false
    local function finite(v) return type(v)=="number" and v==v and math.abs(v)<1e12 end
    local inputs={}
    local function get(name)
        if not inputs[name] then inputs[name]=get_param_handle(name) end
        local v=inputs[name]:get()
        return finite(v) and v or 0
    end
    -- HUD/IRADS cursor (TO 1F-117A-1 4-5): when the look angle is outside the
    -- 20-degree total field of view its centre stays on the boundary. A fitted
    -- layout (layout_profile.lua) additionally keeps it on the drawn area.
    local tfov=math.tan(math.rad(options.tfov_half_deg or 10))
    local area
    if options.layout then
        local l=options.layout
        local w,h=math.rad(l.half_width_deg)*1000,math.rad(l.half_height_deg)*1000
        area={left=(l.origin_mrad[1]-w)/1000,right=(l.origin_mrad[1]+w)/1000,
              bottom=(l.origin_mrad[2]-h)/1000,top=(l.origin_mrad[2]+h)/1000}
    end
    -- World direction (north, up, east) to the aircraft frame (forward, right, up).
    -- getHeading() is counter-clockwise, hence the sign change.
    local function body(n,u,e,heading,pitch,roll)
        local h=-heading
        local ch,sh,cp,sp=math.cos(h),math.sin(h),math.cos(pitch),math.sin(pitch)
        local cr,sr=math.cos(roll),math.sin(roll)
        local along=n*ch+e*sh
        local level_right=-n*sh+e*ch
        local level_up=u*cp-along*sp
        return along*cp+u*sp,level_right*cr-level_up*sr,level_up*cr+level_right*sr
    end
    -- Optical-plane coordinates (right/forward, up/forward), held on the boundary.
    local function project(n,u,e,heading,pitch,roll)
        local f,r,up=body(n,u,e,heading,pitch,roll)
        local lateral=math.sqrt(r*r+up*up)
        if not (finite(f) and finite(lateral)) or f*f+lateral*lateral<1e-12 then return nil end
        local x,y
        if f>0 and lateral<=tfov*f then x,y=r/f,up/f
        elseif lateral>1e-9 then x,y=tfov*r/lateral,tfov*up/lateral
        else x,y=0,-tfov end -- directly aft: no defined bearing, hold at the bottom
        if area then
            local scale=1
            if x>area.right then scale=math.min(scale,area.right/x) end
            if x<area.left then scale=math.min(scale,area.left/x) end
            if y>area.top then scale=math.min(scale,area.top/y) end
            if y<area.bottom then scale=math.min(scale,area.bottom/y) end
            x,y=x*scale,y*scale
        end
        return x,y
    end
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
        set("TAS",math.floor(sensor.getTrueAirSpeed()*1.94384449+.5)) -- knots, HSD speed block
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
        valid=valid and vn*vn+vu*vu+ve*ve>25
        if valid then
            if not filtered_n or filter_time<=0 or (finite(dt) and dt>1) then
                filtered_n,filtered_u,filtered_e=vn,vu,ve
            else
                local elapsed=finite(dt) and math.max(0,dt) or 0
                local weight=1-math.exp(-elapsed/filter_time)
                filtered_n=filtered_n+(vn-filtered_n)*weight
                filtered_u=filtered_u+(vu-filtered_u)*weight
                filtered_e=filtered_e+(ve-filtered_e)*weight
            end
            vn,vu,ve=filtered_n,filtered_u,filtered_e
            local forward,right,up=body(vn,vu,ve,sensor.getHeading(),pitch,roll)
            valid=forward>1 and vn*vn+vu*vu+ve*ve>25
            if valid then x=right/forward;y=up/forward end
        end
        if not valid then
            filtered_n,filtered_u,filtered_e=nil,nil,nil
        end
        set("VV_X",x)
        set("VV_Y",y)
        set("VV_VALID",valid and 1 or 0)
        set("INS_VALID",valid and 1 or 0)

        -- IRADS: the lock point (EFM world metres) gets the box; the cursor
        -- follows the sensor's rendered line of sight, or the lock when locked.
        local heading=sensor.getHeading()
        local powered=get("F117_IRADS_POWER")>.5
        local lx,ly
        if powered and get("F117_IRADS_LOCK_VALID")>.5 and sensor.getSelfCoordinates then
            local ox,oy,oz=sensor.getSelfCoordinates()
            if finite(ox) and finite(oy) and finite(oz) then
                lx,ly=project(get("F117_IRADS_LOCK_X")-ox,get("F117_IRADS_LOCK_Y")-oy,
                    get("F117_IRADS_LOCK_Z")-oz,heading,pitch,roll)
            end
        end
        set("IRADS_LOCK_VALID",lx and 1 or 0)
        set("IRADS_LOCK_AZ",lx or 0)
        set("IRADS_LOCK_EL",ly or 0)
        local cx,cy=lx,ly
        if not cx and powered and get("F117_IRADS_LOS_VALID")>.5 then
            cx,cy=project(get("F117_IRADS_LOS_X"),get("F117_IRADS_LOS_Y"),get("F117_IRADS_LOS_Z"),heading,pitch,roll)
        end
        set("IRADS_VALID",cx and 1 or 0)
        set("IRADS_AZ",cx or 0)
        set("IRADS_EL",cy or 0)
    end
end
