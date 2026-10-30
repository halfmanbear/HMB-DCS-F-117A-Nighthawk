CALIBRATION_KIND = "hud"
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(MILLYRADIANS)
local D = dofile(LockOn_Options.script_path.."Calibration/draw.lua")
local c = dofile(LockOn_Options.script_path.."Calibration/config.lua").hud
local add_combiner_mask = dofile(LockOn_Options.script_path.."HUD/Indicator/combiner_mask.lua")
CALIBRATION_GLASS_LEVEL = 8
CALIBRATION_GLASS_CLIPPED = add_combiner_mask(CALIBRATION_GLASS_LEVEL,c.mount)
local root = D.group(c.origin)
local function p(x,y) return {x*c.scale_x,y*c.scale_y} end
local function line(points,parent,material)
    local converted = {}
    for _,v in ipairs(points) do table.insert(converted,p(v[1],v[2])) end
    return D.line(converted,1.2,parent or root,material)
end
local function text(value,x,y,size,parent,params,controllers,formats)
    local v=p(x,y)
    return D.text(value,v[1],v[2],size or 3,parent or root,params,controllers,formats)
end
local deg = math.pi/180*1000
local w,h = c.half_width_deg*deg,c.half_height_deg*deg
-- Static aircraft-axis angular ruler. REF 0 is not yet a verified boresight.
line({{-w,0},{w,0}})
line({{0,-h},{0,h}})
for i=-math.floor(math.max(c.half_width_deg,c.half_height_deg)),math.floor(math.max(c.half_width_deg,c.half_height_deg)) do
    if i~=0 then
        local n=i*deg
        local tick=i%5==0 and 4 or 2
        if math.abs(n)<=w then
            line({{n,-tick},{n,tick}})
            if i%5==0 then text(string.format("%+d",i),n,-9) end
        end
        if math.abs(n)<=h then
            line({{-tick,n},{tick,n}})
            if i%5==0 then text(string.format("%+d",i),10,n) end
        end
    end
end
for _,bounds in ipairs({{math.min(5*deg,w),math.min(5*deg,h)},{w,h}}) do
    local x,y=bounds[1],bounds[2]
    -- Corner brackets keep the central field relatively clear.
    for _,sx in ipairs({-1,1}) do for _,sy in ipairs({-1,1}) do
        line({{sx*(x-8),sy*y},{sx*x,sy*y},{sx*x,sy*(y-8)}})
    end end
end
text("HUD CAL / DEG",0,h-10,3.5)
text("REF 0",0,10)
text(string.format("1 DEG / %.0f x %.0f DEG",2*c.half_width_deg,2*c.half_height_deg),0,-h+23,3)

-- Attitude reference: rotate the frame, then translate along its local Y.
-- Small-angle pitch projection; large pitch/roll is outside this test's scope.
local bank = D.group({0,0},root,{"ROLL_HUD"},{{"rotate_using_parameter",0,c.roll_gain}})
local horizon = D.group({0,0},bank,{"PITCH_HUD"},{{"move_up_down_using_parameter",0,c.pitch_gain*c.scale_y}})
line({{-8*deg,0},{-1*deg,0}},horizon,D.amber)
line({{1*deg,0},{8*deg,0}},horizon,D.amber)
text("ATT 0",0,-7,3,horizon)
for i,name in ipairs({"PITCH_HUD","ROLL_HUD"}) do
    local label=i==1 and "P" or "R"
    text("",0,-h+23-i*8,2.8,nil,{name},{{"text_using_parameter",0,0}},{label.." %+.3f RAD"})
end
