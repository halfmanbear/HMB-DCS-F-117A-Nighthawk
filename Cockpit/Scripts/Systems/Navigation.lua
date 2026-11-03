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
        route[#route+1]={x=north,z=east,kind=kind(p),number=number,
            label=string.format("%02d",number%100)}
    end
    return route
end
function M.new(sensor,source)
    sensor=sensor or get_base_data()
    source=source or default_source
    local route={}
    local active,attempts,countdown,armed=1,0,0,false
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
    local function update()
        if #route==0 and attempts<MAX_ATTEMPTS then
            countdown=countdown-1
            if countdown<=0 then countdown=RETRY_UPDATES;load() end
        end
        local x,z
        if sensor.getSelfCoordinates then local _;x,_,z=sensor.getSelfCoordinates() end
        local heading=sensor.getHeading and sensor.getHeading()
        local point=route[active]
        if not (point and finite(x) and finite(z) and finite(heading)) then dashes();return end
        heading=-heading -- clockwise true heading, radians
        local function bearing(ax,az,bx,bz)return (math.atan2 or math.atan)(bz-az,bx-ax) end
        local range=math.sqrt((point.x-x)^2+(point.z-z)^2)
        -- Capture only after approaching from outside the radius, so stepping
        -- back to a point already inside it does not sequence straight past it.
        if range>=CAPTURE_NM*NM then armed=true
        elseif armed and active<#route then
            active=active+1;armed=false;point=route[active]
            range=math.sqrt((point.x-x)^2+(point.z-z)^2)
        end
        local direct=bearing(x,z,point.x,point.z)
        local previous=route[active-1]
        local course=previous and previous.kind~="takeoff" and bearing(previous.x,previous.z,point.x,point.z) or direct
        local vn,ve
        if sensor.getSelfVelocity then local _;vn,_,ve=sensor.getSelfVelocity() end
        local speed=finite(vn) and finite(ve) and math.sqrt(vn*vn+ve*ve) or 0
        -- Text follows the HSD card reference (true or magnetic, per HEADING_HUD).
        local card=heading_card:get()
        local offset=finite(card) and (math.deg(heading)-card) or 0
        local function display(angle)return math.floor((math.deg(angle)-offset)%360+.5)%360 end
        local rel=(course-heading+math.pi)%(2*math.pi)-math.pi
        set("VALID",1);set("DEST",point.number);set("RANGE_NM",range/NM)
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
        if #route==0 then return end
        active=math.max(1,math.min(#route,active+delta));armed=false;update()
    end
    local function set_command(command,value)
        if not nav_commands then return false end
        if command==nav_commands.WP_NEXT then if value and value>0 then step(1) end return true end
        if command==nav_commands.WP_PREV then if value and value>0 then step(-1) end return true end
        return false
    end
    local function initialize()
        route,active,attempts,countdown,armed={},1,0,0,false
        dashes()
    end
    return {initialize=initialize,update=update,set_command=set_command,
        route=function()return route end,active=function()return active end}
end
return M
