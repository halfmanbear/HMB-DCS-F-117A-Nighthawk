-- Optional presentation settings for the left CMDI EO repeater.
local options=F117_IRADS_OVERLAY_OPTIONS or {}
local finish_native_brightness=options.repeater and function()end or dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_IRADS_SOURCE")
-- IRADS sensor overlay, styled from the mission capture and sensor-display diagram.
-- Coordinates retain the established centre indicator mapping (aperture ~ +/-0.08).
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local ROOT=CreateElement "ceSimple"
ROOT.name=options.root_name or "F117_IRADS_SOURCE"
ROOT.parent_element=options.parent
ROOT.element_params={"mainpower","MFD_OVERLAY","F117_IRADS_POWER"}
ROOT.controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,.9,1.1},{"parameter_in_range",2,.9,1.1}}
ROOT.h_clip_relation=h_clip_relations.COMPARE
ROOT.level=options.level or MFD_LEVEL
Add(ROOT)

local function props(e,params,controllers)
    e.name=e.name or create_guid_string()
    if options.repeater then e.z_enabled=true end
    e.parent_element=ROOT.name
    e.h_clip_relation=h_clip_relations.COMPARE
    e.level=options.level or MFD_LEVEL
    e.collimated=false
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
    local e=strokes.line(points,options.scale or 1,.8)
    e.material=MFD_WHITE
    return props(e,params,controllers)
end
local SD={.0036,.0036,0,0}
local SMALL={.0025,.0025,0,0}
local function text(value,x,y,size,align,params,controllers,formats)
    local e=CreateElement "ceStringSLine"
    local scale=options.scale or 1
    e.init_pos={x*scale,y*scale}
    e.value=value
    e.material=MFD_FONT
    size=size or SD
    e.stringdefs={size[1]*scale,size[1]*.65*scale,size[1]*.13*scale,0}
    e.alignment=align or "LeftCenter"
    e.formats=formats
    strokes.text(e)
    return props(e,params,controllers)
end
local locked={"F117_IRADS_LOCK_VALID"}
local yes={{"parameter_in_range",0,.9,1.1}}
local no={{"parameter_in_range",0,-.1,.1}}

-- Header positions follow the flight capture. LR is lock slant range in feet.
text("",-.075,.063,SD,"LeftCenter",{"F117_IRADS_ALT_TEXT"},{{"text_using_parameter",0,0}},{"%s"})
text("",-.022,.063,SD,"LeftCenter",{"F117_IRADS_RANGE_TEXT"},{{"text_using_parameter",0,0}},{"%s"})
-- Predicted remaining weapon flight time; never represented as confirmed impact.
text("",.075,.063,SD,"RightCenter",{"F117_IRADS_TIME_TEXT"},{{"text_using_parameter",0,0}},{"%s"})

-- Four separated arms in search, horizontal arms and a small gate when locked,
-- matching the two supplied references. The aimpoint stays unobscured.
line({{-.020,0},{-.0045,0}})
line({{.0045,0},{.020,0}})
line({{0,.0045},{0,.019}},locked,no)
line({{0,-.019},{0,-.0045}},locked,no)
line({{-.0017,-.0017},{-.0017,.0017},{.0017,.0017},{.0017,-.0017},{-.0017,-.0017}},locked,yes)

-- Left sensor funnel: fixed reference geometry, not a simulated steering command.
line({{-.066,.043},{-.066,.040},{-.058,.029},{-.058,-.030},{-.054,-.041}})
line({{-.036,.043},{-.036,.040},{-.044,.029},{-.044,-.030},{-.048,-.041}})
text("LG",-.073,-.006,SD)
for i=0,4 do
    local y=-.013-i*.004
    line({{-.073,y},{-.0715,y}})
end
-- Gain bars and the upper-right attitude ladder are omitted until their actual
-- source parameters are available; no static fill or false attitude is drawn.

text("N",-.073,.055,SD,"LeftCenter",{"IRADS_ZOOM"},{{"parameter_in_range",0,2.9,3.1}})
text("CUED",-.073,.048,SD,"LeftCenter",locked,yes)
text("SRCH",-.073,-.049,SMALL,"LeftCenter",locked,no)
text("POINT",-.073,-.049,SMALL,"LeftCenter",locked,yes)
text("W-HOT",-.073,-.055,SMALL,"LeftCenter",{"WHOT_TOGGLE"},{{"parameter_in_range",0,.9,1.1}})
text("B-HOT",-.073,-.055,SMALL,"LeftCenter",{"WHOT_TOGGLE"},{{"parameter_in_range",0,-.1,.1}})
text("",-.073,-.061,SMALL,"LeftCenter",{"F117_IRADS_MAG_TEXT"},{{"text_using_parameter",0,0}},{"%s"})
text("LASE",0,.033,SD,"CenterCenter",{"F117_LASER_FIRING"},{{"parameter_in_range",0,.9,1.1}})
text("ARM",.073,.048,SMALL,"RightCenter",{"F117_LASER_ARMED"},{{"parameter_in_range",0,.9,1.1}})
text("BOST",.073,.041,SMALL,"RightCenter",{"BOST_TOGGLE"},{{"parameter_in_range",0,.9,1.1}})

-- Compact operational feedback retained from the original overlay.
local status={
    [1]="MASTER SAFE",[2]="IRADS OFF",[3]="NO TARGET",[4]="NO STORE",
    [5]="LASER NOT READY",[6]="BAY CLOSED",[7]="NO SOLUTION",
    [8]="OUT OF RANGE",[9]="RELEASE READY",[10]="RELEASED",
    [11]="LAUNCH RETRY",[12]="ON GROUND",[13]="LAUNCH UNAVAILABLE",[14]="ALIGN TARGET"
}
for code,label in pairs(status) do
    text(label,.073,-.049,SMALL,"RightCenter",{"F117_RELEASE_STATUS"},{{"parameter_in_range",0,code-.1,code+.1}})
end
local stores={[0]="GBU-31V1",[1]="GBU-31V3",[2]="GBU-32",[3]="GBU-12",[4]="GBU-27"}
for code,label in pairs(stores) do
    text(label,.073,-.055,SMALL,"RightCenter",{"F117_CCRP_PROFILE"},{{"parameter_in_range",0,code-.1,code+.1}})
end
text("",.073,-.061,SMALL,"RightCenter",{"F117_WEAPON_STATION"},{{"text_using_parameter",0,0}},{"STN %.0f"})

-- Target latitude/longitude in degrees and decimal minutes, as in the capture.
text("",0,-.070,SD,"CenterCenter",{"F117_IRADS_COORD_TEXT"},{{"text_using_parameter",0,0}},{"%s"})

finish_native_brightness()
