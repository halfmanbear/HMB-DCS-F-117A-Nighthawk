-- Mission flight plan and active waypoint for the MAP, HSD and VSD.
-- The route comes from the cockpit Lua function get_mission_route(); its point
-- layout is checked defensively and logged once so it can be confirmed live.
-- World metres: x north, z east. Bearings and courses are degrees clockwise.
local M={}
local NM=1852
local KNOTS=1.94384449
local CAPTURE_NM=1   -- auto-sequence radius: a mod choice, not a verified OCIP value
local RETRY_UPDATES=100
local MAX_ATTEMPTS=10
-- MARK points (TO 1F-117A-1A): destination points 94-98, assigned in order; DP 99 holds the sensor-update bias.
local MARK_FIRST,MARK_TOTAL=94,5
local logger=log
if not logger then
    local ok,value=pcall(require,"log")
    if ok then logger=value end
end
local function report(message)
    if logger and logger.write then logger.write("F117_NAV",logger.INFO,message) end
end
local function finite(v)return type(v)=="number" and v==v and math.abs(v)<1e12 end
local function default_source()
    if type(get_mission_route)=="function" then return get_mission_route() end
end
-- Accepts a point list directly, or wrapped in route/points; zero-based lists too.
local function point_list(t)
    if type(t)~="table" then return {} end
    if type(t.points)=="table" then t=t.points elseif type(t.route)=="table" then return point_list(t.route) end
    local list={}
    if t[0]~=nil then list[1]=t[0] end
    for _,p in ipairs(t) do list[#list+1]=p end
    return list
end
local function position(p)
    local q=p.world_point or p.point or p.position or p.pos or p
    if type(q)~="table" then return end
    local north,east=q.x,q.z
    if not finite(east) then east=q.y end -- 2D map point: y is east
    if finite(north) and finite(east) then return north,east end
end
local function kind(p)
    local name=tostring(p.type or p.action or p.point_action or ""):lower()
    if name:find("takeoff") or name:find("take off") then return "takeoff" end
    return "navigation"
end
local function fields(p)
    local names={}
    for key in pairs(type(p)=="table" and p or {}) do names[#names+1]=tostring(key) end
    table.sort(names)
    return table.concat(names,",")
end
function M.parse(raw)
    local route={}
    for i,p in ipairs(point_list(raw)) do
        if type(p)~="table" then break end
        local north,east=position(p)
        if not north then break end -- never bridge an unusable record
        local number=finite(p.this_point_num) and math.floor(p.this_point_num) or i-1
        local q=p.world_point or p.point or p.position or p.pos
        local elev=p.alt or p.altitude or p.elev or (type(q)=="table" and q.z~=nil and q.y)
        route[#route+1]={x=north,z=east,elev=finite(elev) and elev or nil,kind=kind(p),number=number,
            label=string.format("%02d",number%100)}
    end
    return route
end
function M.new(sensor,source)
    sensor=sensor or get_base_data()
    source=source or default_source
    local route={}
    local marks={}          -- stored MARK points, in the INS frame: {x,z,elev,number,label,kind="mark"}
    local ground_marks=0    -- MARK activations used up on the ground after power-up
    local bias_dp={n=0,e=0,alt=0} -- DP 99
    local active,attempts,countdown,armed=1,0,0,false
    -- Manual destination selection activates a fixed direct-to course from
    -- ownship, rather than reusing the destination's original inbound leg.
    local manual_course,manual_pending=nil,false
    local handles={}
    local function set(name,value)
        if not handles[name] then handles[name]=get_param_handle("F117_NAV_"..name) end
        handles[name]:set(value)
    end
    local heading_card=get_param_handle("HEADING_HUD")
    local function first_leg()
        for i,p in ipairs(route) do if p.kind~="takeoff" then return i end end
        return 1
    end
    local function load()
        attempts=attempts+1
        local ok,raw=pcall(source)
        local parsed=ok and M.parse(raw) or {}
        if #parsed>0 then
            route=parsed;active=first_leg();armed=false
            manual_course,manual_pending=nil,false
            report(string.format("route: %d points, fields: %s",#parsed,fields(point_list(raw)[1])))
        elseif attempts==MAX_ATTEMPTS then
            report(not ok and "route unavailable: "..tostring(raw)
                or type(raw)=="table" and "route unusable, fields: "..fields(point_list(raw)[1] or raw)
                or "route unavailable")
        end
    end
    local function dashes()
        set("VALID",0);set("DEST",-1);set("RANGE_NM",0);set("BEARING",0)
        set("COURSE",0);set("REL_COURSE",0)
        set("D_TEXT","D  --");set("TTG_TEXT","TTG --:--");set("RNG_TEXT","RNG ---.-");set("CRS_TEXT","CRS ---")
    end
    -- The TO point sequence is the mission route followed by any stored marks.
    local function total() return #route+#marks end
    local function point_at(i) return route[i] or marks[i-#route] end
    local function remaining() return math.max(0,MARK_TOTAL-#marks-ground_marks) end
    local function update()
        set("MARK_REMAINING",remaining())
        if #route==0 and attempts<MAX_ATTEMPTS then
            countdown=countdown-1
            if countdown<=0 then countdown=RETRY_UPDATES;load() end
        end
        local x,z
        if sensor.getSelfCoordinates then local _;x,_,z=sensor.getSelfCoordinates() end
        local heading=sensor.getHeading and sensor.getHeading()
        local point=point_at(active)
        if not (point and finite(x) and finite(z) and finite(heading)) then dashes();return end
        heading=-heading -- clockwise true heading, radians
        local function bearing(ax,az,bx,bz)return (math.atan2 or math.atan)(bz-az,bx-ax) end
        local range=math.sqrt((point.x-x)^2+(point.z-z)^2)
        -- Capture only after approaching from outside the radius, so stepping
        -- back to a point already inside it does not sequence straight past it.
        if range>=CAPTURE_NM*NM then armed=true
        elseif armed and active<#route then
            active=active+1;armed=false;point=point_at(active)
            manual_course,manual_pending=nil,false -- resume the next planned leg
            range=math.sqrt((point.x-x)^2+(point.z-z)^2)
        end
        local direct=bearing(x,z,point.x,point.z)
        local previous=route[active-1]
        if active>#route then previous=nil end -- a mark is steered to directly
        local course=previous and previous.kind~="takeoff" and bearing(previous.x,previous.z,point.x,point.z) or direct
        if manual_pending then
            -- At the point itself the bearing is undefined: retain the planned
            -- course within one metre instead of latching atan2(0,0).
            manual_course=range>=1 and direct or course
            manual_pending=false
        end
        if manual_course~=nil then course=manual_course end
        local vn,ve
        if sensor.getSelfVelocity then local _;vn,_,ve=sensor.getSelfVelocity() end
        local speed=finite(vn) and finite(ve) and math.sqrt(vn*vn+ve*ve) or 0
        -- Text follows the HSD card reference (true or magnetic, per HEADING_HUD).
        local card=heading_card:get()
        local offset=finite(card) and (math.deg(heading)-card) or 0
        local function display(angle)return math.floor((math.deg(angle)-offset)%360+.5)%360 end
        local rel=(course-heading+math.pi)%(2*math.pi)-math.pi
        set("VALID",1);set("DEST",point.number);set("RANGE_NM",range/NM)
        set("DEST_X",point.x);set("DEST_Z",point.z)
        set("DEST_Y",point.elev or 0)
        set("BEARING",math.deg(direct)%360);set("COURSE",math.deg(course)%360);set("REL_COURSE",rel)
        set("D_TEXT","D  "..point.label)
        if speed*KNOTS>=50 then
            local seconds=math.min(5999,math.floor(range/speed+.5))
            set("TTG_TEXT",string.format("TTG %02d:%02d",math.floor(seconds/60),seconds%60))
        else set("TTG_TEXT","TTG --:--") end
        set("RNG_TEXT",string.format("RNG %5.1f",math.min(999.9,range/NM)))
        set("CRS_TEXT",string.format("CRS %03d",display(course)))
    end
    local function step(delta)
        if total()==0 then return end
        local selected=math.max(1,math.min(total(),active+delta))
        if selected==active then return end -- a clamped press is not a new leg
        active=selected;armed=false
        manual_course,manual_pending=nil,true
        update()
    end
    -- Store a mark (INS-frame coordinates). Returns the destination number, or nil when none are left.
    local function add_mark(x,z,elev)
        if remaining()==0 or not (finite(x) and finite(z)) then return nil end
        local number=MARK_FIRST+#marks
        marks[#marks+1]={x=x,z=z,elev=finite(elev) and elev or nil,kind="mark",number=number,
            label=string.format("%02d",number%100)}
        set("MARK_REMAINING",remaining())
        return number
    end
    -- On the ground after power-up each MARK activation uses one of the five points.
    local function consume_ground_mark()
        if remaining()>0 then ground_marks=ground_marks+1;set("MARK_REMAINING",remaining()) end
    end
    -- Destination point by number: route points, marks 94-98 and the bias point 99.
    local function dp(number)
        for _,p in ipairs(route) do if p.number==number then return p end end
        if number==99 then return {x=bias_dp.n,z=bias_dp.e,elev=bias_dp.alt,kind="bias",number=99,label="99"} end
        return marks[number-MARK_FIRST+1]
    end
    local function set_bias(n,e,alt) bias_dp.n,bias_dp.e,bias_dp.alt=n,e,alt end
    local function set_command(command,value)
        if not nav_commands then return false end
        if command==nav_commands.WP_NEXT then if value and value>0 then step(1) end return true end
        if command==nav_commands.WP_PREV then if value and value>0 then step(-1) end return true end
        -- Stock commands are only bound on key down, so every call is a press.
        if command==native_commands.WP_NEXT then step(1) return true end
        if command==native_commands.WP_PREV then step(-1) return true end
        return false
    end
    local function initialize()
        route,active,attempts,countdown,armed={},1,0,0,false
        manual_course,manual_pending=nil,false
        marks,ground_marks,bias_dp={},0,{n=0,e=0,alt=0}
        dashes()
        set("MARK_REMAINING",remaining())
    end
    return {initialize=initialize,update=update,set_command=set_command,
        route=function()return route end,active=function()return active end,
        active_point=function()return point_at(active) end,
        marks=function()return marks end,remaining=remaining,add_mark=add_mark,
        consume_ground_mark=consume_ground_mark,dp=dp,set_bias=set_bias,
        bias=function()return bias_dp.n,bias_dp.e,bias_dp.alt end}
end
return M
