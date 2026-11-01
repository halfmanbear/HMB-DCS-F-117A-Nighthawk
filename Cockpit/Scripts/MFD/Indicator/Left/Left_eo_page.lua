-- Left CMDI EO repeats camera target 0; it never registers a camera source.
-- All elements share the left indicator's native brightness/material registration.
SetScale(METERS)
local root=CreateElement "ceSimple"
root.name="F117_LEFT_EO_ROOT"
root.element_params={"mainpower","F117_LEFT_EO"}
root.controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,.9,1.1}}
Add(root)
local function add(e,relation,additive)
    e.name=e.name or create_guid_string()
    e.parent_element=root.name
    e.collimated=false;e.z_enabled=true
    e.h_clip_relation=relation or h_clip_relations.COMPARE;e.level=1
    e.additive_alpha=additive or false
    e.blend_mode=additive and blend_mode.IBM_REGULAR_ADDITIVE_ALPHA or blend_mode.IBM_REGULAR
    Add(e)
end
-- Match the VSD rounded aperture and reset its stencil when EO is selected.
local aperture={}
for _,c in ipairs({{.044,.041,0},{-.044,.041,90},{-.044,-.037,180},{.044,-.037,270}}) do
    for i=0,8 do local a=math.rad(c[3]+i*90/8);aperture[#aperture+1]={c[1]+.006*math.cos(a),c[2]+.006*math.sin(a)} end
end
local mask=CreateElement "ceMeshPoly"
mask.primitivetype="triangles";mask.vertices=aperture
local indices={}
for i=1,#aperture-2 do for _,j in ipairs({0,i,i+1}) do indices[#indices+1]=j end end
mask.indices=indices
mask.material=MakeMaterial(nil,{0,0,0,255})
add(mask,h_clip_relations.REWRITE_LEVEL)
-- Sample target 0's texture directly. "render_target_1" is an MFD-shader material
-- whose brightness and contrast reach only the indicator that owns the target;
-- anywhere else both are zero, which flattens the picture to mid grey.
local VIDEO=MakeMaterial("mfd0",{255,255,255,255})
-- Keep the same 66 native contrast bands as the centre video. Only one draws.
for band=0,65 do
    local e=CreateElement "ceTexPoly"
    e.name="F117_LEFT_EO_VIDEO_"..band
    e.vertices={{-.052,.050},{.054,.050},{.054,-.046},{-.052,-.046}}
    e.indices={0,1,2,0,2,3};e.tex_coords={{0,0},{1,0},{1,1},{0,1}}
    e.material=VIDEO;e.use_mipfilter=false
    e.input_space_SRGB=true
    e.element_params={"F117_IRADS_POWER","F117_IRADS_CONTRAST_BAND"}
    e.controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,band-.1,band+.1},
        {"set_contrast_raw",(.35+band*.01)/.80}}
    add(e,nil,true)
end
-- Reuse the centre targeting symbols and telemetry, fitted to the smaller glass.
-- ONE avoids applying centre brightness: native left brightness or its final
-- black fallback layer dims the complete EO picture and symbols together.
F117_IRADS_OVERLAY_OPTIONS={repeater=true,root_name="F117_LEFT_EO_SYMBOLOGY",
    parent=root.name,scale=.62,level=1,brightness_parameter="ONE"}
dofile(LockOn_Options.script_path.."MFD/Indicator/MFD_base_page.lua")
F117_IRADS_OVERLAY_OPTIONS=nil
F117_SIDE_DIM_PARAMETER="F117_LEFT_EO_DIM_OPACITY"
F117_SIDE_DIM_ROOT=root.name
F117_SIDE_DIM_NAME="F117_LEFT_EO_DIM_LAYER"
dofile(LockOn_Options.script_path.."MFD/Indicator/side_display_dimmer.lua")
F117_SIDE_DIM_NAME=nil
