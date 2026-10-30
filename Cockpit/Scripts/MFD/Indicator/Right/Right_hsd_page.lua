-- Basic HSD: manual PDF page 36, Figure 4-14 (printed 4-23).
-- Metres. Heading/GS are live; unavailable navigation fields show dashes.
local SD,SM,VAL=HSD_SD,HSD_SD_SMALL,HSD_SD_VALUE
local ROOT=CreateElement "ceSimple"
ROOT.name="F117_HSD_SOURCE"
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
    local e=CreateElement "ceStringPoly"
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

-- Fixed upper switch legends and speed block.
text("MARK",-.027,.042,SD)
text("SNSR",-.010,.042,SD)
text("ENTR",.008,.042,SD)
box(-.038,.032,.020,.010,"magenta")
text("",-.046,.0345,SM,"LeftCenter",{"GS_HUD"},{{"text_using_parameter",0,0}},{"GS  %3.0f"})
text("TAS  ---",-.046,.030,SM,"LeftCenter")
box(.038,.032,.021,.0045,"magenta")
text("CRS SEL",.038,.032,SM)
text("---",.038,.0275,SM)

-- Heading-up card: north is zero; positive headings run clockwise.
-- The parent rotates counterclockwise as aircraft heading increases.
local CY,R=-.001,.033
local card=group({0,CY},ROOT,{"HEADING_HUD"},{{"rotate_using_parameter",0,math.pi/180}})
for degrees=0,355,5 do
    local a=math.rad(degrees)
    local length=degrees%30==0 and .0028 or (degrees%10==0 and .0018 or .0010)
    line({{R*math.sin(a),R*math.cos(a)},{(R-length)*math.sin(a),(R-length)*math.cos(a)}},"magenta",card)
    if degrees%30==0 then
        local label=({[0]="N",[90]="E",[180]="S",[270]="W"})[degrees] or tostring(degrees/10):gsub("%.0$","")
        -- Card numbers remain radial and rotate with the compass card.
        local anchor=group({(R-.0052)*math.sin(a),(R-.0052)*math.cos(a)},card,nil,nil,-degrees)
        text(label,0,0,SD,nil,nil,nil,nil,"white",anchor)
    end
end
-- Fixed lubber line and aircraft symbol.
line({{0,CY+R+.001},{0,CY+R-.003}},"white",nil,nil,.00035)
line({{-.004,CY},{.004,CY}},"white",nil,nil,.00035)
line({{0,CY+.002},{0,CY-.006}},"white",nil,nil,.00035)
line({{-.0015,CY-.005},{.0015,CY-.005}},"white",nil,nil,.00035)

-- No route/course/TACAN receiver is connected yet: avoid invented bearings,
-- DME, destination, warning or master-arm indications.
box(-.036,-.0335,.025,.010,"magenta")
text("D   --",-.047,-.031,SM,"LeftCenter")
text("TTG --:--",-.047,-.034,SM,"LeftCenter")
text("RNG ---.-",-.047,-.037,SM,"LeftCenter")
box(.036,-.035,.024,.0045,"magenta")
text("DME ---.-",.036,-.035,SM)
text("HSD",-.033,-.0405,SD)
box(-.033,-.0405,.009,.0034,"magenta")
text("MAP",-.014,-.0405,SD)
text("STAT",.005,-.0405,SD)
text("SMD",.023,-.0405,SD)
text("DFRM",.041,-.0405,SD)
