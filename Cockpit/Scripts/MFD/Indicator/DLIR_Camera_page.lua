local finish_native_brightness=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("dlir_picture")
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(FOV)
local readability=dofile(LockOn_Options.script_path.."display_readability.lua")

local params={"F117_IRADS_POWER","mainpower"}
local controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,.9,1.1}}
if F117_COMPOSITE_PAGE then
    params[3]="F117_LCD_READY"
    controllers[3]={"parameter_in_range",2,.9,1.1}
end

-- CockpitBase's generic set_contrast_raw controller enables native contrast
-- and sets the texture shader's Power exponent. It accepts a numeric literal,
-- not a parameter handle. Select one of 66 1%-spaced variants; only one draws.
-- All variants sample the same existing camera target, without an extra bake.
for band=0,65 do
    local picture=CreateElement "ceTexPoly"
    picture.name=band==0 and "dlir_picture" or "dlir_picture_contrast_"..band
    picture.vertices={{-1,1},{1,1},{1,-1},{-1,-1}}
    picture.indices={0,1,2,0,2,3}
    picture.tex_coords={{0,0},{1,0},{1,1},{0,1}}
    picture.material=MakeMaterial("mfd0",readability.irads_video_colour)
    picture.input_space_SRGB=true;picture.additive_alpha=true
    picture.use_mipfilter=false
    local p,c={},{}
    for i,v in ipairs(params) do p[i]=v end
    for i,v in ipairs(controllers) do c[i]=v end
    p[#p+1]="F117_IRADS_CONTRAST_BAND"
    c[#c+1]={"parameter_in_range",#p-1,band-.1,band+.1}
    -- Day preset .80 is neutral (power=1); night .96 gives power=1.2.
    c[#c+1]={"set_contrast_raw",(.35+band*.01)/.80}
    picture.element_params=p
    picture.controllers=c
    Add(picture)
end

-- Keep screen brightness independent of native video contrast and symbology.
local dim=CreateElement "ceMeshPoly"
dim.name="F117_IRADS_DIM_LAYER"
dim.primitivetype="triangles"
dim.vertices={{-1,1},{1,1},{1,-1},{-1,-1}}
dim.indices={0,1,2,0,2,3}
dim.material=MakeMaterial(nil,{0,0,0,255})
dim.collimated=false;dim.additive_alpha=false
dim.blend_mode=blend_mode.IBM_REGULAR
dim.h_clip_relation=h_clip_relations.COMPARE;dim.level=0
local p,c={},{}
for i,v in ipairs(params) do p[i]=v end
for i,v in ipairs(controllers) do c[i]=v end
p[#p+1]="F117_IRADS_DIM_OPACITY"
c[#c+1]={"opacity_using_parameter",#p-1}
dim.element_params=p;dim.controllers=c
Add(dim)

finish_native_brightness()
