-- Scope a Layout Studio color override to one drawing-helper invocation.
-- Assign before Add: native element properties need not support table reads.
local current_material
function F117_layout_color(draw, material)
    local original_add = Add
    local previous_material = current_material
    current_material = material
    Add = function(element)
        -- Groups have no material; preserve their inheritance and controllers.
        if element.material then element.material = current_material end
        original_add(element)
    end
    local ok, result = pcall(draw)
    Add = original_add
    current_material = previous_material
    if not ok then error(result) end
    return result
end
