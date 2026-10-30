-- Presentation-only quad. Sensor logic and glyphs are baked by source indicators.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
local output=dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua")[F117_LCD_KIND]
local outline=dofile(LockOn_Options.script_path.."Calibration/measured_outlines.lua")[F117_LCD_KIND]
local vertices,indices={},{}
for i,p in ipairs(outline.outline) do vertices[i]={p[1],p[2]} end
for i=1,#vertices-2 do indices[#indices+1]=0;indices[#indices+1]=i;indices[#indices+1]=i+1 end
local mask=CreateElement "ceMeshPoly"
mask.name="F117_LCD_MASK_"..F117_LCD_KIND
mask.primitivetype="triangles";mask.vertices=vertices;mask.indices=indices
mask.material=MakeMaterial(nil,{255,255,255,255})
mask.h_clip_relation=h_clip_relations.REWRITE_LEVEL;mask.level=1
mask.isvisible=false;mask.collimated=false;mask.z_enabled=true
mask.element_params={"F117_LCD_READY"};mask.controllers={{"parameter_in_range",0,.9,1.1}}
Add(mask)
local e=CreateElement "ceTexPoly"
e.name="F117_LCD_"..F117_LCD_KIND
e.vertices={{-output.half_width,output.half_height},{output.half_width,output.half_height},
    {output.half_width,-output.half_height},{-output.half_width,-output.half_height}}
e.indices={0,1,2,0,2,3};e.tex_coords={{0,0},{1,0},{1,1},{0,1}}
-- The native baker creates a named texture channel, as in the F-16 LCD path.
e.material=MakeMaterial(output.texture,{255,255,255,255})
e.h_clip_relation=h_clip_relations.COMPARE;e.level=1
e.collimated=false;e.z_enabled=true;e.additive_alpha=false
e.use_mipfilter=false
e.element_params={"mainpower","F117_LCD_READY"}
e.controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,.9,1.1}}
Add(e)
