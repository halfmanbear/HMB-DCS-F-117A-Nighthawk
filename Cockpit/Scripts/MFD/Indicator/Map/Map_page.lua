-- Central Harris digital moving-map OUTLINE, not a reproduced terrain database.
-- This legacy marker preserves the installed native brightness/compositor ABI.
local finish=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_IRADS_SOURCE")
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local ROOT=CreateElement "ceSimple"
ROOT.name="F117_IRADS_SOURCE"
ROOT.element_params={"mainpower"};ROOT.controllers={{"parameter_in_range",0,.9,1.1}}
Add(ROOT)
local display_config=dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua")
if display_config.bake_test and not display_config.enabled and display_config.bake_test_source=="map" then
    -- Dedicated marker permits the same centre-only native diagnostic as the
    -- mesh pattern, without activating either side-display bake.
    local marker=CreateElement "ceSimple"
    marker.name="F117_BAKE_TEST_SOURCE";marker.parent_element=ROOT.name
    Add(marker)
end
-- Sized to the CMDI glass (see Map_window.lua), so the chart fills the whole screen.
local window=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Map_window.lua").for_side(F117_CMDI_SIDE)
local aperture={outline=window.outline}
-- Static labels were laid out for the centre glass; stretch them to this window's edges.
local function X(x)return x>=0 and x*window.xmax/.0880 or x*window.xmin/-.0870 end
local function Y(y)return y>=0 and y*window.ymax/.0747 or y*window.ymin/-.0734 end
local G=MAP_TEXT_GAIN or 1
local function props(e,parent,params,controllers,additive)
    e.name=e.name or create_guid_string();e.parent_element=parent or ROOT.name
    e.collimated=false;e.z_enabled=true;e.h_clip_relation=h_clip_relations.COMPARE;e.level=0
    e.additive_alpha=additive or false
    e.blend_mode=additive and blend_mode.IBM_REGULAR_ADDITIVE_ALPHA or blend_mode.IBM_REGULAR
    e.element_params=params;e.controllers=controllers;Add(e);return e
end
local function line(points,colour,parent)
    local e=strokes.line(points,1,.8);e.material=MAP_MATERIALS[colour or "white"]
    return props(e,parent)
end
-- Static label geometry: stretched to the window like label positions.
local function sline(points,colour,parent)
    local mapped={}
    for i,p in ipairs(points) do mapped[i]={X(p[1]),Y(p[2])} end
    return line(mapped,colour,parent)
end
local function text(value,x,y,sd,align,params,controllers,formats,colour)
    local e=CreateElement "ceStringSLine"
    e.value=value;e.init_pos={X(x),Y(y),0};e.stringdefs=sd or MAP_SD
    e.alignment=align or "LeftCenter";e.formats=formats
    e.material=MAP_FONTS[colour or "white"];strokes.text(e)
    return props(e,nil,params,controllers)
end
local function readout(parameter,x,y,align)
    text("",x,y,MAP_SD,align,{"F117_MAP_"..parameter},{{"text_using_parameter",0,0}},{"%s"})
end
-- Opaque measured aperture covers the retained camera-source surface beneath.
-- The camera target registration itself stays intact for left EO video.
local bg=CreateElement "ceMeshPoly"
bg.name="F117_MAP_BACKGROUND";bg.primitivetype="triangles"
bg.vertices=aperture.outline
local indices={}
for i=1,#aperture.outline-2 do for _,j in ipairs({0,i,i+1}) do indices[#indices+1]=j end end
bg.indices=indices
bg.material=MAP_MATERIALS.background;props(bg)
local source=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Map_source.lua")
local source_config=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/render_source.lua")
source.add_layer(source_config,ROOT.name,props,window)
-- Layout follows the supplied MAP DISPLAY figure; colours remain a design choice.
local function box(x,y,w,h,parent)
    w,h=w*G*.85,h*G*.85 -- boxes hug their text a little tighter than the raw gain
    sline({{x-w/2,y-h/2},{x+w/2,y-h/2},{x+w/2,y+h/2},{x-w/2,y+h/2},{x-w/2,y-h/2}},"white",parent)
end
local function group(name,params,controllers,parent)
    local e=CreateElement "ceSimple";e.name=name
    props(e,parent,params,controllers);return e.name
end
local function label(value,x,y,parent,align)
    local e=CreateElement "ceStringSLine";e.value=value;e.init_pos={X(x),Y(y),0}
    e.stringdefs=MAP_SMALL;e.alignment=align or "CenterCenter"
    e.material=MAP_FONTS.white;strokes.text(e);props(e,parent)
end
-- Format must match the stored type: "%s" with a numeric parameter crashes DCS,
-- and Lua set() stores numeric-looking strings such as "25" as numbers.
local function param_label(parameter,x,y,parent,format,align)
    local e=CreateElement "ceStringSLine";e.init_pos={X(x),Y(y),0};e.stringdefs=MAP_SMALL
    e.alignment=align or "CenterCenter";e.formats={format or "%s"};e.material=MAP_FONTS.white;strokes.text(e)
    props(e,parent,{"F117_MAP_"..parameter},{{"text_using_parameter",0,0}})
end
local normal=group("F117_MAP_NORMAL",{"F117_MAP_FUNCTION"},{{"parameter_in_range",0,-.1,.1}})
label("SNSR",-.034,.065,normal);label("ENTR",-.006,.065,normal);label("UPDT",.023,.065,normal)
local function1=group("F117_MAP_FUNCTION1",{"F117_MAP_FUNCTION"},{{"parameter_in_range",0,.9,1.1}})
param_label("BGD_TEXT",-.057,.065,function1);param_label("REFEL_TEXT",-.025,.065,function1)
param_label("ELEVATION_FT",.016,.065,function1,"%.0f")
sline({{-.003,.063},{0,.067},{.003,.063},{-.003,.063}},"white",function1)
sline({{.035,.067},{.038,.063},{.041,.067},{.035,.067}},"white",function1)
param_label("DATABASE_TEXT",.064,.065);box(.064,.065,.023,.007)
readout("GS_TEXT",-.076,.054);box(-.065,.054,.026,.007)
readout("CRS_TEXT",.076,.054,"RightCenter");box(.062,.054,.030,.007)
param_label("FUNCTION_TEXT",-.069,.043);box(-.069,.043,.018,.007)
sline({{.067,.033},{.070,.038},{.073,.033},{.067,.033}})
param_label("RANGE",.070,.024,nil,"%.0f")
sline({{.067,.015},{.070,.010},{.073,.015},{.067,.015}})
readout("ORIENTATION_TEXT",.077,-.011,"RightCenter")
readout("TDC_TEXT",.077,-.035,"RightCenter")
label("HSD",-.057,-.065);label("MAP",-.027,-.065);box(-.027,-.065,.021,.007)
label("STAT",0,-.065);label("SMD",.030,-.065);label("DFRM",.058,-.065)
-- No ALERT/COR is asserted without an actual alert/corridor data source.
-- PMAP and DMAP select the requested background; neither has map tiles yet.
text("MAP DATA NOT LOADED",0,-.055,MAP_SMALL,"CenterCenter",
    {"F117_MAP_SOURCE_VISIBLE"},{{"parameter_in_range",0,-.1,.1}},nil,"yellow")
local manual=group("F117_MAP_MANUAL",{"F117_MAP_MANUAL"},{{"parameter_in_range",0,.9,2.1}})
label("LOOK",-.071,.023,manual);label("SCRL",-.071,-.011,manual)
local looking=group("F117_MAP_LOOK_SELECTED",{"F117_MAP_LOOK"},{{"parameter_in_range",0,.9,1.1}},manual)
box(-.071,.023,.018,.007,looking)
local scrolling=group("F117_MAP_SCROLL_SELECTED",{"F117_MAP_SCROLL"},{{"parameter_in_range",0,.9,1.1}},manual)
box(-.071,-.011,.018,.007,scrolling)
local cursor=group("F117_MAP_CURSOR",{"F117_MAP_MANUAL"},{{"parameter_in_range",0,.9,2.1}})
line({{-.005,0},{-.0015,0}},"white",cursor);line({{.0015,0},{.005,0}},"white",cursor)
line({{0,-.005},{0,-.0015}},"white",cursor);line({{0,.0015},{0,.005}},"white",cursor)
local function ellipse(rx,ry)
    local points={}
    for i=0,24 do local a=i*2*math.pi/24;points[#points+1]={rx*math.cos(a),ry*math.sin(a)} end
    return points
end
-- Route legs are independently clipped, so crossing legs survive off-screen endpoints.
for i=1,64 do
    local prefix="F117_MAP_LEG_"..i.."_"
    local e=CreateElement "ceSimpleLineObject";e.name=prefix.."LINE"
    e.vertices={{0,0},{0,0}};e.width=.00016;e.material=MAP_MATERIALS.white
    props(e,nil,{prefix.."VISIBLE",prefix.."X",prefix.."Y",prefix.."BX",prefix.."BY"},
        {{"parameter_in_range",0,.9,1.1},{"line_object_set_point_using_parameters",0,1,2,1,1},
        {"line_object_set_point_using_parameters",1,3,4,1,1}})
end
local shapes={ellipse(.0022,.0022),{{0,.0026},{-.0025,-.0021},{.0025,-.0021},{0,.0026}},
    {{0,.0028},{.0022,0},{0,-.0028},{-.0022,0},{0,.0028}},
    {{-.0022,-.0022},{.0022,-.0022},{.0022,.0022},{-.0022,.0022},{-.0022,-.0022}},ellipse(.0032,.0015)}
for i=1,64 do
    local prefix="F117_MAP_WP_"..i.."_"
    local parent=group(prefix.."ROOT",{prefix.."VISIBLE",prefix.."X",prefix.."Y"},
        {{"parameter_in_range",0,.9,1.1},{"move_left_right_using_parameter",1,1},{"move_up_down_using_parameter",2,1}})
    for kind,points in ipairs(shapes) do
        local symbol=group(prefix.."KIND_"..kind,{prefix.."KIND"},{{"parameter_in_range",0,kind-.1,kind+.1}},parent)
        line(points,"white",symbol)
    end
    param_label("WP_"..i.."_LABEL",.0035,-.001,parent,"%s","LeftCenter")
end
for i=1,32 do
    local prefix="F117_MAP_THREAT_"..i.."_"
    local parent=group(prefix.."ROOT",{prefix.."VISIBLE",prefix.."X",prefix.."Y"},
        {{"parameter_in_range",0,.9,1.1},{"move_left_right_using_parameter",1,1},{"move_up_down_using_parameter",2,1}})
    param_label("THREAT_"..i.."_LABEL",0,0,parent)
end
local own=group("F117_MAP_OWNSHIP",{"F117_MAP_VALID","F117_MAP_OWN_X","F117_MAP_OWN_Y","F117_MAP_OWN_ROT"},
    {{"parameter_in_range",0,.9,1.1},{"move_left_right_using_parameter",1,1},{"move_up_down_using_parameter",2,1},{"rotate_using_parameter",3,1}})
-- Aircraft reference symbol: fuselage, main wings and tailplane, as illustrated.
line({{0,-.0035},{0,.005}},"white",own)
line({{-.004,.0015},{.004,.0015}},"white",own)
line({{-.002,-.0025},{.002,-.0025}},"white",own)
local target=group("F117_MAP_IRADS_POINT",{"F117_MAP_TARGET_VISIBLE","F117_MAP_TARGET_X","F117_MAP_TARGET_Y"},
    {{"parameter_in_range",0,.9,1.1},{"move_left_right_using_parameter",1,1},{"move_up_down_using_parameter",2,1}})
-- Separate IRADS cursor: open centre with four arms; it is not a target waypoint.
for _,points in ipairs({{{-.004,0},{-.0016,0}},{{.0016,0},{.004,0}},{{0,-.004},{0,-.0016}},{{0,.0016},{0,.004}}}) do line(points,"white",target) end
local dim=CreateElement "ceMeshPoly"
dim.name="F117_MAP_DIM_LAYER";dim.primitivetype="triangles"
dim.vertices=aperture.outline;dim.indices=indices
dim.material=MakeMaterial(nil,{0,0,0,255})
props(dim,nil,{"F117_MAP_DIM_OPACITY"},{{"opacity_using_parameter",0}})
finish()
