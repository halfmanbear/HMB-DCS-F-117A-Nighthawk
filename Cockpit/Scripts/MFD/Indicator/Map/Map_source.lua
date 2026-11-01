-- Hornet-inspired separation of native map video and aircraft-specific overlays.
-- No F18 classes/controllers are instantiated by this adapter.
local M={}
function M.configured(config)
    return type(config)=="table" and config.enabled==true and
        type(config.material)=="string" and config.material:match("%S")~=nil and
        config.material~="mfd0" and -- reserved IRADS source; never reuse it
        -- MFD materials get brightness and contrast only on the target's own
        -- indicator; this page does not own one, so it would draw flat grey.
        not config.material:match("^render_target_")
end
function M.add_layer(config,parent,add)
    if not M.configured(config) then return end
    local e=CreateElement "ceTexPoly"
    e.name="F117_MAP_SOURCE_IMAGE";e.material=MakeMaterial(config.material,{255,255,255,255})
    e.vertices={{-.061,.049},{.061,.049},{.061,-.049},{-.061,-.049}}
    e.indices={0,1,2,0,2,3}
    e.tex_coords={{0,0},{1,0},{1,1},{0,1}}
    e.input_space_SRGB=true
    -- Additive alpha, as stock video on the Hornet and F-16 uses. add() applies depth
    -- and the central clip level. The dark backing stays below; all overlays follow.
    add(e,parent,{"F117_MAP_SOURCE_VISIBLE"},{{"parameter_in_range",0,.9,1.1}},true)
    return e
end
return M
