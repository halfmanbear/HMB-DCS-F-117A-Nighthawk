local finish_native_brightness=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_HSD_SOURCE")
-- Basic HSD: manual PDF page 36, Figure 4-14 (printed 4-23).
-- Metres. Heading/GS are live; unavailable navigation fields show dashes.
local SD,SM,VAL=HSD_SD,HSD_SD_SMALL,HSD_SD_VALUE
local ROOT=CreateElement "ceSimple"
ROOT.name="F117_HSD_SOURCE"
ROOT.element_params={"F117_ON_CMDI_R"}
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
local function group(pos,parent,params,controllers,rotation)
    local e=CreateElement "ceSimple"
    e.init_pos={pos[1],pos[2],0}
    e.init_rot={rotation or 0,0,0}
    return props(e,parent,1,params,controllers)
end
local function poly(vertices,colour,parent,level,relation)
    local e=CreateElement "ceMeshPoly"
    e.primitivetype="triangles"
    e.material=HSD_MATERIALS[colour or "white"]
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
    e.material=HSD_MATERIALS[colour or "white"]
    return props(e,parent,level)
end
local function text(value,x,y,sd,align,params,controllers,formats,colour,parent,level)
    local e=CreateElement "ceStringSLine"
    e.value=value;e.init_pos={x,y,0}
    e.material=HSD_FONTS[colour or "white"]
    local s=sd or SD
    local height=s[1]*GetScale()*HSD_READABILITY.mfd_text_scale
    e.stringdefs={height,height*.55,height*.10,s[4]}
    strokes.text(e)
    e.alignment=align or "CenterCenter";e.formats=formats
    return props(e,parent,level,params,controllers)
end
local function box(x,y,w,h,colour)
    return line({{x-w/2,y-h/2},{x+w/2,y-h/2},{x+w/2,y+h/2},{x-w/2,y+h/2},{x-w/2,y-h/2}},colour)
end
local function circle(cx,cy,r)
    local p={}
    for i=0,64 do local a=i*math.pi/32;table.insert(p,{cx+r*math.cos(a),cy+r*math.sin(a)}) end
    return p
end
-- Same measured side-screen safe area as the VSD, shifted to right connector centre.
local aperture={}
for _,c in ipairs({{.044,.041,0},{-.044,.041,90},{-.044,-.037,180},{.044,-.037,270}}) do
    for i=0,8 do local a=math.rad(c[3]+i*90/8);table.insert(aperture,{c[1]+.006*math.cos(a),c[2]+.006*math.sin(a)}) end
end
poly(aperture,"background",nil,1,h_clip_relations.REWRITE_LEVEL)
poly({{-.052,-.046},{.052,-.046},{.052,.050},{-.052,.050}},"background")

-- Layout matched to the cockpit video frame in docs/reference/CockpitImages/CMDI_HSD.
-- Fixed upper switch legends and speed block.
text("MARK",-0.027,0.042,SD)
text("-",-0.027,0.0385,SM)            -- mark number: no mark store yet
text("SNSR",-0.0135,0.042,SD)
text("ENTR",0,0.042,SD)
box(-0.039,0.0295,.0175,.0090)
text("",-0.0465,0.0315,SM,"LeftCenter",{"GS_HUD"},{{"text_using_parameter",0,0}},{"GS  %3.0f"})
text("",-0.0465,0.0275,SM,"LeftCenter",{"F117_OCIP_TAS"},{{"text_using_parameter",0,0}},{"TAS %3.0f"})
box(0.036,0.0305,.0150,.0042)
text("",0.036,0.0305,SM,nil,{"F117_NAV_CRS_TEXT"},{{"text_using_parameter",0,0}},{"%s"})
box(0.036,0.023,.0150,.0042)
text("CRS SEL",0.036,0.023,SM)
text("---",0.036,0.019,SM)

-- Heading-up card: north is zero; positive headings run clockwise.
-- The parent rotates counterclockwise as aircraft heading increases.
-- Labels sit on the ring in place of the 30-degree ticks and stay upright.
local CY,R=-.001,.030
local card=group({0,CY},ROOT,{"HEADING_HUD"},{{"rotate_using_parameter",0,math.pi/180}})
for degrees=0,355,5 do
    local a=math.rad(degrees)
    if degrees%30==0 then
        local label=({[0]="N",[90]="E",[180]="S",[270]="W"})[degrees] or tostring(degrees/10):gsub("%.0$","")
        local anchor=group({(R-.0005)*math.sin(a),(R-.0005)*math.cos(a)},card)
        local upright=group({0,0},anchor,{"HEADING_HUD"},{{"rotate_using_parameter",0,-math.pi/180}})
        text(label,0,0,SD,nil,nil,nil,nil,"white",upright)
    else
        local length=degrees%10==0 and .0016 or .0010
        line({{R*math.sin(a),R*math.cos(a)},{(R-length)*math.sin(a),(R-length)*math.cos(a)}},"white",card)
    end
end
-- Fixed lubber above the ring and reference marks at 3, 6 and 9 o'clock.
line({{0,CY+R+.0015},{0,CY+R+.0060}},"white",nil,nil,.00035)
line({{-R-.0017,CY},{-R-.0075,CY}},"white",nil,nil,.00035)
line({{R+.0017,CY},{R+.0075,CY}},"white",nil,nil,.00035)
line({{0,CY-R-.0017},{0,CY-R-.0065}},"white",nil,nil,.00035) -- shorter: clears the STAT legend
-- Course group: arrow, tip circle, course line and the small outer arrowhead
-- outside the ring all point at the desired course to the active waypoint
-- (Systems/Navigation.lua). F117_NAV_REL_COURSE is clockwise; positive
-- rotation is counterclockwise, hence the -1 gain. With no route it is 0 (up).
local course=group({0,CY},ROOT,{"F117_NAV_REL_COURSE"},{{"rotate_using_parameter",0,-1}})
line({{-.0014,R+.0013},{0,R+.0032},{.0014,R+.0013}},"white",course)
line({{-.0025,R-.0082},{0,R-.0027},{.0025,R-.0082}},"white",course)
line(circle(0,R-.0021,.0006),"white",course)
line({{0,R-.0027},{0,-R+.0010}},"white",course)
-- Deviation dots stay fixed on the aircraft axis; no deviation bar yet.
for _,x in ipairs({-.46,-.23,.23,.46}) do poly(circle(x*R,CY,.00035),"white") end
-- Fixed aircraft symbol.
line({{-.0037,CY+.0005},{.0037,CY+.0005}},"white",nil,nil,.00035)
line({{-.0012,CY-.0040},{.0012,CY-.0040}},"white",nil,nil,.00035)

-- Destination, time to go and range come from the mission route; they show
-- dashes without one. No TACAN receiver: DME stays a bare legend.
text("COR",-0.046,-0.0225,SM,"LeftCenter")
box(-0.036,-0.0295,.025,.010)
for i,name in ipairs({"D_TEXT","TTG_TEXT","RNG_TEXT"}) do
    text("",-0.047,-0.023-.003*i,SM,"LeftCenter",{"F117_NAV_"..name},{{"text_using_parameter",0,0}},{"%s"})
end
box(0.0386,-0.0305,.0193,.0045)
text("DME",0.0301,-0.0305,SM,"LeftCenter")
-- Bottom option row: size, weight and selection box shared with VSD and MAP.
local ROW=dofile(LockOn_Options.script_path.."MFD/Indicator/cmdi_option_row.lua")
local function label(value,x,y)
    local e=CreateElement "ceStringSLine"
    e.value=value;e.init_pos={x,y,0};e.alignment="CenterCenter"
    e.material=HSD_FONTS.white;e.stringdefs=ROW.stringdefs()
    strokes.text(e,ROW.weight)
    return props(e)
end
label("HSD",-.0252,-.0405)
-- HSD is the selected page; legend text stays white.
line(ROW.outline(-.0252,-.0405),"paleyellow",nil,nil,.00020*ROW.weight)
label("MAP",-.0119,-.0405)
label("STAT",.0012,-.0405)
label("SMD",.0149,-.0405)
label("DFRM",.0282,-.0405)

F117_SIDE_DIM_PARAMETER="F117_RIGHT_DIM_OPACITY"
F117_SIDE_DIM_ROOT=ROOT.name
dofile(LockOn_Options.script_path.."MFD/Indicator/side_display_dimmer.lua")

finish_native_brightness()
