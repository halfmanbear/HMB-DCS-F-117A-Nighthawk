-- Deliberately texture-free source: tests native baking separately from sampling.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
local finish=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_IRADS_SOURCE")
local root=CreateElement "ceSimple"
root.name="F117_IRADS_SOURCE"
root.element_params={"mainpower"};root.controllers={{"parameter_in_range",0,.9,1.1}}
Add(root)
local marker=CreateElement "ceSimple"
marker.name="F117_BAKE_TEST_SOURCE";marker.parent_element=root.name
Add(marker)
local function rectangle(name,x0,y0,x1,y1,colour)
    local e=CreateElement "ceMeshPoly"
    e.name="F117_BAKE_TEST_"..name;e.parent_element=root.name
    e.primitivetype="triangles"
    e.vertices={{x0,y1},{x1,y1},{x1,y0},{x0,y0}}
    e.indices={0,1,2,0,2,3};e.material=MakeMaterial(nil,colour)
    e.collimated=false;e.z_enabled=true;e.additive_alpha=false
    e.h_clip_relation=h_clip_relations.NULL;e.level=0
    Add(e)
end
rectangle("RED",-.080,0,0,.068,{220,35,35,255})
rectangle("GREEN",0,0,.080,.068,{35,220,35,255})
rectangle("BLUE",-.080,-.068,0,0,{35,70,230,255})
rectangle("YELLOW",0,-.068,.080,0,{230,210,35,255})
rectangle("MARK",-.070,.048,-.057,.060,{255,255,255,255})
rectangle("VERTICAL",-.001,-.068,.001,.068,{0,0,0,255})
rectangle("HORIZONTAL",-.080,-.001,.080,.001,{0,0,0,255})
finish()
