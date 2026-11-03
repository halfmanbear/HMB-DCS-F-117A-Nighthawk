local finish_native_brightness=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_VSD_SOURCE")
-- LEFT VSD DESIGN: manual PDF p33, Figure 4-13 basic display, matched to the
-- cockpit video frames in docs/reference/CockpitImages/CMDI_VSD.
-- Metres, fitted to the measured aperture. Flight data uses existing parameters;
-- navigation/status text is static reference artwork. Default left cockpit page.
local SD,SM,VAL=VSD_SD,VSD_SD_SMALL,VSD_SD_VALUE
local ROOT=CreateElement "ceSimple"
ROOT.name="F117_VSD_SOURCE"
ROOT.element_params={"mainpower","F117_LEFT_EO"}
ROOT.controllers={{"parameter_in_range",0,0.9,1.1},{"parameter_in_range",1,-.1,.1}}
Add(ROOT)
local function props(e,parent,level,params,controllers)
    e.name=e.name or create_guid_string()
    e.parent_element=(parent or ROOT).name
    e.collimated=false
    e.z_enabled=true
    e.h_clip_relation=h_clip_relations.COMPARE
    e.level=level or 1
    e.additive_alpha=false
    e.blend_mode=blend_mode.IBM_REGULAR
    e.element_params=params
    e.controllers=controllers
    Add(e)
    return e
end
local function group(pos,parent,params,controllers)
    local e=CreateElement "ceSimple"
    e.init_pos={pos[1],pos[2],0}
    return props(e,parent,1,params,controllers)
end
local function poly(vertices,colour,parent,level,relation)
    local e=CreateElement "ceMeshPoly"
    e.primitivetype="triangles"
    e.material=VSD_MATERIALS[colour or "white"]
    e.vertices=vertices
    local indices={}
    for i=1,#vertices-2 do for _,j in ipairs({0,i,i+1}) do table.insert(indices,j) end end
    e.indices=indices
    if relation then
        e.name=create_guid_string();e.parent_element=ROOT.name
        e.h_clip_relation=relation;e.level=level;e.isvisible=false
        e.collimated=false;e.z_enabled=true;Add(e);return e
    end
    return props(e,parent,level)
end
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local function line(points,colour,parent,level,width)
    local e=strokes.line(points,1,(width or .00020)/.00020)
    e.material=VSD_MATERIALS[colour or "white"]
    return props(e,parent,level)
end
-- Many disjoint segments ({x1,y1,x2,y2}, ...) in one element: tape graduations.
local function segments(list,colour,parent,level)
    local e=strokes.line({{0,0},{0,0}},1,1)
    local vertices,indices={},{}
    for _,s in ipairs(list) do
        vertices[#vertices+1]={s[1],s[2]};vertices[#vertices+1]={s[3],s[4]}
        indices[#indices+1]=#vertices-2;indices[#indices+1]=#vertices-1
    end
    e.vertices=vertices;e.indices=indices
    e.material=VSD_MATERIALS[colour or "white"]
    return props(e,parent,level)
end
local function text(value,x,y,sd,align,params,controllers,formats,colour,parent,level)
    local e=CreateElement "ceStringSLine"
    e.value=value;e.init_pos={x,y,0}
    e.material=VSD_FONTS[colour or "white"]
    local s=sd or SD
    local height=s[1]*GetScale()*VSD_READABILITY.mfd_text_scale
    e.stringdefs={height,height*.55,height*.10,s[4]}
    strokes.text(e)
    e.alignment=align or "CenterCenter";e.formats=formats
    return props(e,parent,level,params,controllers)
end
local function box(x,y,w,h,colour,parent)
    return line({{x-w/2,y-h/2},{x+w/2,y-h/2},{x+w/2,y+h/2},{x-w/2,y+h/2},{x-w/2,y-h/2}},colour,parent)
end
-- Background-filled box: masks tape labels scrolling behind a readout.
local function readout(x,y,w,h,colour,parent)
    poly({{x-w/2,y-h/2},{x+w/2,y-h/2},{x+w/2,y+h/2},{x-w/2,y+h/2}},"background",parent)
    return box(x,y,w,h,colour,parent)
end
local function rect(x1,y1,x2,y2) return {{x1,y1},{x2,y1},{x2,y2},{x1,y2}} end
local function circle(cx,cy,r)
    local p={}
    for i=0,64 do local a=i*math.pi/32;table.insert(p,{cx+r*math.cos(a),cy+r*math.sin(a)}) end
    return p
end
-- Shown only while the named parameter is 1. Nothing drives these yet, so they stay blank.
local function when(name,parent)
    return group({0,0},parent,{name},{{"parameter_in_range",0,.9,1.1}})
end
-- Rounded safe area, inset from the 104.1 x 95.3 mm measured screen.
local aperture={}
for _,c in ipairs({{.044,.041,0},{-.044,.041,90},{-.044,-.037,180},{.044,-.037,270}}) do
    for i=0,8 do local a=math.rad(c[3]+i*90/8);table.insert(aperture,{c[1]+.006*math.cos(a),c[2]+.006*math.sin(a)}) end
end
poly(aperture,"background",nil,1,h_clip_relations.REWRITE_LEVEL)
poly({{-.052,-.046},{.052,-.046},{.052,.050},{-.052,.050}},"background")

-- Attitude ball: blue #0310B2 / ground #A38C50.
local CY,R=-.002,.024
local ball=circle(0,CY,R)
poly(ball,"background",nil,1,h_clip_relations.INCREASE_IF_LEVEL)
local bank=group({0,CY},ROOT,{"ROLL_HUD"},{{"rotate_using_parameter",0,1}})
local pitch=group({0,0},bank,{"PITCH_HUD"},{{"move_up_down_using_parameter",0,-R/math.rad(30)}})
poly({{-.12,0},{.12,0},{.12,.12},{-.12,.12}},"sky",pitch,2)
poly({{-.12,-.12},{.12,-.12},{.12,0},{-.12,0}},"earth",pitch,2)
-- Ladder: continuous 10 degree bars numbered at both ends, short centred 5 degree dashes.
line({{-.09,0},{.09,0}},"white",pitch,2,.00028)
for degrees=-25,25,5 do
    local y=degrees*R/30
    if degrees==0 then
        text("0",-.0072,y,SM,nil,nil,nil,nil,nil,pitch,2)
        text("0",.0072,y,SM,nil,nil,nil,nil,nil,pitch,2)
    elseif degrees%10==0 then
        line({{-.0040,y},{.0040,y}},"white",pitch,2)
        text(tostring(math.abs(degrees)),-.0072,y,SM,nil,nil,nil,nil,nil,pitch,2)
        text(tostring(math.abs(degrees)),.0072,y,SM,nil,nil,nil,nil,nil,pitch,2)
    else
        line({{-.0015,y},{.0015,y}},"white",pitch,2)
    end
end
poly(ball,"background",nil,2,h_clip_relations.DECREASE_IF_LEVEL)
line(ball)
-- Fixed bank graduations all round the ball; the open triangles roll with the ball.
for _,degrees in ipairs({10,20,30,45,60,90,120,150}) do
    for _,sign in ipairs({-1,1}) do
        local a=math.rad(sign*degrees);local r=R+.0012
        local l=degrees%30==0 and .0018 or .0011
        line({{r*math.sin(a),CY+r*math.cos(a)},{(r+l)*math.sin(a),CY+(r+l)*math.cos(a)}})
    end
end
line({{0,R-.0006},{-.0011,R-.0026},{.0011,R-.0026},{0,R-.0006}},"white",bank)
line({{0,-R+.0006},{-.0011,-R+.0026},{.0011,-R+.0026},{0,-R+.0006}},"white",bank)
-- Steering line (static: no steering data yet), heading lubber and aircraft symbol.
line({{0,.0318},{0,-.0300}},"green")
line({{-.0010,.0303},{0,.0322},{.0010,.0303}})
line({{-.0042,CY},{-.0022,CY},{-.0011,CY-.0018},{0,CY-.0004},{.0011,CY-.0018},{.0022,CY},{.0042,CY}},nil,nil,nil,.0004)
-- CCRP release window staple: enters 30 s before the ballistic release point and
-- descends the steering line; it sits on the pitch reference symbol (release gate
-- open) while the EFM reports the store in its release zone.
local STAPLE={{-.0022,0},{-.0022,.0010},{.0022,.0010},{.0022,0}}
local staple=group({0,CY+.0002},ROOT,{"F117_RELEASE_CUE_TTG","F117_RELEASE_CUE_VALID","F117_RELEASE_CUE_IN_ZONE"},
    {{"parameter_in_range",0,.01,30},{"parameter_in_range",1,.9,1.1},{"parameter_in_range",2,-.1,.1},
     {"move_up_down_using_parameter",0,.0005}})
line(STAPLE,"green",staple,nil,.0003)
local stapleGate=group({0,CY+.0002},ROOT,{"F117_RELEASE_CUE_VALID","F117_RELEASE_CUE_IN_ZONE"},
    {{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,.9,1.1}})
line(STAPLE,"green",stapleGate,nil,.0003)

-- Scrolling tapes, each clipped to its own window.
local SX,AX=-.0326,.0307            -- airspeed and altitude tape spines
local KT,FT,DEG=.00029,.0000273,.00045 -- metres per knot, foot, degree
local windows={
    rect(-.052,-.0265,SX+.0003,.0235),
    rect(AX-.0003,-.0320,.052,.0235),
    rect(-.0118,.0325,.0118,.0430),
}
for _,w in ipairs(windows) do poly(w,"background",nil,1,h_clip_relations.INCREASE_IF_LEVEL) end
local ias=group({0,CY},ROOT,{"CURR_IAS"},{{"move_up_down_using_parameter",0,-KT}})
local ticks={}
for kt=0,800,10 do ticks[#ticks+1]={SX,kt*KT,SX-(kt%50==0 and .0028 or .0016),kt*KT} end
segments(ticks,"white",ias,2)
for kt=0,800,50 do text(tostring(kt),SX-.0036,kt*KT,SM,"RightCenter",nil,nil,nil,nil,ias,2) end
local alt=group({0,CY},ROOT,{"ALTITUDE_HUD"},{{"move_up_down_using_parameter",0,-FT}})
ticks={}
for ft=-1000,50000,100 do ticks[#ticks+1]={AX,ft*FT,AX+(ft%500==0 and .0025 or .0012),ft*FT} end
segments(ticks,"white",alt,2)
for ft=-1000,50000,500 do text(tostring(ft),AX+.0034,ft*FT,SM,"LeftCenter",nil,nil,nil,nil,alt,2) end
local HY=.0395                      -- heading readout row; ticks rise from .0335
local hdg=group({0,0},ROOT,{"HEADING_HUD"},{{"move_left_right_using_parameter",0,-DEG}})
ticks={}
for h=-40,400,5 do ticks[#ticks+1]={h*DEG,.0335,h*DEG,.0335+(h%10==0 and .0018 or .0010)} end
segments(ticks,"white",hdg,2)
for h=-30,390,30 do text(string.format("%02d",(h%360)/10),h*DEG,HY,SM,nil,nil,nil,nil,nil,hdg,2) end
for _,w in ipairs(windows) do poly(w,"background",nil,2,h_clip_relations.DECREASE_IF_LEVEL) end

-- Fixed tape parts: spines, readouts and the open chevrons tied to the ball.
line({{SX,-.0265},{SX,.0235}})
line({{AX,-.0320},{AX,.0235}})
line({{-R-.0004,CY},{SX+.0006,CY}});line({{SX+.0026,CY+.0012},{SX+.0006,CY},{SX+.0026,CY-.0012}})
line({{R+.0004,CY},{AX-.0006,CY}});line({{AX-.0026,CY+.0012},{AX-.0006,CY},{AX-.0026,CY-.0012}})
readout(-.0405,CY,.0115,.0055)
text("",-.0405,CY,VAL,nil,{"CURR_IAS"},{{"text_using_parameter",0,0}},{"%3.0f"})
poly(rect(-.0445,CY+.0030,-.0365,CY+.0064),"background")
text("",-.0405,CY+.0047,SM,nil,{"MACH_A"},{{"text_using_parameter",0,0}},{"%.2f"})
readout(.0400,CY,.0155,.0055)
text("",.0400,CY,VAL,nil,{"ALTITUDE_HUD"},{{"text_using_parameter",0,0}},{"%5.0f"})
text("P/L",-.0400,.0255,SM)
readout(0,HY,.0095,.0050)
text("",0,HY,SD,nil,{"HEADING_HUD"},{{"text_using_parameter",0,0}},{"%03.0f"})
line({{-.0012,.0353},{.0012,.0353}},"green")
local mea=when("F117_VSD_MEA")
readout(0,.0445,.0090,.0040,nil,mea)
text("MEA",0,.0445,SM,nil,nil,nil,nil,nil,mea)

-- Ground speed and AOA (0-15 units, red above 10, index at 10).
box(-.040,.0395,.013,.0045)
text("",-.040,.0395,SM,nil,{"GS_HUD"},{{"text_using_parameter",0,0}},{"GS %3.0f"})
local AOX,A0,AU=-.028,.014,.0019
line({{AOX,A0},{AOX,A0+10*AU}})
line({{AOX,A0+10*AU},{AOX,A0+15*AU}},"red",nil,nil,.0003)
for i=0,15 do
    local y=A0+i*AU
    line({{AOX,y},{AOX+(i%5==0 and .0035 or .0017),y}})
    if i%5==0 then text(tostring(i),AOX+.0052,y,SM) end
end
line({{AOX-.0035,A0+10*AU},{AOX,A0+10*AU}})
local aoaPointer=group({0,A0},ROOT,{"F117_OCIP_AOA"},
    {{"parameter_in_range",0,-.01,math.rad(15.5)},{"move_up_down_using_parameter",0,AU*180/math.pi}})
line({{AOX-.0004,0},{AOX-.0022,.0009},{AOX-.0022,-.0009},{AOX-.0004,0}},"white",aoaPointer)

-- Vertical velocity: alternating graduations, open pointer at the zero mark, digital value.
for i=0,6 do
    local y=.0383-i*.00384
    line({{i%2==0 and .0201 or .0219,y},{.0234,y}})
end
line({{.0240,.0306},{.0256,.0314},{.0256,.0298},{.0240,.0306}});line({{.0256,.0306},{.0272,.0306}})
text("",.0355,.0306,SM,nil,{"VVI_HUD"},{{"text_using_parameter",0,0}},{"%.0f"})

-- Lower annotations. Destination, time to go and range come from the mission
-- route (Systems/Navigation.lua) and show dashes without one.
-- ARS selection blanks the digital readout and FMS status/commands (manual 4-21).
local arsBlank=group({0,0},nil,{"F117_ARS_ACTIVE"},{{"parameter_in_range",0,-.1,.1}})
text("ETA",-.046,-.0283,SM,"LeftCenter",nil,nil,nil,nil,arsBlank)
box(-.035,-.0345,.022,.009,nil,arsBlank)
for i,name in ipairs({"D_TEXT","TTG_TEXT","RNG_TEXT"}) do
    text("",-.044,-.0285-.003*i,SM,"LeftCenter",{"F117_NAV_"..name},{{"text_using_parameter",0,0}},{"%s"},nil,arsBlank)
end
local dr=when("F117_NAV_DR")
box(-.0205,-.0235,.0075,.0035,"amber",dr)
text("DR",-.0205,-.0235,SM,nil,nil,nil,nil,nil,dr)
box(.036,-.0335,.023,.0045)
text("DME",.036,-.0335,SM) -- no TACAN receiver: no distance value
-- Store legend (Weapons.lua): the selected store, or the store just fired,
-- crossed out with thin red lines until the next station step or designation.
for profile,name in pairs({[0]="GBU31",[1]="GBU31V3",[2]="GBU32",[3]="GBU12",[4]="GBU27"}) do
    text(name,.036,-.0375,SM,nil,{"F117_VSD_STORE"},{{"parameter_in_range",0,profile-.1,profile+.1}})
end
local fired=when("F117_VSD_STORE_FIRED")
line({{.0300,-.0390},{.0420,-.0360}},"red",fired,nil,.00012)
line({{.0300,-.0360},{.0420,-.0390}},"red",fired,nil,.00012)

-- FMS command line (Fig 4-13 item 26): A/T CAS hold reads "C <value> CAS" (manual 4-39).
local atLine=group({-.0165,-.0315},arsBlank,{"F117_AT_ENGAGED"},{{"parameter_in_range",0,.9,1.1}})
text("C",0,0,SM,"LeftCenter",nil,nil,nil,"green",atLine)
text("",.0030,0,SM,"LeftCenter",{"F117_AT_CAS_COMMAND"},{{"text_using_parameter",0,0}},{"%3.0f CAS"},nil,atLine)

-- ARS indication (item 31): minimum pullout altitude in red, to the next lower thousand feet.
local arsLine=group({-.030,-.0335},nil,{"F117_ARS_ACTIVE"},{{"parameter_in_range",0,.9,1.1}})
text("",0,0,VAL,"LeftCenter",{"F117_ARS_MIN_ALT"},{{"text_using_parameter",0,0}},{"ARS  %5.0f"},"red",arsLine)

-- Bottom option row.
box(-.028,-.0415,.008,.0028,"green")
text("VSD",-.028,-.0415,SM,nil,nil,nil,nil,"green")
line({{-.018,-.0415},{-.0148,-.0415}});line({{-.0132,-.0415},{-.010,-.0415}})
line(circle(-.014,-.0415,.0008));line({{-.014,-.0407},{-.014,-.0395}})
text("STAT",0,-.0415,SM)
text("DEP",.026,-.0415,SM)

F117_SIDE_DIM_PARAMETER="F117_LEFT_DIM_OPACITY"
F117_SIDE_DIM_ROOT=ROOT.name
dofile(LockOn_Options.script_path.."MFD/Indicator/side_display_dimmer.lua")

-- EO is composed separately by CMDI_formats.lua.

finish_native_brightness()
