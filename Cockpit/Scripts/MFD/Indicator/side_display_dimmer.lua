-- Final regular-alpha black layer dims the whole physical side display,
-- including opaque attitude colours; reducing each shape's alpha would expose
-- underlying layers instead. Existing aperture stencil and depth tests remain.
local e=CreateElement "ceMeshPoly"
e.name=F117_SIDE_DIM_NAME or "F117_"..F117_SIDE_DIM_PARAMETER.."_LAYER"
e.parent_element=F117_SIDE_DIM_ROOT
e.primitivetype="triangles"
e.vertices={{-.052,-.046},{.054,-.046},{.054,.050},{-.052,.050}}
e.indices={0,1,2,0,2,3}
e.material=MakeMaterial(nil,{0,0,0,255})
e.h_clip_relation=h_clip_relations.COMPARE;e.level=1
e.collimated=false;e.z_enabled=true
e.additive_alpha=false;e.blend_mode=blend_mode.IBM_REGULAR
e.element_params={F117_SIDE_DIM_PARAMETER}
e.controllers={{"opacity_using_parameter",0}}
Add(e)
