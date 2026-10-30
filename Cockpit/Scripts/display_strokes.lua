local S={}
local style=dofile(LockOn_Options.script_path.."display_readability.lua")
function S.line(points,scale,weight)
    local e=CreateElement "ceSMultiLine"
    local vertices,indices={},{}
    for i,p in ipairs(points) do
        vertices[i]={p[1]*scale,p[2]*scale}
        if i>1 then indices[#indices+1]=i-2;indices[#indices+1]=i-1 end
    end
    e.vertices=vertices;e.indices=indices
    e.thickness=style.thickness*(weight or 1);e.fuzziness=style.fuzziness;e.draw_as_wire=false
    return e
end
function S.text(e)
    e.thickness=style.thickness;e.fuzziness=style.fuzziness;e.draw_as_wire=false
    e.use_mipfilter=false
end
return S
