-- F-117 OCIP basic HUD, manual Figure 4-4, PDF p21 (printed 4-8).
-- No illustration border, numbered callouts, or leader lines are drawn.
dofile(LockOn_Options.script_path.."HUD/Indicator/OCIP_def.lua")
local U=OCIP_U
local layout=dofile(LockOn_Options.script_path.."HUD/Indicator/layout_profile.lua")
local DEG=math.pi/180*1000
local root=CreateElement "ceSimple"
root.name="OCIP_ROOT"
root.init_pos={layout.origin_mrad[1]*U,layout.origin_mrad[2]*U,0}
root.element_params={"mainpower","HUDBrightness"}
root.controllers={{"parameter_in_range",0,.9,1.1},{"opacity_using_parameter",1}}
Add(root)
local function props(e,parent,level,params,controllers)
    e.name=e.name or create_guid_string()
    e.parent_element=(parent or root).name
    e.collimated=true;e.z_enabled=false
    e.h_clip_relation=h_clip_relations.COMPARE;e.level=level or HUD_DEFAULT_LEVEL
    e.additive_alpha=true;e.blend_mode=blend_mode.IBM_REGULAR_ADDITIVE_ALPHA
    e.element_params=params;e.controllers=controllers
    Add(e);return e
end
local function group(name,x,y,parent,params,controllers)
    local e=CreateElement "ceSimple";e.name=name
    e.init_pos={x*U,y*U,0}
    return props(e,parent,nil,params,controllers)
end
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local function line(points,parent,width,level,name)
    local e=strokes.line(points,U,(width or .65)/.65)
    e.name=name;e.material=OCIP_LINE
    return props(e,parent,level)
end
local function text(value,x,y,size,parent,params,controllers,formats,align,level,name)
    local e=CreateElement "ceStringPoly";e.name=name
    e.value=value;e.init_pos={x*U,y*U,0};e.material=OCIP_FONT
    local font_size=(size or 2.8)*OCIP_FONT_SCALE*OCIP_READABILITY.hud_text_scale
    e.stringdefs={font_size,font_size*.65,font_size*.13,0}
    strokes.text(e)
    e.alignment=align or "CenterCenter";e.formats=formats
    return props(e,parent,level,params,controllers)
end
local function readout(param,x,y,size,format,name)
    return text("",x,y,size,nil,{param},{{"text_using_parameter",0,0}},{format},nil,nil,name)
end
local function box(x,y,w,h,parent,level,name)
    return line({{x-w/2,y-h/2},{x+w/2,y-h/2},{x+w/2,y+h/2},{x-w/2,y+h/2},{x-w/2,y-h/2}},parent,.65,level,name)
end
local function stencil(x,y,w,h,relation,level)
    local e=CreateElement "ceMeshPoly"
    e.name=create_guid_string();e.parent_element=root.name
    e.primitivetype="triangles";e.material=OCIP_LINE
    e.vertices={{(x-w/2)*U,(y-h/2)*U},{(x+w/2)*U,(y-h/2)*U},{(x+w/2)*U,(y+h/2)*U},{(x-w/2)*U,(y+h/2)*U}}
    e.indices={0,1,2,0,2,3};e.collimated=true;e.z_enabled=false
    e.h_clip_relation=relation;e.level=level;e.isvisible=false
    Add(e)
end
-- Readout occlusion zones prevent pitch symbology passing through the boxes.
local zones={{-103,4,35,17},{103,4,42,17},{0,85,104,37},
    {0,-64,48,22},{-76,-91,64,36},{83,-100,58,16}}
for _,z in ipairs(zones) do stencil(z[1],z[2],z[3],z[4],h_clip_relations.INCREASE_IF_LEVEL,2) end

-- Conformal symbols reference the connector optical axis, not the fitted layout
-- centre or the attitude depicted in the manual's example. Cancel the layout
-- translation here; fixed readouts retain their accepted positions.
local datum=group("OCIP_DATUM",-layout.origin_mrad[1],-layout.origin_mrad[2])
local bank=group("OCIP_LADDER_BANK",0,0,datum,{"ROLL_HUD"},{{"rotate_using_parameter",0,1}})
local pitch=group("OCIP_LADDER_PITCH",0,0,bank)
for degrees=-85,85,5 do
    local tag=degrees<0 and "N"..(-degrees) or "P"..degrees
    local bar=group("OCIP_PITCH_"..tag,0,0,pitch,
        {"F117_OCIP_LADDER_"..tag,"F117_OCIP_LADDER_VALID_"..tag},
        {{"move_up_down_using_parameter",0,1000*U},{"parameter_in_range",1,.9,1.1}})
    local y=0
    local bend=math.rad(math.min(math.abs(degrees),45))
    local bend_y=(degrees>0 and -1 or 1)*8*math.sin(bend)
    local inner,outer=22,49
    if degrees==0 then
        line({{-105,y},{-inner,y}},bar)
        line({{inner,y},{105,y}},bar)
    else
        -- All pitch bars have a gap wider than the flight-path symbol.
        for _,side in ipairs({-1,1}) do
            if degrees>0 then
                line({{side*inner,y+bend_y},{side*(inner+8*math.cos(bend)),y},{side*outer,y}},bar)
            else
                line({{side*inner,y+bend_y},{side*(inner+8*math.cos(bend)),y}},bar)
                for x=inner+9,outer-3,7 do line({{side*x,y},{side*math.min(x+4,outer),y}},bar) end
            end
            text(tostring(degrees),side*58,y,2.6,bar)
        end
    end
end
for _,z in ipairs(zones) do stencil(z[1],z[2],z[3],z[4],h_clip_relations.DECREASE_IF_LEVEL,3) end

-- Compact magnetic heading scale, moving under a fixed lubber line.
-- 10-degree major ticks / odd 5-degree minor ticks / labels every 30 degrees.
stencil(0,85,104,37,h_clip_relations.INCREASE_IF_LEVEL,2)
stencil(0,98,35,22,h_clip_relations.INCREASE_IF_LEVEL,3)
local heading=group("OCIP_HEADING_TAPE",0,76,nil,{"F117_OCIP_HEADING"},{{"move_left_right_using_parameter",0,-1.4*U}})
for degrees=-60,420,5 do
    local x=degrees*1.4
    line({{x,0},{x,degrees%10==0 and 6 or 3}},heading,.65,3)
    if degrees%30==0 then
        local h=degrees%360
        text(string.format("%02d",h==0 and 36 or h/10),x,15,2.5,heading,nil,nil,nil,nil,3)
    end
end
stencil(0,98,35,22,h_clip_relations.DECREASE_IF_LEVEL,4)
stencil(0,85,104,37,h_clip_relations.DECREASE_IF_LEVEL,3)
line({{0,72},{0,65}},nil,.8,nil,"OCIP_LUBBER")
box(0,99,31,15)
readout("F117_OCIP_HEADING",0,99,3.1,"%03.0f","OCIP_HEADING")
readout("GS_HUD",-83,104,2.8,"GS %.0f","OCIP_GS")

-- Upper-right vertical speed scale: +1000 to -2000 fpm, 500 fpm intervals.
for i=0,6 do local y=110-i*10;line({{68,y},{i%2==0 and 77 or 73,y}}) end
local vvi=group("OCIP_VVI_POINTER",0,90,nil,{"VVI_SCALE"},{{"move_up_down_using_parameter",0,.020*U}})
line({{77,3},{73,0},{77,-3},{77,3}},vvi)
readout("F117_OCIP_VVI",100,90,2.8,"%+.0f","OCIP_VVI")

-- Boxed calibrated airspeed, Mach above; five-digit barometric altitude.
box(-103,4,33,15)
readout("F117_OCIP_CAS",-103,4,3.2,"%03.0f","OCIP_CAS")
readout("F117_OCIP_MACH",-103,20,2.7,"%.2f","OCIP_MACH")
box(103,4,40,15)
readout("F117_OCIP_ALT",103,4,3.0,"%05.0f","OCIP_ALT")

-- Flight-path symbol: ground velocity transformed into the aircraft optical plane.
for _,z in ipairs(zones) do stencil(z[1],z[2],z[3],z[4],h_clip_relations.INCREASE_IF_LEVEL,2) end
local vv=group("OCIP_VV",0,0,datum,{"F117_OCIP_VV_X","F117_OCIP_VV_Y","F117_OCIP_VV_VALID","F117_OCIP_INS_VALID"},
    {{"move_left_right_using_parameter",0,1000*U},{"move_up_down_using_parameter",1,1000*U},
     {"parameter_in_range",2,.9,1.1},{"parameter_in_range",3,.9,1.1}})
local ring={}
for i=0,32 do local a=i*math.pi/16;table.insert(ring,{4.5*math.cos(a),4.5*math.sin(a)}) end
line(ring,vv)
line({{-16,0},{-4.5,0}},vv)
line({{4.5,0},{16,0}},vv)
line({{0,4.5},{0,11}},vv)
-- Fixed W pitch-reference symbol appears only for an explicit INS/DR invalid flag.
local ref=group("OCIP_PITCH_REFERENCE",0,0,datum,{"F117_OCIP_INS_VALID"},{{"parameter_in_range",0,-.1,.1}})
line({{-16,0},{-8,0},{-4,-5},{0,0},{4,-5},{8,0},{16,0}},ref)
-- Approach bracket: centred at optimum 12 degrees; 1 degree error moves one arm.
local approach=group("OCIP_AOA_BRACKET",-25,0,vv,{"F117_OCIP_APPROACH","F117_OCIP_AOA"},
    {{"parameter_in_range",0,.9,1.1},{"move_up_down_using_parameter",1,-1000*U}})
local aoa_zero=group("OCIP_AOA_OPTIMUM",0,12*DEG,approach)
line({{5,DEG},{0,DEG},{0,-DEG},{5,-DEG}},aoa_zero)
line({{0,0},{4,0}},aoa_zero)

for _,z in ipairs(zones) do stencil(z[1],z[2],z[3],z[4],h_clip_relations.DECREASE_IF_LEVEL,3) end

-- Bank scale fixed below the flight-data region; triangle moves with bank.
local BX,BY,R=0,-35,30
for _,degrees in ipairs({-30,-20,-10,-5,0,5,10,20,30}) do
    local a=math.rad(degrees);local length=degrees%10==0 and 5 or 3
    line({{BX+R*math.sin(a),BY-R*math.cos(a)},{BX+(R+length)*math.sin(a),BY-(R+length)*math.cos(a)}})
end
local bank_pointer=group("OCIP_BANK_POINTER",BX,BY,nil,{"ROLL_HUD"},{{"rotate_using_parameter",0,1}})
line({{-3,-R+9},{3,-R+9},{0,-R+3},{-3,-R+9}},bank_pointer)

-- Fields remain visibly unavailable until an actual navigation/TACAN source
-- supplies valid data. No example destination or guidance is displayed in flight.
text("D   --",-102,-79,2.5,nil,nil,nil,nil,"LeftCenter")
text("TTG --:--",-102,-90,2.5,nil,nil,nil,nil,"LeftCenter")
text("RNG ---.-",-102,-101,2.5,nil,nil,nil,nil,"LeftCenter")
text("DME ---.-",83,-100,2.5)
-- Symbol contracts for future avionics integration (all validity flags default 0).
local function cue(name,valid,az,el)
    return group(name,0,0,datum,{valid,az,el},{{"parameter_in_range",0,.9,1.1},
        {"move_left_right_using_parameter",1,1000*U},{"move_up_down_using_parameter",2,1000*U}})
end
for _,z in ipairs(zones) do stencil(z[1],z[2],z[3],z[4],h_clip_relations.INCREASE_IF_LEVEL,2) end
local dest=cue("OCIP_DESTINATION","F117_OCIP_DEST_VALID","F117_OCIP_DEST_AZ","F117_OCIP_DEST_EL")
box(0,0,12,12,dest)
local offset=cue("OCIP_OFFSET","F117_OCIP_OFFSET_VALID","F117_OCIP_OFFSET_AZ","F117_OCIP_OFFSET_EL")
line({{0,6},{6,0},{0,-6},{-6,0},{0,6}},offset)
local cursor=cue("OCIP_IRADS_CURSOR","F117_OCIP_IRADS_VALID","F117_OCIP_IRADS_AZ","F117_OCIP_IRADS_EL")
line({{-8,0},{8,0}},cursor)
line({{0,-8},{0,8}},cursor)

for _,z in ipairs(zones) do stencil(z[1],z[2],z[3],z[4],h_clip_relations.DECREASE_IF_LEVEL,3) end
