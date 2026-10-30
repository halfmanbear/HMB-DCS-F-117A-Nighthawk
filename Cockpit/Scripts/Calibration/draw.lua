-- Drawing helpers used only by the independent calibration indicators.
local D = {}
local cyan = {50, 230, 255, 255}
local amber = {255, 190, 35, 255}
D.material = MakeMaterial(nil, cyan)
D.amber = MakeMaterial(nil, amber)
-- Stock Unicode font identifier used by DCS common indicator pages.
D.font = MakeFont({used_DXUnicodeFontData="font_dejavu_lgc_sans_22"}, cyan)

function D.add(e, parent)
    e.name = create_guid_string()
    e.collimated = CALIBRATION_KIND == "hud"
    -- Physical MFDs must be obscured by the stick and other cockpit geometry.
    -- Only the collimated HUD follows the stock HUD's depth-disabled convention.
    e.z_enabled = CALIBRATION_KIND ~= "hud"
    if CALIBRATION_KIND == "hud" and CALIBRATION_GLASS_CLIPPED then
        e.h_clip_relation = h_clip_relations.COMPARE
        e.level = CALIBRATION_GLASS_LEVEL
    else
        e.h_clip_relation = h_clip_relations.NULL
        e.level = 0
    end
    e.use_mipfilter = true
    e.additive_alpha = true
    e.change_opacity = false
    if parent then e.parent_element = parent.name end
    Add(e)
    return e
end

function D.group(pos, parent, params, controllers)
    local e = CreateElement "ceSimple"
    e.init_pos = {pos[1], pos[2], 0}
    e.element_params = params
    e.controllers = controllers
    return D.add(e, parent)
end

function D.line(points, width, parent, material)
    local e = CreateElement "ceMeshPoly"
    e.primitivetype = "triangles"
    e.material = material or D.material
    local vertices, indices = {}, {}
    for i=1,#points-1 do
        local a,b = points[i],points[i+1]
        local dx,dy = b[1]-a[1],b[2]-a[2]
        local length = math.sqrt(dx*dx+dy*dy)
        if length > 0 then
            local nx,ny = -dy/length*width/2, dx/length*width/2
            local n = #vertices
            for _,v in ipairs({{a[1]+nx,a[2]+ny},{a[1]-nx,a[2]-ny},
                               {b[1]+nx,b[2]+ny},{b[1]-nx,b[2]-ny}}) do
                table.insert(vertices,v)
            end
            for _,v in ipairs({n,n+1,n+2,n+1,n+3,n+2}) do table.insert(indices,v) end
        end
    end
    e.vertices = vertices
    e.indices = indices
    return D.add(e,parent)
end

function D.text(value,x,y,size,parent,params,controllers,formats)
    local e = CreateElement "ceStringPoly"
    e.material = D.font
    e.value = value
    e.init_pos = {x,y,0}
    e.alignment = "CenterCenter"
    -- DCS does not apply the geometry scale to font stringdefs. In particular,
    -- 3 mrad must become 0.003 here, otherwise the glyphs fill the entire view.
    -- Follow the stock HUD pages: font dimensions include GetScale explicitly.
    local font_scale = GetScale()
    -- Keep diagnostic labels readable in a full-cockpit capture.
    e.stringdefs = {size*font_scale*2,size*font_scale*2,0,0}
    e.element_params = params
    e.controllers = controllers
    e.formats = formats
    return D.add(e,parent)
end

return D
