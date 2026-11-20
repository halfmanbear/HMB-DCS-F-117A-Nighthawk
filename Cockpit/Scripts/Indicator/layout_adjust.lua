-- Layout Studio overrides run before native Add(), in preview and DCS alike.
local M={}
local function scaled(values,factor,count)
    local result={}
    for i,v in ipairs(values) do result[i]=(i<=count and type(v)=="number") and v*factor or v end
    return result
end
function M.begin_page(factor)
    local original=Add
    Add=function(e)
        -- Native DCS elements expose unset properties as strings (rather than
        -- nil as in the offline preview). Only transform typed geometry.
        if type(e.init_pos)=="table" then e.init_pos=scaled(e.init_pos,factor,2) end
        if type(e.vertices)=="table" then
            local vertices={}
            for i,v in ipairs(e.vertices) do vertices[i]=scaled(v,factor,2) end
            e.vertices=vertices
        end
        if type(e.stringdefs)=="table" then e.stringdefs=scaled(e.stringdefs,factor,3) end
        if type(e.width)=="number" then e.width=e.width*factor end
        if type(e.controllers)=="table" then
            local controllers={}
            for i,c in ipairs(e.controllers) do
                local n=scaled(c,1,0)
                if c[1]=="move_left_right_using_parameter" or c[1]=="move_up_down_using_parameter" then
                    n[3]=(c[3] or 1)*factor
                end
                controllers[i]=n
            end
            e.controllers=controllers
        end
        original(e)
    end
    return function() Add=original end
end
function M.begin_weight(factor)
    local original=Add
    Add=function(e)
        if type(e.thickness)=="number" then e.thickness=e.thickness*factor
        elseif type(e.width)=="number" then e.width=e.width*factor end
        original(e)
    end
    return function() Add=original end
end
function M.weight(draw,factor)
    local restore=M.begin_weight(factor)
    local ok,result=pcall(draw)
    restore()
    if not ok then error(result) end
    return result
end
return M
