dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
local D = dofile(LockOn_Options.script_path.."Calibration/draw.lua")
local config = dofile(LockOn_Options.script_path.."Calibration/config.lua")
local geometry = dofile(LockOn_Options.script_path.."Calibration/measured_outlines.lua")
local c = config[CALIBRATION_KIND]
local g = geometry[CALIBRATION_KIND]
local root = D.group(c.offset)
local function p(x,y) return {x*c.scale_x,y*c.scale_y} end
local function line(points,material)
    local converted = {}
    for _,v in ipairs(points) do table.insert(converted,p(v[1],v[2])) end
    return D.line(converted,0.001,root,material)
end
local function text(value,x,y,size)
    local v=p(x,y)
    return D.text(value,v[1],v[2],size or 0.0022,root)
end
-- Evaluated Blender mesh silhouette, projected into this connector frame.
local outline = {}
for _,v in ipairs(g.outline) do table.insert(outline,v) end
table.insert(outline,g.outline[1])
line(outline,D.amber)
line({{-.020,-.020},{.020,-.020},{.020,.020},{-.020,.020},{-.020,-.020}})
text("40 x 40 mm",0,-.025)
-- Axes and 10 mm ticks (positive X is display right; positive Y is up).
line({{g.xmin+.003,0},{g.xmax-.003,0}})
line({{0,g.ymin+.003},{0,g.ymax-.003}})
for i=-8,8 do
    local x=i*.010
    if x>g.xmin+.004 and x<g.xmax-.004 then line({{x,-.0015},{x,.0015}}) end
end
for i=-7,7 do
    local y=i*.010
    if y>g.ymin+.004 and y<g.ymax-.004 then line({{-.0015,y},{.0015,y}}) end
end
text(string.upper(CALIBRATION_KIND).." CAL",0,g.ymax-.009,.0025)
text("UP +Y",0,g.ymax-.015)
text("+X",g.xmax-.008,.006)
text("10 mm TICKS",0,g.ymin+.010)
text(string.format("%.1f x %.1f mm",g.width*1000,g.height*1000),0,g.ymin+.005,.0019)
