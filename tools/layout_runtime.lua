-- Offline DCS indicator API. Real mod drawing helpers are loaded by Python.
_elements = {}
_guid = 0
_parameters = {}
_tracked = ''
function create_guid_string() _guid = _guid + 1; return 'preview_' .. _guid end
local function origin()
    local line = 1
    for depth = 2, 30 do
        local info = debug.getinfo(depth, 'Sl')
        if not info then break end
        if info.source == '@' .. _tracked then line = info.currentline end
    end
    return line
end
function CreateElement(kind)
    return setmetatable({_etype=kind, _source_line=origin()}, {
        __newindex=function(t,k,v)
            if k == 'init_pos' then rawset(t, '_position_line', origin()) end
            rawset(t,k,v)
        end
    })
end
function Add(o) table.insert(_elements, o) end
function MakeMaterial(path, color) return {path=path, color=color} end
function MakeFont(desc, color, ...) return {font=true, color=color, description=desc} end
function SetScale(...) end
-- Approximation for offline physical masks; no head/camera projection here.
function GetScale() return 1 end
function get_param_handle(name)
    return {get=function() return _parameters[name] or 0 end,
            set=function(_,v) _parameters[name]=v end}
end
function Copy(o)
    local c = {}; for k,v in pairs(o) do c[k]=v end; return c
end
function set_circle(o, outer, inner, arc, res)
    outer=outer or .01; inner=inner or 0; arc=arc or 360; res=res or 36
    o.vertices={}; o.indices={}
    for i=0,res do
        local a=math.rad(-arc/2 + arc*i/res)
        table.insert(o.vertices,{outer*math.sin(a),outer*math.cos(a)})
        table.insert(o.vertices,{inner*math.sin(a),inner*math.cos(a)})
        if i<res then
            local n=i*2
            for _,v in ipairs({n,n+1,n+2,n+1,n+3,n+2}) do table.insert(o.indices,v) end
        end
    end
end
FOV=1; MILLYRADIANS=2
h_clip_relations={COMPARE=1,REWRITE_LEVEL=2,INCREASE_IF_LEVEL=3,
    DECREASE_IF_LEVEL=4,INCREASE_LEVEL=5,DECREASE_LEVEL=6}
blend_mode={IBM_REGULAR_ADDITIVE_ALPHA=1,IBM_REGULAR=2}
LockOn_Options={script_path='',common_script_path='__dcs__/'}
