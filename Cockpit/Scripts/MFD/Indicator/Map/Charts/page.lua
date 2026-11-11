-- The common T4 terrain renderer produces the chart image. No clipboard,
-- route, text or symbols are drawn into it; F-117 overlays remain independent.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(FOV)
-- The terrain renderer leaves the target's alpha unset, as the stock kneeboard map
-- page implies by writing alpha only. Make the whole chart opaque the same way.
local opaque=CreateElement "ceMeshPoly"
opaque.name="F117_CHART_OPAQUE"
opaque.primitivetype="triangles"
opaque.material=MakeMaterial(nil,{255,255,255,255})
opaque.vertices={{-2,2},{2,2},{2,-2},{-2,-2}}
opaque.indices={0,1,2,0,2,3}
opaque.blend_mode=blend_mode.IBM_ONLY_ALPHA
Add(opaque)
