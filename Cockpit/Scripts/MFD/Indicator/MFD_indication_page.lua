-- Optional presentation settings for the left CMDI EO repeater.
local options=F117_IRADS_OVERLAY_OPTIONS or {}
local finish_native_brightness=(options.repeater or F117_IRADS_REGISTERED) and function()end or dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_IRADS_SOURCE")
-- IRADS sensor display symbology: TO 1F-117A-1 Figure 4-17, laid out from the
-- recorded sensor display frames in docs/reference/CockpitImages/IRADS.
-- The display is a text grid of 30 columns by 15 rows. Column c starts at
-- x=-.07548+.0050949*c and row r is centred on y=.06683-.00936*r (metres).
-- Row 0 (ALT/range/time) and row 14 (latitude/longitude) sit on black bands
-- outside the picture. The reticle is centred on the sensor boresight (0,0).
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local ROOT=CreateElement "ceSimple"
ROOT.name=options.root_name or "F117_IRADS_SOURCE"
ROOT.parent_element=options.parent
ROOT.element_params={"F117_ON_SD","MFD_OVERLAY","F117_IRADS_POWER"}
ROOT.controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,.9,1.1},{"parameter_in_range",2,.9,1.1}}
ROOT.h_clip_relation=h_clip_relations.COMPARE
ROOT.level=options.level or MFD_LEVEL
Add(ROOT)

local scale=options.scale or 1
local function place(e)
    e.name=e.name or create_guid_string()
    if options.repeater then e.z_enabled=true end
    e.parent_element=ROOT.name
    e.h_clip_relation=h_clip_relations.COMPARE
    e.level=options.level or MFD_LEVEL
    e.collimated=false
end
local function props(e,params,controllers)
    place(e)
    e.additive_alpha=true
    e.blend_mode=blend_mode.IBM_REGULAR_ADDITIVE_ALPHA
    -- Copy shared lock/mode tables before adding per-element luminance control.
    local p,c={},{}
    for i,v in ipairs(params or {}) do p[i]=v end
    for i,v in ipairs(controllers or {}) do c[i]=v end
    p[#p+1]=options.brightness_parameter or "F117_IRADS_DRAW_BRIGHTNESS"
    c[#c+1]={"opacity_using_parameter",#p-1}
    e.element_params=p
    e.controllers=c
    Add(e)
    return e
end
local function line(points,params,controllers)
    local e=strokes.line(points,scale,.8)
    e.material=MFD_WHITE
    return props(e,params,controllers)
end
local function quad(x0,y0,x1,y1)
    local e=CreateElement "ceMeshPoly"
    e.primitivetype="triangles"
    e.vertices={{x0*scale,y0*scale},{x1*scale,y0*scale},{x1*scale,y1*scale},{x0*scale,y1*scale}}
    e.indices={0,1,2,0,2,3}
    return e
end
local function fill(x0,y0,x1,y1,material,params,controllers)
    local e=quad(x0,y0,x1,y1)
    e.material=material or MFD_WHITE
    return props(e,params,controllers)
end
-- One character cell: 4.7 mm high, 5.1 mm pitch.
local SD={.00467,.00377,.00132}
local function text(value,x,y,size,align,params,controllers,formats)
    local e=CreateElement "ceStringSLine"
    e.init_pos={x*scale,y*scale}
    e.value=value
    e.material=MFD_FONT
    size=size or SD
    e.stringdefs={size[1]*scale,size[2]*scale,size[3]*scale,0}
    e.alignment=align or "LeftCenter"
    e.formats=formats
    strokes.text(e)
    return props(e,params,controllers)
end
local locked={"F117_IRADS_LOCK_VALID"}
local yes={{"parameter_in_range",0,.9,1.1}}
local no={{"parameter_in_range",0,-.1,.1}}

-- Opaque black bands behind rows 0 and 14, outside the picture. They reach the
-- glass edge and ignore brightness, so the picture never shows through them.
local BLACK=MakeMaterial(nil,{0,0,0,255})
for side,band in pairs({TOP={.06269,.0760},BOTTOM={-.05978,-.0760}}) do
    local e=quad(-.0890,band[1],.0890,band[2])
    e.name=ROOT.name.."_BAND_"..side
    e.material=BLACK
    place(e)
    e.additive_alpha=false
    e.blend_mode=blend_mode.IBM_REGULAR
    Add(e)
end

-- Row 0: altitude, range (LR laser, ER estimated, R to destination) and
-- TTI after release or TTG. Text comes from Systems/IRADS_Readouts.lua.
text("",-.07548,.06683,SD,"LeftCenter",{"F117_IRADS_ALT_TEXT"},{{"text_using_parameter",0,0}},{"%s"})
text("",-.01944,.06683,SD,"LeftCenter",{"F117_IRADS_RANGE_TEXT"},{{"text_using_parameter",0,0}},{"%s"})
text("",.03151,.06683,SD,"LeftCenter",{"F117_IRADS_TIME_TEXT"},{{"text_using_parameter",0,0}},{"%s"})

-- Rows 2 and 3: field of view, release ready, IRADS mode.
text("W",-.07039,.04811,SD,"LeftCenter",{"IRADS_ZOOM"},{{"parameter_in_range",0,.9,1.1}})
text("N",-.07039,.04811,SD,"LeftCenter",{"IRADS_ZOOM"},{{"parameter_in_range",0,2.9,3.1}})
text("RDY",-.0602,.04811,SD,"LeftCenter",{"F117_RELEASE_STATUS"},{{"parameter_in_range",0,8.9,9.1}})
text("CUED",-.07039,.03875,SD,"LeftCenter",locked,yes)
text("SRCH",-.07039,.03875,SD,"LeftCenter",locked,no)

-- Row 4, column 14: laser mode over the reticle (A armed, F firing, X not firing).
text("",-.00415,.02939,SD,"LeftCenter",{"F117_IRADS_LASER_TEXT"},{{"text_using_parameter",0,0}},{"%s"})

-- Reticle: four arms with an open centre in every mode, and the track gate
-- on the designated point while locked.
line({{-.0201,0},{-.0050,0}})
line({{.0050,0},{.0201,0}})
line({{0,.0058},{0,.0226}})
line({{0,-.0058},{0,-.0226}})
line({{-.0017,-.0017},{-.0017,.0017},{.0017,.0017},{.0017,-.0017},{-.0017,-.0017}},locked,yes)

-- Left funnel with scale marks on rows 6 to 10.
line({{-.0702,.03339},{-.0702,.03106},{-.06215,.02114},{-.06215,-.03791},{-.05812,-.0503}})
line({{-.03711,.03339},{-.03711,.03106},{-.04554,.02114},{-.04554,-.03791},{-.04931,-.0503}})
for _,y in ipairs({.01067,.00131,-.00805,-.01741,-.02677}) do
    line({{-.0634,y},{-.06215,y}})
end

-- Row 8: L (level) and G (gain) scales, five marks each, bars filling upward.
text("LG",-.07548,-.00805,SD)
for _,y in ipairs({-.014,-.01866,-.02333,-.02799,-.03266}) do
    line({{-.07674,y},{-.07561,y}})
    line({{-.07145,y},{-.07045,y}})
end
local BAR_BOTTOM,BAR_TOP,STEPS=-.03266,-.014,8
for i=1,STEPS do
    local y0=BAR_BOTTOM+(BAR_TOP-BAR_BOTTOM)*(i-1)/STEPS
    local y1=BAR_BOTTOM+(BAR_TOP-BAR_BOTTOM)*i/STEPS
    local threshold=(i-.5)/STEPS
    fill(-.07548,y0,-.07271,y1,nil,{"F117_IRADS_LEVEL"},{{"parameter_in_range",0,threshold,1.5}})
    fill(-.07045,y0,-.06781,y1,nil,{"F117_IRADS_GAIN"},{{"parameter_in_range",0,threshold,1.5}})
end

-- Rows 12 and 13: Mach number, calibrated airspeed and GPS time.
text("",-.07548,-.04549,SD,"LeftCenter",{"F117_IRADS_MACH"},{{"text_using_parameter",0,0}},{".%02.0f"})
text("",-.07548,-.05485,SD,"LeftCenter",{"F117_IRADS_CAS"},{{"text_using_parameter",0,0}},{"%3.0f"})
text("",-.04491,-.05485,SD,"LeftCenter",{"F117_IRADS_CLOCK_TEXT"},{{"text_using_parameter",0,0}},{"%s"})

-- Row 12, right: release faults, in the failure message position. Normal
-- states (safe, no target, ready, released, on the ground) show nothing here.
-- No bay-door fault (code 6): the bay opens by itself on release.
local status={
    [4]="NO STORE",[5]="LASER NOT READY",[7]="NO SOLUTION",
    [8]="OUT OF RANGE",[11]="LAUNCH RETRY",[13]="LAUNCH UNAVAILABLE",[14]="ALIGN TARGET"
}
for code,label in pairs(status) do
    text(label,.07605,-.04549,SD,"RightCenter",{"F117_RELEASE_STATUS"},{{"parameter_in_range",0,code-.1,code+.1}})
end

-- Row 14: target latitude and longitude, or the ten-step gray scale without one.
text("",-.07548,-.06421,SD,"LeftCenter",{"F117_IRADS_COORD_TEXT"},{{"text_using_parameter",0,0}},{"%s"})
-- The ten steps run edge to edge across the visible screen and fill the band;
-- the first is black. edge_half_width is the visible half-width in page units.
local colour=MFD_COLOUR or {255,255,255}
local EDGE=options.edge_half_width or .0881
local STEP=2*EDGE/10
for i=1,9 do
    local k=i/9
    local x0=-EDGE+i*STEP
    local shade={math.floor(colour[1]*k+.5),math.floor(colour[2]*k+.5),math.floor(colour[3]*k+.5),255}
    local e=quad(x0,-.05978,x0+STEP,-.0760)
    e.name=ROOT.name.."_GRAY_"..i
    e.material=MakeMaterial(nil,shade)
    props(e,locked,no)
end

finish_native_brightness()
