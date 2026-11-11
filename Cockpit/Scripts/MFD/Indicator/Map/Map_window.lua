-- Map display window in map source units.
-- The MAP page is only shown on the CMDIs. CMDI_formats.lua draws it at `scale`
-- (the centre-sized layout shrunk to fit the side glass), so the page measures
-- its fill area as the measured side glass divided by that scale: after scaling
-- the chart and its aperture then cover the whole glass, not a centred sub-window.
local outlines=dofile(LockOn_Options.script_path.."Calibration/measured_outlines.lua")
local M={}
local function bounds(o)
    return {xmin=o.xmin,xmax=o.xmax,ymin=o.ymin,ymax=o.ymax}
end
-- side: "left", "right" or "centre" (unscaled, centre glass). Source-unit window.
function M.for_side(side)
    local o=outlines[side or "centre"] or outlines.centre
    local scale=1
    if o~=outlines.centre then
        scale=.98*math.min(o.width/outlines.centre.width,o.height/outlines.centre.height)
    end
    local outline={}
    for i,p in ipairs(o.outline) do outline[i]={p[1]/scale,p[2]/scale} end
    local b=bounds(o)
    local w={scale=scale,outline=outline,
        xmin=b.xmin/scale,xmax=b.xmax/scale,ymin=b.ymin/scale,ymax=b.ymax/scale}
    -- Chart camera and texture are centred on screen (0,0): use symmetric half extents.
    w.half_width=math.max(math.abs(w.xmin),math.abs(w.xmax))
    w.half_height=math.max(math.abs(w.ymin),math.abs(w.ymax))
    return w
end
-- Largest half extents over both CMDIs; one device drives both maps.
function M.cmdi()
    local l,r=M.for_side("left"),M.for_side("right")
    return {half_width=math.max(l.half_width,r.half_width),
        half_height=math.max(l.half_height,r.half_height)}
end
return M
