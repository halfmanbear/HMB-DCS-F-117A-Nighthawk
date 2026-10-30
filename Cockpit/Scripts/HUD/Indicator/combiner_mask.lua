-- Finite, cockpit-fixed glass stencil. The HUD symbols remain collimated.
-- Follows the stock F-16 HUD_base.lua combiner convention: physical metres
-- divided by GetScale(), non-collimated mesh, tilted in the third init_rot axis.
return function(level, mount)
    local config = dofile(LockOn_Options.script_path.."HUD/Indicator/combiner_config.lua")
    if not config.enabled then return false end
    local panes = dofile(LockOn_Options.script_path.."HUD/Indicator/combiner_geometry.lua")
    local units_per_metre = 1/GetScale()
    mount = mount or config.mount
    local material = MakeMaterial(nil,{70,100,255,65})
    for i,pane in ipairs(panes) do
        local vertices,indices = {},{}
        local sx = math.max(0,1-2*config.inset_m/pane.width_m)
        local sy = math.max(0,1-2*config.inset_m/pane.height_m)
        for _,v in ipairs(pane.outline_m) do
            table.insert(vertices,{v[1]*sx*units_per_metre,v[2]*sy*units_per_metre})
        end
        for j=1,#vertices-2 do
            for _,v in ipairs({0,j,j+1}) do table.insert(indices,v) end
        end
        local mask = CreateElement "ceMeshPoly"
        mask.name = "F117_COMBINER_MASK_"..create_guid_string()
        mask.primitivetype = "triangles"
        mask.vertices = vertices
        mask.indices = indices
        mask.init_pos = {
            (pane.pos_m[1]-(mount.sz_l or 0)+config.offset_m[1])*units_per_metre,
            (pane.pos_m[2]-(mount.sy_l or 0)+config.offset_m[2])*units_per_metre,
            (pane.pos_m[3]+(mount.sx_l or 0)+config.offset_m[3])*units_per_metre,
        }
        mask.init_rot = {0,0,pane.tilt_deg}
        mask.material = material
        mask.collimated = false
        mask.h_clip_relation = h_clip_relations.REWRITE_LEVEL
        mask.level = level
        mask.isdraw = true
        mask.isvisible = config.show_mask
        mask.change_opacity = false
        mask.z_enabled = true
        Add(mask)
    end
    return true
end
