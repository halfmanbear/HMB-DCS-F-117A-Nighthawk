-- LEFT VSD DESIGN: manual PDF p33, Figure 4-13 basic display.
-- Metres, fitted to the measured aperture. Flight data uses existing parameters;
-- navigation/status text is static reference artwork. Default left cockpit page.
local SD,SM,VAL=VSD_SD,VSD_SD_SMALL,VSD_SD_VALUE
local ROOT=CreateElement "ceSimple"
ROOT.name="F117_VSD_SOURCE"
ROOT.element_params={"mainpower"}
ROOT.controllers={{"parameter_in_range",0,0.9,1.1}}
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
local function text(value,x,y,sd,align,params,controllers,formats,colour,parent,level)
    local e=CreateElement "ceStringPoly"
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
local function circle(cx,cy,r)
    local p={}
    for i=0,64 do local a=i*math.pi/32;table.insert(p,{cx+r*math.cos(a),cy+r*math.sin(a)}) end
    return p
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
line({{-.09,0},{.09,0}},"white",pitch,2,.00028)
for degrees=-30,30,5 do
    if degrees~=0 then
        local y=degrees*R/30
        local w=degrees%10==0 and .012 or .007
        line({{-w,y},{-.002,y}},"white",pitch,2)
        line({{.002,y},{w,y}},"white",pitch,2)
        if degrees%10==0 then
            text(tostring(math.abs(degrees)),-.015,y,SM,nil,nil,nil,nil,nil,pitch,2)
            text(tostring(math.abs(degrees)),.015,y,SM,nil,nil,nil,nil,nil,pitch,2)
        end
    end
end
poly(ball,"background",nil,2,h_clip_relations.DECREASE_IF_LEVEL)
line(ball)
for _,degrees in ipairs({-60,-45,-30,-20,-10,0,10,20,30,45,60}) do
    local a=math.rad(degrees);local r=R+.0015
    local l=degrees%30==0 and .0018 or .0010
    line({{r*math.sin(a),CY+r*math.cos(a)},{(r+l)*math.sin(a),CY+(r+l)*math.cos(a)}})
end
poly({{0,CY+R+.002},{-.0012,CY+R+.004},{.0012,CY+R+.004}},"white")
line({{-.012,CY},{-.004,CY},{-.002,CY-.001},{0,CY},{.002,CY-.001},{.004,CY},{.012,CY}},nil,nil,nil,.0004)
line({{-.003,CY+.004},{0,CY+.005},{.003,CY+.004}},"magenta")

-- Top strip: ground speed, AOA scale, heading and vertical velocity.
box(-.040,.040,.013,.0045)
text("",-.040,.040,SM,nil,{"GS_HUD"},{{"text_using_parameter",0,0}},{"GS %3.0f"})
text("P/L",-.045,.033,SM)
line({{-.028,.043},{-.028,.014}})
for i=0,15 do
    local y=.014+i*.0019
    line({{-.028,y},{-.028+(i%5==0 and .0035 or .0017),y}})
    if i%5==0 then text(tostring(i),-.0228,y,SM) end
end
line({{-.031,.020},{-.030,.026},{-.029,.025}},nil,nil,nil,.00035)
text("MEA",0,.043,SM)
box(0,.036,.010,.0045)
text("",0,.036,SD,nil,{"HEADING_HUD"},{{"text_using_parameter",0,0}},{"%03.0f"})
for i=-6,6 do local x=i*.0017;line({{x,.029},{x,.029+(i%3==0 and .0018 or .0009)}}) end
text("27",-.012,.034,SM)
text("33",.012,.034,SM)
line({{-.0018,.026},{0,.029},{.0018,.026}})
for i=0,5 do line({{.023,.017+i*.005},{.025,.017+i*.005}}) end
line({{.027,.021},{.030,.021},{.030,.040}})
text("",.035,.033,SM,"LeftCenter",{"VVI_HUD"},{{"text_using_parameter",0,0}},{"%+.0f"})

-- Airspeed tape and boxed CAS; tape graduations remain design samples.
line({{-.034,-.030},{-.034,.025}})
for i=0,10 do local y=-.030+i*.005;line({{-.034,y},{-.034+(i%5==0 and .003 or .0014),y}}) end
text("350",-.039,.014,SM)
text("300",-.039,-.006,SM)
text("250",-.039,-.027,SM)
text("",-.043,.006,SM,nil,{"MACH_A"},{{"text_using_parameter",0,0}},{"%.2f"})
poly({{-.033,-.001},{-.030,0},{-.033,.001}},"white")
poly({{-.049,-.003},{-.036,-.003},{-.036,.003},{-.049,.003}},"background")
box(-.0425,0,.013,.006)
text("",-.0425,0,VAL,nil,{"CURR_IAS"},{{"text_using_parameter",0,0}},{"%3.0f"})

-- Altitude tape and boxed barometric altitude.
line({{.033,-.030},{.033,.025}})
for i=0,12 do local y=-.030+i*.0045;line({{.033,y},{.033+(i%4==0 and .0025 or .0012),y}}) end
text("22500",.041,.019,SM)
text("22000",.041,-.008,SM)
text("21500",.041,-.026,SM)
poly({{.031,-.001},{.033,0},{.031,.001}},"white")
poly({{.034,-.003},{.050,-.003},{.050,.003},{.034,.003}},"background")
box(.042,0,.016,.006)
text("",.042,0,VAL,nil,{"ALTITUDE_HUD"},{{"text_using_parameter",0,0}},{"%5.0f"})

-- Static lower annotations from the basic VSD (not valid navigation/status).
-- ARS selection blanks the digital readout, FMS status/commands, ICE and CONS (manual 4-21).
local arsBlank=group({0,0},nil,{"F117_ARS_ACTIVE"},{{"parameter_in_range",0,-.1,.1}})
text("ICE",-.021,-.027,SM,nil,nil,nil,nil,nil,arsBlank)
text("ALIGN",-.0195,-.0295,SM)
text("CONS",.021,-.027,SM,nil,nil,nil,nil,nil,arsBlank)
text("ALERT",.040,-.032,SM)
box(-.035,-.0345,.022,.009,nil,arsBlank)
text("D  39",-.044,-.0315,SM,"LeftCenter",nil,nil,nil,nil,arsBlank)
text("TTG 13:47",-.044,-.0345,SM,"LeftCenter",nil,nil,nil,nil,arsBlank)
text("RNG 108.4",-.044,-.0375,SM,"LeftCenter",nil,nil,nil,nil,arsBlank)
box(.036,-.037,.023,.0045)
text("DME 40.7",.036,-.037,SM)

-- FMS command line (Fig 4-13 item 26): A/T CAS hold reads "C <value> CAS" (manual 4-39).
local atLine=group({-.022,-.0340},arsBlank,{"F117_AT_ENGAGED"},{{"parameter_in_range",0,.9,1.1}})
text("",0,0,SM,"LeftCenter",{"F117_AT_CAS_COMMAND"},{{"text_using_parameter",0,0}},{"C %3.0f CAS"},nil,atLine)

-- ARS indication (item 31): minimum pullout altitude in red, to the next lower thousand feet.
local arsLine=group({-.030,-.0335},nil,{"F117_ARS_ACTIVE"},{{"parameter_in_range",0,.9,1.1}})
text("",0,0,VAL,"LeftCenter",{"F117_ARS_MIN_ALT"},{{"text_using_parameter",0,0}},{"ARS  %5.0f"},"red",arsLine)
text("VSD",-.035,-.0415,SM,nil,nil,nil,nil,"magenta")
box(-.035,-.0415,.008,.0025)
line({{-.023,-.0415},{-.015,-.0415}})
line({{-.019,-.043},{-.019,-.040}})
text("STAT",0,-.0415,SM)
text("DEP",.034,-.0415,SM)
